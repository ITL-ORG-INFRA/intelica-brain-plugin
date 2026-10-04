#!/usr/bin/env python3
"""Junta los fragmentos de captura de una sesion en un solo material de
trabajo, listo para que el skill escriba los .md finales.

Hace solo la parte determinista, que es la que un LLM haria caro e
inconsistente: deduplicar entidades por ID acumulando propiedades, deduplicar
relaciones, y agrupar los hechos por cuenta. Una sesion larga puede dejar 8
fragmentos con 40 entidades cada uno -- deduplicar 320 a mano leyendolas todas
no tiene sentido.

Lo que NO hace, porque necesita criterio: resolver contradicciones entre
fragmentos (uno afirma algo que otro despues descarto) y escribir la
narrativa. Eso queda para el skill, y por eso los hechos se devuelven con su
numero de fragmento -- el orden importa para saber que vino despues.

Uso:
    python3 consolidate.py --session <session_id>
    python3 consolidate.py --session <session_id> --keep   # no borra nada nunca,
                                                           # es el default

Imprime en stdout un JSON con: accounts, facts (con secuencia), entities
deduplicadas, relations deduplicadas, y open_questions.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

STAGING_ROOT = Path(
    os.environ.get("INTELICA_ARCA_STAGING", "~/.intelica-arca/sessions")
).expanduser()

SAFE_SESSION = re.compile(r"[^A-Za-z0-9._-]")


def session_dir(session_id: str) -> Path:
    safe = SAFE_SESSION.sub("_", session_id.strip()) or "unknown-session"
    return STAGING_ROOT / safe


def merge_entities(fragments: list[dict]) -> list[dict]:
    """Deduplica por `id`. El primer fragmento que declara una entidad suele
    tener mas contexto que una referencia posterior, asi que las propiedades
    ya presentes no se pisan -- solo se completan las que faltan.

    Acumula en `seen_in` de que fragmentos vino, que le sirve al skill para
    saber si algo aparecio una vez al pasar o fue tema recurrente.
    """
    merged: dict[str, dict] = {}
    for fragment in fragments:
        seq = fragment.get("sequence")
        for entity in fragment.get("entities") or []:
            if not isinstance(entity, dict):
                continue
            eid = entity.get("id")
            if not eid:
                continue
            existing = merged.get(eid)
            if existing is None:
                merged[eid] = {**entity, "seen_in": [seq]}
                continue
            for key, value in entity.items():
                if value not in (None, "", [], {}):
                    existing.setdefault(key, value)
            if seq not in existing["seen_in"]:
                existing["seen_in"].append(seq)
    return list(merged.values())


def merge_relations(fragments: list[dict]) -> list[dict]:
    """Deduplica por la terna (from, type, to). Una relacion repetida entre
    fragmentos es la misma relacion, no dos."""
    seen: set[tuple[str, str, str]] = set()
    out: list[dict] = []
    for fragment in fragments:
        for rel in fragment.get("relations") or []:
            if not isinstance(rel, dict):
                continue
            key = (rel.get("from"), rel.get("type"), rel.get("to"))
            if not all(key) or key in seen:
                continue
            seen.add(key)
            out.append({"from": key[0], "type": key[1], "to": key[2]})
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--session", required=True, help="session_id de la conversacion")
    parser.add_argument("--keep", action="store_true", default=True,
                        help="conservar los fragmentos (default, y no hay opcion de borrar)")
    args = parser.parse_args()

    directory = session_dir(args.session)
    paths = sorted(directory.glob("[0-9][0-9][0-9].json"))

    if not paths:
        # No es un error: una conversacion corta nunca se compacto, asi que no
        # hay fragmentos. El skill tiene que extraer de la conversacion viva.
        json.dump({
            "session_id": args.session,
            "fragment_count": 0,
            "note": "Sin fragmentos de captura — esta conversacion no se compacto. "
                    "Extraer directamente de la conversacion actual.",
            "accounts": [], "facts": [], "entities": [], "relations": [],
            "open_questions": [], "reports": [],
        }, sys.stdout, ensure_ascii=False, indent=2)
        return 0

    fragments: list[dict] = []
    for path in paths:
        try:
            fragments.append(json.loads(path.read_text(encoding="utf-8")))
        except json.JSONDecodeError:
            print(f"  aviso: {path.name} no es JSON valido, se omite", file=sys.stderr)

    facts: list[dict] = []
    open_questions: list[dict] = []
    summaries: list[dict] = []
    accounts: list[str] = []
    # Por ruta: el mismo HTML se puede capturar en dos compactaciones si se
    # siguio editando. Gana la ultima descripcion, como con los hechos.
    reports: dict[str, dict] = {}

    for fragment in fragments:
        seq = fragment.get("sequence")
        if fragment.get("summary"):
            summaries.append({"sequence": seq, "summary": fragment["summary"]})
        for fact in fragment.get("facts") or []:
            facts.append({"sequence": seq, "fact": fact})
        for question in fragment.get("open_questions") or []:
            open_questions.append({"sequence": seq, "question": question})
        for report in fragment.get("reports") or []:
            if isinstance(report, dict) and report.get("path"):
                reports[report["path"]] = {**report, "sequence": seq}
        for account in fragment.get("accounts") or []:
            if account not in accounts:
                accounts.append(account)

    entities = merge_entities(fragments)
    relations = merge_relations(fragments)

    # Las cuentas tambien salen de las entidades Account, por si un fragmento
    # no las declaro explicitamente en `accounts`.
    for entity in entities:
        if entity.get("type") == "Account" and entity.get("id") not in accounts:
            accounts.append(entity["id"])

    json.dump({
        "session_id": args.session,
        "fragment_count": len(fragments),
        "accounts": accounts,
        "summaries": summaries,
        "facts": facts,
        "entities": entities,
        "relations": relations,
        "open_questions": open_questions,
        "reports": list(reports.values()),
        "note": "Los hechos vienen con su numero de fragmento: si dos se "
                "contradicen, el de secuencia mayor es el posterior en la "
                "conversacion. Resolverlo es criterio del skill, no del script.",
    }, sys.stdout, ensure_ascii=False, indent=2)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
