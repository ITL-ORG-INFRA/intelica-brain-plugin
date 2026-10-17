#!/usr/bin/env python3
"""Guarda en el staging el tramo del transcript que la compactacion va a
resumir, como texto legible, para que /intelica-arca lo extraiga al cerrar.

Reemplaza al hook que frenaba la compactacion con exit 2 para pedirle a
Claude que capturara: ese aviso le llega al usuario, no al modelo, asi que
la captura nunca corria y la compactacion pasaba al segundo intento. Copiar
el tramo no necesita criterio, asi que lo hace este script y la compactacion
sigue sin esperar a nadie. El criterio (que vale documentar) queda para el
cierre, cuando hay tiempo y contexto libre para aplicarlo.

Dos entradas:

    tramos.py guardar          # el hook PreCompact: JSON del hook por stdin
    tramos.py al-dia --session <id> [--transcript <path>]

`al-dia` recupera las compactaciones que no tienen tramo -- las de antes de
este cambio, o una en la que el hook fallo -- cortando el transcript en cada
`compact_boundary`. consolidate.py lo llama antes de leer los fragmentos.

Del transcript solo se leen `type` y `message.content`, que tienen la forma
de la API de mensajes. El resto del formato es interno de Claude Code y
cambia entre versiones: lo que no se reconoce se ignora, no rompe.

Cada tramo queda como `tramo-NNN.md` y su numero es la secuencia que tendra
el fragmento que se extraiga de el (`NNN.json`), para que el orden de los
hechos siga el de la conversacion aunque se extraigan en paralelo.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

STAGING_ROOT = Path(
    os.environ.get("INTELICA_ARCA_STAGING", "~/.intelica-arca/sessions")
).expanduser()
CLAUDE_DIR = Path(os.environ.get("CLAUDE_CONFIG_DIR", "~/.claude")).expanduser()

SAFE_SESSION = re.compile(r"[^A-Za-z0-9._-]")

# Un tramo lo lee entero un subagente. Unos 60k tokens le dejan lugar para
# razonar y escribir el fragmento; un tramo mas largo se parte en varios.
MAX_CHARS_TRAMO = 220_000
# La salida completa de una tool casi nunca hace falta: los identificadores
# que importan aparecen al principio o los repite la respuesta del modelo.
MAX_CHARS_RESULTADO = 1_500
MAX_CHARS_INPUT = 600

MANIFIESTO = "tramos.json"
SYSTEM_REMINDER = re.compile(r"<system-reminder>.*?</system-reminder>", re.S)


def session_dir(session_id: str) -> Path:
    safe = SAFE_SESSION.sub("_", session_id.strip()) or "unknown-session"
    return STAGING_ROOT / safe


def buscar_transcript(session_id: str) -> Path | None:
    safe = SAFE_SESSION.sub("_", session_id.strip())
    candidatos = sorted((CLAUDE_DIR / "projects").glob(f"*/{safe}.jsonl"))
    return candidatos[0] if candidatos else None


def leer_manifiesto(directory: Path) -> list[dict]:
    path = directory / MANIFIESTO
    if not path.exists():
        return []
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []


def siguiente_numero(directory: Path, manifiesto: list[dict]) -> int:
    usados = [t["numero"] for t in manifiesto]
    usados += [int(p.stem) for p in directory.glob("[0-9][0-9][0-9].json")]
    return max(usados, default=0) + 1


def recortar(texto: str, limite: int) -> str:
    if len(texto) <= limite:
        return texto
    return f"{texto[:limite]}\n[... {len(texto) - limite} caracteres recortados]"


def texto_de_resultado(contenido) -> str:
    if isinstance(contenido, str):
        return contenido
    partes = []
    for bloque in contenido or []:
        if isinstance(bloque, dict) and bloque.get("type") == "text":
            partes.append(bloque.get("text", ""))
    return "\n".join(partes)


def entradas(linea: str) -> list[str]:
    """Lo legible de una linea del transcript, o nada si no es conversacion."""
    try:
        d = json.loads(linea)
    except json.JSONDecodeError:
        return []
    if not isinstance(d, dict) or d.get("type") not in ("user", "assistant"):
        return []
    # El resumen de la compactacion repite el tramo anterior, que ya se
    # guardo; las lineas de un subagente las resume su propia respuesta.
    if d.get("isCompactSummary") or d.get("isSidechain"):
        return []
    mensaje = d.get("message")
    if not isinstance(mensaje, dict):
        return []
    contenido = mensaje.get("content")
    if isinstance(contenido, str):
        contenido = [{"type": "text", "text": contenido}]
    if not isinstance(contenido, list):
        return []

    rol = "usuario" if d["type"] == "user" else "claude"
    out = []
    for bloque in contenido:
        if not isinstance(bloque, dict):
            continue
        tipo = bloque.get("type")
        if tipo == "text":
            texto = SYSTEM_REMINDER.sub("", bloque.get("text", "")).strip()
            # La carga de un skill trae el SKILL.md entero: es el plugin, no
            # la conversacion.
            if texto and not texto.startswith("Base directory for this skill"):
                out.append(f"[{rol}] {texto}")
        elif tipo == "tool_use":
            entrada = json.dumps(bloque.get("input"), ensure_ascii=False)
            out.append(f"[tool {bloque.get('name')}] {recortar(entrada, MAX_CHARS_INPUT)}")
        elif tipo == "tool_result":
            texto = SYSTEM_REMINDER.sub("", texto_de_resultado(bloque.get("content"))).strip()
            if texto:
                error = " (error)" if bloque.get("is_error") else ""
                out.append(f"[resultado{error}] {recortar(texto, MAX_CHARS_RESULTADO)}")
    return out


def timestamp(linea: str) -> str | None:
    try:
        return json.loads(linea).get("timestamp")
    except (json.JSONDecodeError, AttributeError):
        return None


def guardar_rango(session_id: str, transcript: Path, lineas: list[str],
                  desde: int, hasta: int) -> list[dict]:
    """Escribe las lineas [desde, hasta) como uno o mas tramos. Devuelve los
    tramos escritos; ninguno si el rango no tiene conversacion."""
    bloques: list[tuple[int, str]] = []
    for i in range(desde, hasta):
        for entrada in entradas(lineas[i]):
            bloques.append((i, entrada))
    if not bloques:
        return []

    directory = session_dir(session_id)
    directory.mkdir(parents=True, exist_ok=True)
    manifiesto = leer_manifiesto(directory)

    # Partir en tramos que entren en un subagente, sin cortar una entrada.
    grupos: list[list[tuple[int, str]]] = [[]]
    largo = 0
    for bloque in bloques:
        if grupos[-1] and largo + len(bloque[1]) > MAX_CHARS_TRAMO:
            grupos.append([])
            largo = 0
        grupos[-1].append(bloque)
        largo += len(bloque[1]) + 2

    escritos = []
    for n, grupo in enumerate(grupos):
        numero = siguiente_numero(directory, manifiesto)
        primera = grupo[0][0]
        # El ultimo grupo cubre hasta el final del rango, para que el
        # siguiente tramo arranque donde termina este.
        ultima = hasta if n == len(grupos) - 1 else grupos[n + 1][0][0]
        cuerpo = "\n\n".join(texto for _, texto in grupo)
        encabezado = (
            f"# Tramo {numero} — sesion {session_id}\n\n"
            f"Transcript: {transcript}, lineas {primera}–{ultima}\n"
            f"Desde {timestamp(lineas[primera]) or '?'} "
            f"hasta {timestamp(lineas[grupo[-1][0]]) or '?'}\n\n---\n\n"
        )
        archivo = directory / f"tramo-{numero:03d}.md"
        fd = os.open(archivo, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(encabezado + cuerpo + "\n")

        tramo = {
            "numero": numero,
            "archivo": archivo.name,
            "transcript": str(transcript),
            "desde_linea": primera if n else desde,
            "hasta_linea": ultima,
            "caracteres": len(cuerpo),
            "guardado": datetime.now(timezone.utc).isoformat(),
        }
        manifiesto.append(tramo)
        escritos.append(tramo)

    (directory / MANIFIESTO).write_text(
        json.dumps(manifiesto, ensure_ascii=False, indent=2), encoding="utf-8")
    return escritos


def cubierto_hasta(session_id: str, transcript: Path) -> int:
    manifiesto = leer_manifiesto(session_dir(session_id))
    return max((t["hasta_linea"] for t in manifiesto
                if t.get("transcript") == str(transcript)), default=0)


def guardar(session_id: str, transcript: Path) -> list[dict]:
    """El hook: todo lo que no tiene tramo, hasta el final del transcript."""
    lineas = transcript.read_text(encoding="utf-8").splitlines()
    escritos = poner_al_dia(session_id, transcript, lineas)
    desde = cubierto_hasta(session_id, transcript)
    return escritos + guardar_rango(session_id, transcript, lineas, desde, len(lineas))


def poner_al_dia(session_id: str, transcript: Path,
                 lineas: list[str] | None = None) -> list[dict]:
    """Un tramo por cada compactacion que quedo sin el suyo."""
    if lineas is None:
        lineas = transcript.read_text(encoding="utf-8").splitlines()
    escritos = []
    desde = cubierto_hasta(session_id, transcript)
    for i in range(desde, len(lineas)):
        if '"compact_boundary"' not in lineas[i]:
            continue
        try:
            d = json.loads(lineas[i])
        except json.JSONDecodeError:
            continue
        if d.get("type") == "system" and d.get("subtype") == "compact_boundary":
            escritos += guardar_rango(session_id, transcript, lineas, desde, i)
            # Aunque el rango no tuviera conversacion (el hook ya lo habia
            # guardado y solo quedaron lineas internas), el siguiente arranca
            # despues de esta compactacion.
            desde = max(desde, cubierto_hasta(session_id, transcript), i)
    return escritos


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="accion", required=True)
    sub.add_parser("guardar", help="hook PreCompact: lee el JSON del hook por stdin")
    al_dia = sub.add_parser("al-dia", help="tramos para compactaciones sin el suyo")
    al_dia.add_argument("--session", required=True)
    al_dia.add_argument("--transcript")
    args = parser.parse_args()

    if args.accion == "guardar":
        try:
            entrada = json.load(sys.stdin)
        except json.JSONDecodeError:
            entrada = {}
        session_id = entrada.get("session_id") or ""
        if not session_id:
            print("intelica-arca: el hook no trajo session_id; no se guarda el tramo.",
                  file=sys.stderr)
            return 0
        transcript = Path(entrada["transcript_path"]) if entrada.get("transcript_path") \
            else buscar_transcript(session_id)
        if not transcript or not transcript.exists():
            print(f"intelica-arca: no se encontro el transcript de {session_id}.",
                  file=sys.stderr)
            return 0
        escritos = guardar(session_id, transcript)
        if escritos:
            print(f"intelica-arca: {len(escritos)} tramo(s) guardado(s) para /intelica-arca.")
        return 0

    transcript = Path(args.transcript) if args.transcript else buscar_transcript(args.session)
    if not transcript or not transcript.exists():
        print(json.dumps({"tramos_nuevos": [], "transcript": None}))
        return 0
    escritos = poner_al_dia(args.session, transcript)
    print(json.dumps({"tramos_nuevos": escritos, "transcript": str(transcript)},
                     ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
