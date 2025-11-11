#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
UV_CACHE_DIR="${ROOT_DIR}/.uv-cache"

DEFAULT_FLIGHTS=12
DEFAULT_BASE_PAX=200
DEFAULT_TICKER_SLEEP=30

SEED=1
FLIGHT_COUNT="${DEFAULT_FLIGHTS}"
BASE_PAX="${DEFAULT_BASE_PAX}"
START_TICKER=0
TICKER_SLEEP="${DEFAULT_TICKER_SLEEP}"

usage() {
  cat <<EOF
Usage: $(basename "$0") [options]

Options:
  --skip-seed           Skip running scripts/generate_mock_data.py before starting services
  --flights N           Number of flight manifests to seed (default: ${DEFAULT_FLIGHTS})
  --base-passengers N   Average passengers per flight (default: ${DEFAULT_BASE_PAX})
  --ticker              Start scripts/flight_ticker.py alongside the servers
  --ticker-sleep N      Seconds between ticker updates (default: ${DEFAULT_TICKER_SLEEP})
  -h, --help            Show this help message
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --skip-seed)
      SEED=0
      shift
      ;;
    --flights)
      FLIGHT_COUNT="$2"
      shift 2
      ;;
    --base-passengers)
      BASE_PAX="$2"
      shift 2
      ;;
    --ticker)
      START_TICKER=1
      shift
      ;;
    --ticker-sleep)
      TICKER_SLEEP="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage
      exit 1
      ;;
  esac
done

kill_port() {
  local port="$1"
  if ! command -v lsof >/dev/null 2>&1; then
    echo "lsof not available; skipping port cleanup for ${port}"
    return
  fi

  local pids
  pids=$(lsof -ti :"${port}" 2>/dev/null || true)
  if [[ -n "${pids}" ]]; then
    echo "Killing processes on port ${port}: ${pids}"
    # shellcheck disable=SC2086
    kill -9 ${pids} >/dev/null 2>&1 || true
  fi
}

mkdir -p "${UV_CACHE_DIR}"

kill_port 8000
kill_port 3000

BACK_PID=""
FRONT_PID=""
TICKER_PID=""

cleanup() {
  if [[ -n "${TICKER_PID}" ]] && kill -0 "${TICKER_PID}" >/dev/null 2>&1; then
    kill "${TICKER_PID}" >/dev/null 2>&1 || true
  fi
  if [[ -n "${FRONT_PID}" ]] && kill -0 "${FRONT_PID}" >/dev/null 2>&1; then
    kill "${FRONT_PID}" >/dev/null 2>&1 || true
  fi
  if [[ -n "${BACK_PID}" ]] && kill -0 "${BACK_PID}" >/dev/null 2>&1; then
    kill "${BACK_PID}" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT

if [[ "${SEED}" -eq 1 ]]; then
  echo "Seeding Mongo with ${FLIGHT_COUNT} flights (${BASE_PAX} pax avg)..."
  UV_CACHE_DIR="${UV_CACHE_DIR}" uv run --project "${ROOT_DIR}/backend" python "${ROOT_DIR}/scripts/generate_mock_data.py" \
    --flights "${FLIGHT_COUNT}" \
    --base-passengers "${BASE_PAX}" \
    --no-kafka
fi

if [[ "${START_TICKER}" -eq 1 ]]; then
  echo "Starting flight ticker (interval ${TICKER_SLEEP}s)..."
  UV_CACHE_DIR="${UV_CACHE_DIR}" uv run --project "${ROOT_DIR}/backend" python "${ROOT_DIR}/scripts/flight_ticker.py" \
    --sleep "${TICKER_SLEEP}" &
  TICKER_PID=$!
fi

echo "Starting FastAPI backend on http://127.0.0.1:8000"
(
  cd "${ROOT_DIR}/backend"
  UV_CACHE_DIR="${UV_CACHE_DIR}" uv run uvicorn app.main:app --host 127.0.0.1 --port 8000
) &
BACK_PID=$!

echo "Starting Vite dev server on http://127.0.0.1:3000"
(
  cd "${ROOT_DIR}/frontend/dashboard"
  npm run dev
) &
FRONT_PID=$!

# Fallback for macOS bash without wait -n
while true; do
  if ! kill -0 "${BACK_PID}" >/dev/null 2>&1; then
    wait "${BACK_PID}" || true
    break
  fi
  if ! kill -0 "${FRONT_PID}" >/dev/null 2>&1; then
    wait "${FRONT_PID}" || true
    break
  fi
  sleep 1
done

echo "One of the services exited; stopping the rest..."
