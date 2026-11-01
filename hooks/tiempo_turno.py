#!/usr/bin/env python3
"""Hooks UserPromptSubmit y Stop: cuanto tardo el turno, al pie de la respuesta.

    02:00 min

El modelo no tiene reloj: no puede decir cuanto tardo. El cliente si. Al
recibir el mensaje se anota la hora, y al terminar el turno se muestra la
diferencia como mensaje del sistema, debajo del pie de tokens y USD que
piden las instrucciones del conector.

Es el turno entero: desde que llega el mensaje hasta que Claude termina,
con las consultas, lo que piensa entre ellas y la respuesta escrita. Solo
existe en Claude Code (terminal, app de escritorio, IDE); claude.ai no corre
hooks.

Recibe por stdin el JSON del hook, con session_id y hook_event_name. Nunca
frena el turno: si algo falla, no muestra nada. INTELICA_ARCA_TIEMPO=off lo
apaga.
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
from pathlib import Path

DIRECTORIO = Path(os.environ.get("INTELICA_ARCA_HOME", Path.home() / ".intelica-arca")) / "turnos"

# Una sesion abandonada deja su marca. Se borran al pasar este tiempo, en
# el proximo mensaje de cualquier sesion.
VIDA_MARCA_S = 7 * 24 * 3600

_SESION_VALIDA = re.compile(r"^[A-Za-z0-9_-]{1,128}$")


def formato(segundos: float) -> str:
    s = max(0, round(segundos))
    if s >= 3600:
        return f"{s // 3600}:{s % 3600 // 60:02d}:{s % 60:02d} h"
    return f"{s // 60:02d}:{s % 60:02d} min"


def _marca(sesion: str) -> Path | None:
    # El id viene del cliente, pero arma una ruta: nada de '/' ni '..'.
    return DIRECTORIO / sesion if _SESION_VALIDA.match(sesion or "") else None


def _limpiar(ahora: float) -> None:
    for vieja in DIRECTORIO.glob("*"):
        try:
            if ahora - vieja.stat().st_mtime > VIDA_MARCA_S:
                vieja.unlink()
        except OSError:
            pass


def al_recibir(sesion: str, ahora: float) -> None:
    marca = _marca(sesion)
    if marca is None:
        return
    DIRECTORIO.mkdir(parents=True, exist_ok=True)
    _limpiar(ahora)
    marca.write_text(repr(ahora))


def al_terminar(sesion: str, ahora: float) -> str | None:
    """El mensaje para el usuario, o None si no hay con que medir.

    La marca no se borra: si otro hook de Stop hace seguir el turno, el
    Stop siguiente tiene que medir desde el mismo mensaje."""
    marca = _marca(sesion)
    if marca is None or not marca.exists():
        return None
    return formato(ahora - float(marca.read_text()))


def main() -> int:
    if os.environ.get("INTELICA_ARCA_TIEMPO", "").strip().lower() in ("off", "0", "false", "no"):
        return 0
    try:
        datos = json.load(sys.stdin)
        sesion = datos.get("session_id", "")
        evento = datos.get("hook_event_name", "")
        ahora = time.time()
        if evento == "UserPromptSubmit":
            al_recibir(sesion, ahora)
        elif evento == "Stop":
            mensaje = al_terminar(sesion, ahora)
            if mensaje:
                print(json.dumps({"systemMessage": mensaje}))
    except Exception:  # noqa: BLE001 -- un reloj roto no puede trabar la sesion
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
