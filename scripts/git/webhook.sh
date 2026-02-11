#!/bin/bash

URL="${1:-http://localhost/git/webhook}"

SECRET="0qmSbIL9KaZ0VJZXxG6LBC1aTPDVtvYZQivVkcYLKzcZ5uOP9LeFdFruSZHUJQOK"

PAYLOAD_FILE="payload.json"

if [ ! -f "$PAYLOAD_FILE" ]; then
	echo "Error: Payload file '$PAYLOAD_FILE' not found."
	exit 1
fi

SIGNATURE=$(openssl dgst -sha256 -hmac "$SECRET" "$PAYLOAD_FILE" | awk '{print $NF}')

echo "---------------------------------------------------"
echo "Target URL: $URL"
echo "Secret:     $SECRET"
echo "Signature:  sha256=$SIGNATURE"
echo "Payload:    $PAYLOAD_FILE"
echo "---------------------------------------------------"

curl -v \
  -X POST \
  -H "Content-Type: application/json" \
  -H "X-Hub-Signature-256: sha256=$SIGNATURE" \
  -H "X-GitHub-Event: push" \
  --data-binary "@$PAYLOAD_FILE" \
  "$URL"

echo ""