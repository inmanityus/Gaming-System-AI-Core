#!/usr/bin/env sh

# wait-for.sh: wait for TCP host:port to become available

set -e

HOST="$1"
PORT="$2"
shift 2

while ! nc -z "$HOST" "$PORT" >/dev/null 2>&1; do
  echo "Waiting for $HOST:$PORT..."
  sleep 2
done

exec "$@"


