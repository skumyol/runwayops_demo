#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="${ROOT_DIR}/backend"
FRONTEND_DIR="${ROOT_DIR}/frontend/dashboard"
UV_CACHE_DIR="${ROOT_DIR}/.uv-cache"

PYTHON_REQUIRED_MAJOR=3
PYTHON_REQUIRED_MINOR=12
NODE_REQUIRED_MAJOR=18

command_exists() {
  command -v "$1" >/dev/null 2>&1
}

ensure_python_version() {
  if ! command_exists python3; then
    echo "❌ python3 is required (>=${PYTHON_REQUIRED_MAJOR}.${PYTHON_REQUIRED_MINOR})." >&2
    exit 1
  fi

  local version major minor
  version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:3])))')
  IFS=. read -r major minor _ <<<"${version}"

  if (( major < PYTHON_REQUIRED_MAJOR )) || { (( major == PYTHON_REQUIRED_MAJOR )) && (( minor < PYTHON_REQUIRED_MINOR )); }; then
    echo "❌ Python ${PYTHON_REQUIRED_MAJOR}.${PYTHON_REQUIRED_MINOR}+ required (found ${version})." >&2
    exit 1
  fi

  echo "✅ Python ${version} detected."
}

ensure_node_version() {
  if ! command_exists node; then
    echo "❌ Node.js is required (>=${NODE_REQUIRED_MAJOR}). Install from https://nodejs.org" >&2
    exit 1
  fi

  local version major
  version=$(node -v | sed 's/^v//')
  IFS=. read -r major _ _ <<<"${version}"

  if (( major < NODE_REQUIRED_MAJOR )); then
    echo "❌ Node.js ${NODE_REQUIRED_MAJOR}+ required (found v${version})." >&2
    exit 1
  fi

  if ! command_exists npm; then
    echo "❌ npm is required but was not found. Ensure Node.js installs npm." >&2
    exit 1
  fi

  echo "✅ Node.js v${version} detected."
}

ensure_uv_installed() {
  if command_exists uv; then
    echo "✅ uv $(uv --version 2>/dev/null | head -n1) detected."
    return
  fi

  echo "⚠️  uv not found; installing with 'python3 -m pip --user uv'..."

  if ! python3 -m pip --version >/dev/null 2>&1; then
    python3 -m ensurepip --upgrade >/dev/null
  fi

  python3 -m pip install --user uv

  local user_bin="${HOME}/.local/bin"
  if [[ -d "${user_bin}" && ":${PATH}:" != *":${user_bin}:"* ]]; then
    export PATH="${user_bin}:${PATH}"
    echo "ℹ️  Added ${user_bin} to PATH for this session. Add it to your shell profile for future sessions."
  fi

  if ! command_exists uv; then
    cat >&2 <<'EOF'
❌ Failed to install uv automatically.
Please install it manually: https://docs.astral.sh/uv/getting-started/
EOF
    exit 1
  fi

  echo "✅ uv installed."
}

install_backend_dependencies() {
  echo "📦 Installing backend dependencies..."

  mkdir -p "${UV_CACHE_DIR}"

  if [[ -f "${BACKEND_DIR}/pyproject.toml" ]]; then
    UV_CACHE_DIR="${UV_CACHE_DIR}" uv sync --project "${BACKEND_DIR}"
  elif [[ -f "${BACKEND_DIR}/requirements.txt" ]]; then
    UV_CACHE_DIR="${UV_CACHE_DIR}" uv pip install -r "${BACKEND_DIR}/requirements.txt"
  else
    echo "❌ No dependency manifest found in backend/." >&2
    exit 1
  fi
}

install_frontend_dependencies() {
  echo "📦 Installing frontend dependencies (npm install)..."
  (
    cd "${FRONTEND_DIR}"
    npm install
  )
}

main() {
  echo "==> Setting up Runway Ops Demo prerequisites"
  ensure_python_version
  ensure_node_version
  ensure_uv_installed
  install_backend_dependencies
  install_frontend_dependencies
  echo "✅ Installation complete. You can now run ./run_dev.sh"
}

main "$@"
