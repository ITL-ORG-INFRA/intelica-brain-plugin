#!/usr/bin/env bash
# Hook PreCompact: guarda en el staging el tramo de la conversacion que la
# compactacion va a resumir, para que /intelica-arca lo extraiga al cerrar.
#
# Antes frenaba la compactacion con exit 2 y le pedia a Claude que capturara.
# Ese mensaje le llega al usuario, no al modelo: la captura nunca corria y la
# compactacion pasaba al segundo intento, porque la marca de "ya frene una vez"
# la dejaba seguir. Ahora el hook copia el tramo el mismo -- eso no necesita
# criterio -- y nunca frena: perder un tramo es molesto, trabar la sesion es
# peor.
#
# Recibe por stdin un JSON con session_id, transcript_path, trigger, entre
# otros. Instalacion: ver README.md del plugin.

set -uo pipefail

python3 "${CLAUDE_PLUGIN_ROOT}/skills/intelica-arca/scripts/tramos.py" guardar \
  || echo "intelica-arca: no se pudo guardar el tramo; /intelica-arca lo recupera del transcript." >&2

exit 0
