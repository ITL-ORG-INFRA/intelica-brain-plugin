#!/usr/bin/env python3
"""Verifica los limites que exige el marketplace de la organizacion en claude.ai.

    python3 scripts/check-limites.py

Existe porque el marketplace de la org no rechaza el plugin: lo sincroniza
igual y descarta en silencio lo que no cumple. El 2026-10-24 la primera
sincronizacion dejo afuera intelica-arca-capture y intelica-arca-recall, y
el unico aviso fue un panel de advertencias. Claude Code instalado desde el
repo no aplica estos limites, asi que en local todo parece andar.

Limites (los que mostro esa sincronizacion):
  - description del plugin: 500 caracteres, en plugin.json y marketplace.json
  - description de cada skill: 1024 caracteres
  - description de una skill: sin tags tipo XML (<algo>)
"""
from __future__ import annotations

import glob
import json
import os
import re
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAX_PLUGIN = 500
MAX_SKILL = 1024
TAG = re.compile(r"<[^>\n]+>")


def descripcion_de_skill(path: str) -> str:
    texto = open(path, encoding="utf-8").read()
    if not texto.startswith("---"):
        return ""
    frontmatter = texto.split("---", 2)[1]
    m = re.search(r'^description:\s*(.*?)(?=^[A-Za-z][\w-]*:|\Z)', frontmatter, re.M | re.S)
    if not m:
        return ""
    valor = m.group(1).strip()
    if len(valor) >= 2 and valor[0] == valor[-1] and valor[0] in "\"'":
        valor = valor[1:-1]
    return valor


def main() -> int:
    errores = []

    plugin = json.load(open(os.path.join(RAIZ, ".claude-plugin/plugin.json"), encoding="utf-8"))
    market = json.load(open(os.path.join(RAIZ, ".claude-plugin/marketplace.json"), encoding="utf-8"))
    for origen, desc in (("plugin.json", plugin.get("description", "")),
                         ("marketplace.json", market["plugins"][0].get("description", ""))):
        if len(desc) > MAX_PLUGIN:
            errores.append(f"{origen}: description del plugin con {len(desc)} caracteres (max {MAX_PLUGIN})")

    for path in sorted(glob.glob(os.path.join(RAIZ, "skills/*/SKILL.md"))):
        nombre = os.path.relpath(path, RAIZ)
        desc = descripcion_de_skill(path)
        if not desc:
            errores.append(f"{nombre}: sin description")
            continue
        if len(desc) > MAX_SKILL:
            errores.append(f"{nombre}: description con {len(desc)} caracteres (max {MAX_SKILL})")
        tag = TAG.search(desc)
        if tag:
            errores.append(f"{nombre}: description con un tag tipo XML ({tag.group(0)})")

    if errores:
        print("FUERA DE LOS LIMITES DEL MARKETPLACE DE LA ORG", file=sys.stderr)
        for e in errores:
            print(f"  {e}", file=sys.stderr)
        print("\nLa org sincroniza igual y descarta esto sin avisar mas que en un panel.",
              file=sys.stderr)
        return 1
    print("Descripciones dentro de los limites del marketplace de la org")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
