#!/usr/bin/env python3
"""Pruebas de tramos.py con un transcript inventado. Sin pytest:

    python3 skills/intelica-arca/scripts/test_tramos.py
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

AQUI = Path(__file__).resolve().parent
WRITE_CAPTURE = AQUI.parent.parent / "intelica-arca-capture" / "scripts" / "write_capture.py"
SESION = "sesion-de-prueba"


def linea(tipo: str, **extra) -> str:
    return json.dumps({"type": tipo, "timestamp": "2026-10-17T12:00:00Z", **extra})


def usuario(texto: str, **extra) -> str:
    return linea("user", message={"role": "user", "content": texto}, **extra)


def claude(*bloques: dict) -> str:
    return linea("assistant", message={"role": "assistant", "content": list(bloques)})


def frontera() -> str:
    return linea("system", subtype="compact_boundary", content="Conversation compacted")


def correr(script: Path, *args: str, entrada: str = "", staging: Path) -> subprocess.CompletedProcess:
    env = {**os.environ, "INTELICA_ARCA_STAGING": str(staging)}
    return subprocess.run([sys.executable, str(script), *args], input=entrada,
                          capture_output=True, text=True, env=env, check=False)


def hook(transcript: Path, staging: Path) -> subprocess.CompletedProcess:
    entrada = json.dumps({"session_id": SESION, "transcript_path": str(transcript),
                          "trigger": "auto"})
    return correr(AQUI / "tramos.py", "guardar", entrada=entrada, staging=staging)


def consolidar(transcript: Path, staging: Path) -> dict:
    r = correr(AQUI / "consolidate.py", "--session", SESION, "--transcript", str(transcript),
               staging=staging)
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout)


PRIMER_TRAMO = [
    linea("queue-operation"),
    usuario("¿qué SG usa la RDS de portal-prod?"),
    claude({"type": "thinking", "thinking": ""},
           {"type": "tool_use", "name": "aws_api", "input": {"op": "DescribeDBInstances"}}),
    linea("user", message={"role": "user", "content": [
        {"type": "tool_result", "content": "sg-04aac9e78d6520b80 " + "x" * 5000}]}),
    claude({"type": "text", "text": "Usa sg-04aac9e78d6520b80."}),
    usuario("<system-reminder>ruido</system-reminder>"),
    linea("user", message={"role": "user", "content": [
        {"type": "text", "text": "Base directory for this skill: /x\n# SKILL entero"}]}),
]
SEGUNDO_TRAMO = [
    usuario("Resumen de lo anterior", isCompactSummary=True),
    usuario("¿y el puerto?"),
    claude({"type": "text", "text": "1433, abierto solo a los nodos."}),
]


def test_hook_guarda_y_no_frena(tmp: Path) -> None:
    staging, transcript = tmp / "s1", tmp / "t1.jsonl"
    transcript.write_text("\n".join(PRIMER_TRAMO) + "\n")

    r = hook(transcript, staging)
    assert r.returncode == 0, "el hook nunca frena la compactacion"
    texto = (staging / SESION / "tramo-001.md").read_text()
    assert "[usuario] ¿qué SG usa la RDS de portal-prod?" in texto
    assert "[tool aws_api]" in texto and "sg-04aac9e78d6520b80" in texto
    assert "caracteres recortados" in texto, "la salida larga de una tool se recorta"
    assert "ruido" not in texto and "SKILL entero" not in texto

    # Claude Code compacta y la conversacion sigue en el mismo archivo.
    with transcript.open("a") as fh:
        fh.write("\n".join([frontera(), *SEGUNDO_TRAMO]) + "\n")
    assert hook(transcript, staging).returncode == 0
    segundo = (staging / SESION / "tramo-002.md").read_text()
    assert "1433" in segundo and "Resumen de lo anterior" not in segundo
    assert "¿qué SG" not in segundo, "un tramo no repite el anterior"

    # Al cerrar no hay nada que recuperar: el hook ya guardo los dos.
    assert [t["tramo"] for t in consolidar(transcript, staging)["tramos_pendientes"]] == [1, 2]
    assert not (staging / SESION / "tramo-003.md").exists()


def test_recupera_compactaciones_sin_hook(tmp: Path) -> None:
    staging, transcript = tmp / "s2", tmp / "t2.jsonl"
    transcript.write_text("\n".join(
        [*PRIMER_TRAMO, frontera(), *SEGUNDO_TRAMO, frontera(), usuario("en vivo")]) + "\n")

    pendientes = consolidar(transcript, staging)["tramos_pendientes"]
    assert [t["tramo"] for t in pendientes] == [1, 2]
    textos = [Path(t["path"]).read_text() for t in pendientes]
    assert "sg-04aac9e78d6520b80" in textos[0] and "1433" in textos[1]
    assert not any("en vivo" in t for t in textos), "lo posterior a la ultima compactacion esta en contexto"

    # Correrlo de nuevo no duplica.
    consolidar(transcript, staging)
    assert not (staging / SESION / "tramo-003.md").exists()

    # Extraidos los dos (en desorden, como en paralelo), consolida en orden.
    for n, hecho in ((2, "puerto 1433"), (1, "la RDS usa sg-04aac9e78d6520b80")):
        r = correr(WRITE_CAPTURE, "--session", SESION, "--tramo", str(n),
                   entrada=json.dumps({"summary": "s", "facts": [hecho]}), staging=staging)
        assert r.returncode == 0, r.stderr
    r = correr(WRITE_CAPTURE, "--session", SESION, "--tramo", "1",
               entrada=json.dumps({"summary": "otra vez"}), staging=staging)
    assert r.returncode != 0, "un tramo ya extraido no se pisa"

    resultado = consolidar(transcript, staging)
    assert "tramos_pendientes" not in resultado
    assert resultado["fragment_count"] == 2
    assert [f["sequence"] for f in resultado["facts"]] == [1, 2]

    # Una captura sin tramo no toma el numero de uno.
    r = correr(WRITE_CAPTURE, "--session", SESION, entrada='{"summary": "x"}', staging=staging)
    assert "003.json" in r.stdout, r.stdout


def test_tramo_largo_se_parte(tmp: Path) -> None:
    staging, transcript = tmp / "s3", tmp / "t3.jsonl"
    largas = [claude({"type": "text", "text": f"{i} " + "y" * 50_000}) for i in range(10)]
    transcript.write_text("\n".join(largas) + "\n")
    hook(transcript, staging)
    tramos = json.loads((staging / SESION / "tramos.json").read_text())
    assert len(tramos) == 3, [t["caracteres"] for t in tramos]
    assert tramos[0]["desde_linea"] == 0 and tramos[-1]["hasta_linea"] == 10
    assert all(a["hasta_linea"] == b["desde_linea"] for a, b in zip(tramos, tramos[1:]))


def test_sin_session_id_no_frena(tmp: Path) -> None:
    r = correr(AQUI / "tramos.py", "guardar", entrada="{}", staging=tmp / "s4")
    assert r.returncode == 0


def main() -> int:
    pruebas = [v for k, v in globals().items() if k.startswith("test_")]
    for prueba in pruebas:
        with tempfile.TemporaryDirectory() as tmp:
            prueba(Path(tmp))
        print(f"ok  {prueba.__name__}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
