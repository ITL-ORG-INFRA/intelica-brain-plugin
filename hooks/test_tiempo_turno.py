#!/usr/bin/env python3
"""Pruebas de tiempo_turno.py, corriendolo como lo corre Claude Code. Sin pytest:

    python3 hooks/test_tiempo_turno.py

Lo que se fija:
  - Stop muestra el tiempo desde el mensaje, como systemMessage;
  - UserPromptSubmit no imprime nada: lo que imprime le llega al modelo;
  - sin marca (el plugin se instalo a mitad del turno) no muestra nada;
  - un session_id con '/' o '..' no arma una ruta;
  - INTELICA_ARCA_TIEMPO=off lo apaga, y un JSON roto no frena el turno.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))

import tiempo_turno  # noqa: E402

_fallas: list[str] = []


def check(cond, etiqueta):
    if not cond:
        _fallas.append(etiqueta)


def correr(evento: str, sesion: str, home: str, **env) -> subprocess.CompletedProcess:
    entrada = json.dumps({"session_id": sesion, "hook_event_name": evento,
                          "transcript_path": "/x.jsonl", "prompt": "hola"})
    return subprocess.run([sys.executable, str(AQUI / "tiempo_turno.py")], input=entrada,
                          capture_output=True, text=True,
                          env={**os.environ, "INTELICA_ARCA_HOME": home, **env})


# --- formato ------------------------------------------------------------------

check(tiempo_turno.formato(120) == "02:00 min", f"dos minutos: {tiempo_turno.formato(120)}")
check(tiempo_turno.formato(7.4) == "00:07 min", f"segundos: {tiempo_turno.formato(7.4)}")
check(tiempo_turno.formato(3725) == "1:02:05 h", f"mas de una hora: {tiempo_turno.formato(3725)}")
check(tiempo_turno.formato(-3) == "00:00 min", "un reloj que retrocede no da negativo")

# --- el turno ---------------------------------------------------------------------

with tempfile.TemporaryDirectory() as home:
    r = correr("UserPromptSubmit", "abc-123", home)
    check(r.returncode == 0 and r.stdout == "",
          f"al recibir no imprime nada, porque le llegaria al modelo: {r.stdout!r}")
    marca = Path(home) / "turnos" / "abc-123"
    check(marca.exists(), "deja la marca de la sesion")

    marca.write_text(repr(time.time() - 125))
    r = correr("Stop", "abc-123", home)
    salida = json.loads(r.stdout or "{}")
    check(r.returncode == 0 and salida.get("systemMessage") in ("02:05 min", "02:06 min"),
          f"al terminar muestra el tiempo del turno: {r.stdout!r}")
    check(marca.exists(), "la marca queda: si otro hook hace seguir el turno, se mide desde el mismo mensaje")

    r = correr("Stop", "otra-sesion", home)
    check(r.stdout == "", f"sin marca no muestra nada: {r.stdout!r}")

    r = correr("UserPromptSubmit", "../../fuera", home)
    check(not (Path(home).parent / "fuera").exists() and r.returncode == 0,
          "un session_id con '..' no escribe fuera del directorio")

    r = correr("Stop", "abc-123", home, INTELICA_ARCA_TIEMPO="off")
    check(r.stdout == "", f"INTELICA_ARCA_TIEMPO=off lo apaga: {r.stdout!r}")

    r = subprocess.run([sys.executable, str(AQUI / "tiempo_turno.py")], input="no es json",
                       capture_output=True, text=True, env={**os.environ, "INTELICA_ARCA_HOME": home})
    check(r.returncode == 0 and r.stdout == "", "un JSON roto no frena el turno")

    vieja = Path(home) / "turnos" / "sesion-abandonada"
    vieja.write_text("0")
    hace_ocho_dias = time.time() - 8 * 24 * 3600
    os.utime(vieja, (hace_ocho_dias, hace_ocho_dias))
    correr("UserPromptSubmit", "abc-123", home)
    check(not vieja.exists(), "las marcas de mas de una semana se borran")

if _fallas:
    print(f"\n{len(_fallas)} falla(s):\n")
    for f in _fallas:
        print("  -", f)
    sys.exit(1)
print("Tiempo por turno OK: se mide del mensaje al final del turno y nunca frena.")
