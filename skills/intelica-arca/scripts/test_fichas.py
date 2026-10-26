#!/usr/bin/env python3
"""Tests de las fichas del catalogo en build_push_args.py.

    python3 skills/intelica-arca/scripts/test_fichas.py

Corre el script como lo corre la skill (JSON por stdin) y mira lo que sale.

Lo que se fija:
  - una lista de temas sigue funcionando igual que antes;
  - una ficha va a database/catalogo/<perfil>/<BASE>/<OBJETO>.md, la de una
    base a _base.md, la de un servidor a _servidor.md, y una plantilla
    (MSTRAFB*) a la carpeta sin el asterisco;
  - el frontmatter lleva entities y relations en bloque (el parser del grafo
    no lee mapas en linea);
  - `temas` suma a `fuentes` la ruta del documento de la conversacion;
  - se rechaza lo que dejaria una ficha rota: sin su DatabaseObject, con el
    object_type que no corresponde, un objeto sin esquema, dos fichas para la
    misma ruta, un tema que no existe.
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


TEMA = {
    "title": "Como corre el sync de fees", "domain": "database",
    "summary": "Una conversacion.", "tags": ["sync"], "body": "## Resumen\n\nTexto.",
}


def ficha(**cambios):
    base = {
        "perfil": "denver", "base": "ASSOCINV", "objeto": "dbo.FEE_FRAC_N", "tipo": "tabla",
        "title": "FEE_FRAC_N", "summary": "Fees fraccionados por banco y corrida.",
        "body": "## Para que sirve\n\nTexto.", "entornos": ["denver-dev"],
        "filas_aprox": 378182565, "medido_en": "2026-10-25", "acotar_por": "RPT_BNK_ID",
        "tags": ["fees", "fraccionamiento"], "fuentes": ["inbox/database/x.md"],
        "entities": [{"type": "DatabaseObject", "id": "ASSOCINV.dbo.FEE_FRAC_N",
                      "object_type": "table", "filter_key": "RPT_BNK_ID"}],
        "relations": [{"from": "ASSOCINV.dbo.FEE_FRAC_N", "type": "IN_DATABASE", "to": "ASSOCINV"}],
    }
    base.update(cambios)
    return base


# --- La forma de siempre ---------------------------------------------------

codigo, salida, err = correr([TEMA])
check(codigo == 0 and [f["path"].split("/")[1] for f in salida["files"]] == ["database"],
      f"una lista de temas sigue funcionando: {err}")
check(salida and salida["files"][0]["path"].startswith("inbox/database/"),
      "y va a inbox/<dominio>/")

# --- Una ficha con su tema ---------------------------------------------------

codigo, salida, err = correr({"temas": [TEMA],
                              "fichas": [ficha(temas=["Como corre el sync de fees"])]})
check(codigo == 0, f"tema y ficha juntos: {err}")
archivos = {f["path"]: f["content"] for f in (salida or {}).get("files", [])}
ruta = "database/catalogo/denver/ASSOCINV/FEE_FRAC_N.md"
check(ruta in archivos, f"la ficha va a {ruta}: {list(archivos)}")
contenido = archivos.get(ruta, "")
md_tema = next((p for p in archivos if p.startswith("inbox/database/") and p.endswith(".md")), "")
check(f"  - {md_tema}" in contenido and "  - inbox/database/x.md" in contenido,
      f"`fuentes` suma el documento de la conversacion: {contenido[:600]}")
check("entities:\n  - type: DatabaseObject\n    id: ASSOCINV.dbo.FEE_FRAC_N" in contenido,
      f"entities en bloque: {contenido}")
check("relations:\n  - from: ASSOCINV.dbo.FEE_FRAC_N\n    type: IN_DATABASE\n    to: ASSOCINV"
      in contenido, "relations en bloque")
check("{" not in contenido.split("---")[1], "ningun mapa en linea en el frontmatter")
for linea in ("tipo: tabla", "perfil: denver", "base: ASSOCINV", "objeto: dbo.FEE_FRAC_N",
              "acotar_por: RPT_BNK_ID", "filas_aprox: 378182565", "entornos: [denver-dev]"):
    check(f"\n{linea}\n" in contenido, f"el frontmatter tiene `{linea}`")
check(contenido.rstrip().endswith("Texto."), "el cuerpo va despues del frontmatter")
check(salida and salida["new_branch_name"].startswith("docs/brain-"), "la rama de siempre")

# --- Rutas de base, servidor y plantilla ----------------------------------------

codigo, salida, err = correr({"fichas": [
    ficha(tipo="base", objeto=None, entities=[{"type": "Database", "id": "ASSOCINV"}], relations=[]),
    ficha(tipo="servidor", base=None, objeto=None, entities=[], relations=[]),
    ficha(base="MSTRAFB*", objeto="dbo.SYNC_FRAC_CONFIG",
          entities=[{"type": "DatabaseObject", "id": "MSTRAFB*.dbo.SYNC_FRAC_CONFIG",
                     "object_type": "table"}],
          relations=[]),
]})
rutas = [f["path"] for f in (salida or {}).get("files", [])]
check(codigo == 0 and rutas == ["database/catalogo/denver/ASSOCINV/_base.md",
                                "database/catalogo/denver/_servidor.md",
                                "database/catalogo/denver/MSTRAFB/SYNC_FRAC_CONFIG.md"],
      f"rutas de base, servidor y plantilla: {rutas} {err}")
check(salida and "catalogo-3" in salida["new_branch_name"], "sin temas, la rama dice catalogo")

# --- Lo que se rechaza ------------------------------------------------------------

for desc, entrada, motivo in (
    ("sin su DatabaseObject", {"fichas": [ficha(entities=[])]}, "falta la entidad `DatabaseObject`"),
    ("object_type que no corresponde", {"fichas": [ficha(tipo="vista")]}, "no coinciden"),
    ("object_type inventado", {"fichas": [ficha(entities=[
        {"type": "DatabaseObject", "id": "ASSOCINV.dbo.FEE_FRAC_N", "object_type": "tabla"}])]},
     "`object_type: tabla`"),
    ("objeto sin esquema", {"fichas": [ficha(objeto="FEE_FRAC_N")]}, "esquema.nombre"),
    ("perfil en mayusculas", {"fichas": [ficha(perfil="Denver")]}, "minusculas"),
    ("dos fichas para la misma ruta", {"fichas": [ficha(), ficha()]}, "van juntas"),
    ("un tema que no existe", {"fichas": [ficha(temas=["otro"])]}, "no es un tema de este push"),
    ("una relacion inventada", {"fichas": [ficha(relations=[
        {"from": "ASSOCINV.dbo.FEE_FRAC_N", "type": "LOADS", "to": "ASSOCINV"}])]}, "`LOADS`"),
):
    codigo, salida, err = correr(entrada)
    check(codigo == 1 and salida is None and motivo in err,
          f"{desc}: tendria que rechazarse con '{motivo}' ({codigo}): {err[-300:]}")

# --- consolidate.py junta lo descriptivo por objeto -------------------------------

sys.path.insert(0, os.path.dirname(SCRIPT))
import consolidate  # noqa: E402

juntos = consolidate.merge_catalogo([
    {"sequence": 1, "catalogo": [{"objeto": "ASSOCINV.dbo.FEE_FRAC_N", "perfil": "denver",
                                  "tipo": "tabla", "hechos": ["se acota por RPT_BNK_ID"]}]},
    {"sequence": 2, "catalogo": [{"objeto": "associnv.dbo.fee_frac_n", "perfil": "denver",
                                  "hechos": ["DISCARDED: se acota por RPT_BNK_ID — tambien por fecha"]},
                                 {"objeto": "MSTRAFB*.dbo.SYNC_FRAC_CONFIG", "perfil": "denver",
                                  "tipo": "tabla", "hechos": ["tabla de trabajo del sync"]}]},
])
fee = next((o for o in juntos if o["objeto"] == "ASSOCINV.dbo.FEE_FRAC_N"), {})
check(len(juntos) == 2 and [h["sequence"] for h in fee.get("hechos", [])] == [1, 2],
      f"un objeto escrito con otras mayusculas es el mismo, y sus hechos guardan el orden: {juntos}")
check(fee.get("tipo") == "tabla", "el tipo no se pierde si un tramo no lo repite")

if _failures:
    print(f"\n{len(_failures)} fallo(s):\n")
    for f in _failures:
        print("  -", f)
    sys.exit(1)
print("Fichas OK: rutas, frontmatter en bloque, fuentes de la conversacion y los rechazos.")
