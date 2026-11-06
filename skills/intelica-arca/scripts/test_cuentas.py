#!/usr/bin/env python3
"""Tests de `account` y de las entidades Account en build_push_args.py.

    python3 skills/intelica-arca/scripts/test_cuentas.py

Corre el script como lo corre la skill (JSON por stdin) y mira lo que sale.
Fija lo que el `validar` de intelica-brain-ia exige y el script no exigia:

  - todo documento lleva `account`: un tema de database o windows sin cuenta
    sale con `account: N/A`, y va a la carpeta plana del dominio;
  - en `aws`, sin cuenta sigue siendo un error, y una cuenta que no es
    canonica tambien;
  - una Account con el numero de cuenta como id y el nombre canonico en
    `name` se corrige: el id pasa al nombre, el numero a `account_id`, y las
    relaciones que apuntaban al numero apuntan al nombre;
  - una Account con un id que no se puede deducir se rechaza.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys

SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "build_push_args.py")
_failures: list[str] = []


def check(cond, label):
    if not cond:
        _failures.append(label)


def correr(entrada) -> tuple[int, dict | None, str]:
    proc = subprocess.run([sys.executable, SCRIPT], input=json.dumps(entrada),
                          capture_output=True, text=True)
    salida = json.loads(proc.stdout) if proc.returncode == 0 else None
    return proc.returncode, salida, proc.stderr


def tema(**cambios):
    base = {"title": "Bucket de reportes", "domain": "aws", "account": "Interchange-Prod",
            "summary": "Una conversacion.", "tags": ["s3"], "body": "## Resumen\n\nTexto."}
    base.update(cambios)
    return base


def archivos(salida) -> dict[str, str]:
    return {f["path"]: f["content"] for f in (salida or {}).get("files", [])}


# --- account en el frontmatter ------------------------------------------------

codigo, salida, err = correr([tema(domain="database", account=None)])
md = next(iter(archivos(salida).items()), ("", ""))
check(codigo == 0, f"un tema de database sin cuenta se acepta: {err}")
check("\naccount: N/A\n" in md[1], f"y sale con account: N/A:\n{md[1]}")
check(md[0].startswith("inbox/database/") and md[0].count("/") == 2,
      f"en la carpeta plana del dominio: {md[0]}")

codigo, _, err = correr([tema(account=None)])
check(codigo != 0 and "falta `account`" in err, f"en aws, sin cuenta es error: {err}")

codigo, _, err = correr([tema(account="Interchange-Prd")])
check(codigo != 0 and "no es una cuenta canonica" in err,
      f"una cuenta mal escrita es error: {err}")

codigo, salida, err = correr([tema(account="N/A")])
check(codigo == 0 and "\naccount: N/A\n" in next(iter(archivos(salida).values()), ""),
      f"N/A sigue valiendo para un tema que cruza cuentas: {err}")

# --- Entidades Account --------------------------------------------------------

codigo, salida, err = correr([tema(
    entities=[{"type": "Account", "id": "818835242461", "name": "Interchange-Prod"},
              {"type": "Resource", "id": "itl-0004-itx-prd-intchg-02-s3-reports",
               "resource_type": "s3_bucket"}],
    relations=[{"from": "itl-0004-itx-prd-intchg-02-s3-reports", "type": "BELONGS_TO",
                "to": "818835242461"}],
)])
grafo = next((c for p, c in archivos(salida).items() if p.endswith(".graph.yaml")), "")
check(codigo == 0, f"numero de cuenta con nombre canonico se corrige: {err}")
check("  - type: Account\n    id: Interchange-Prod\n    account_id: \"818835242461\"\n" in grafo,
      f"el id pasa al nombre y el numero a account_id, entre comillas:\n{grafo}")
check("    to: Interchange-Prod\n" in grafo and "to: \"818835242461\"" not in grafo,
      f"la relacion apunta al nombre:\n{grafo}")
check("name:" not in grafo, f"name no queda repetido:\n{grafo}")
check("pasa a `Interchange-Prod`" in err, f"y se avisa: {err}")

codigo, _, err = correr([tema(entities=[{"type": "Account", "id": "818835242461"}])])
check(codigo != 0 and "va en `account_id`" in err,
      f"un numero sin nombre se rechaza y dice donde va: {err}")

codigo, _, err = correr([tema(entities=[{"type": "Account", "id": "Interchange-Prd"}])])
check(codigo != 0 and "no tiene el id canonico" in err, f"un id mal escrito se rechaza: {err}")

codigo, _, err = correr([tema(entities=[{"type": "Account", "id": "Interchange-Prod",
                                         "account_id": "818835242461"}])])
check(codigo == 0, f"la forma correcta pasa sin tocar: {err}")

if _failures:
    print(f"\n{len(_failures)} fallo(s):\n")
    for f in _failures:
        print("  -", f)
    sys.exit(1)
print("Cuentas OK: account en todo documento, ids canonicos y la correccion del numero.")
