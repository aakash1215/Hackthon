#!/usr/bin/env bash
# Generate certs/cert.pem + certs/key.pem for localhost and every current LAN IPv4,
# plus 192.168.137.1 (the laptop's fixed IP when it hosts a Windows Mobile Hotspot).
# Re-run whenever the IP changes, then restart the app. Usage: bash scripts/make_certs.sh [extra-ip ...]
set -eu
cd "$(dirname "$0")/.."
MKCERT="${MKCERT:-models/tools/mkcert.exe}"
mkdir -p certs
IPS=$(ipconfig | grep -i "IPv4" | sed 's/.*: *//' | tr -d '\r' | sort -u)
"$MKCERT" -cert-file certs/cert.pem -key-file certs/key.pem \
  localhost 127.0.0.1 ::1 192.168.137.1 $IPS "$@"
CAROOT=$("$MKCERT" -CAROOT | tr -d '\r')
cp "$CAROOT/rootCA.pem" certs/rootCA.crt   # this file goes on the phones (CA certificate)
echo "Cert covers: localhost 127.0.0.1 192.168.137.1 $IPS $*"
echo "Phone CA file: certs/rootCA.crt"
