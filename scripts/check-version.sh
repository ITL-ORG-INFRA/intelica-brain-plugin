#!/usr/bin/env bash
# Verifica que la version este igual en los dos archivos que la declaran.
#
#   ./scripts/check-version.sh
#
# Existe porque la version vive en dos lugares y solo uno se nota: el cliente
# lee marketplace.json para decidir si ofrece actualizar, mientras que
# plugin.json es el que uno recuerda tocar. Si se desincronizan, el cambio
# existe en main y nadie lo recibe -- el boton "Actualizar" queda gris y no
# hay ningun error que lo explique. Ya paso tres veces.

set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

PLUGIN=$(python3 -c 'import json; print(json.load(open(".claude-plugin/plugin.json"))["version"])')
MARKET=$(python3 -c 'import json; print(json.load(open(".claude-plugin/marketplace.json"))["plugins"][0]["version"])')

if [[ "${PLUGIN}" != "${MARKET}" ]]; then
  echo "VERSIONES DESINCRONIZADAS" >&2
  echo "  .claude-plugin/plugin.json:      ${PLUGIN}" >&2
  echo "  .claude-plugin/marketplace.json: ${MARKET}" >&2
  echo "" >&2
  echo "El cliente mira marketplace.json: mientras diga ${MARKET}, nadie" >&2
  echo "recibe la ${PLUGIN} y el boton Actualizar queda gris." >&2
  exit 1
fi

echo "Version sincronizada: ${PLUGIN}"
