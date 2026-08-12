#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

echo ""
echo "PULSE workshop setup"
echo "===================="

for command in node npm python3 g++; do
  if ! command -v "$command" >/dev/null 2>&1; then
    echo "Missing required command: $command"
    exit 1
  fi
done

echo "[1/4] Installing Node dependencies"
if [ -f package-lock.json ]; then
  npm ci --omit=dev
else
  npm install --omit=dev
fi

echo "[2/4] Preparing Python environment"
if [ ! -x .venv/bin/python ]; then
  python3 -m venv .venv
fi
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt

echo "[3/4] Compiling native services"
g++ -std=c++23 -O3 -Isrc backend.cpp -o backend -lrt
g++ -std=c++23 -O3 -Isrc simulator_stress.cpp -o simulator_stress
g++ -std=c++23 -O3 -Isrc src/rpi_sensor_the_pi_version.cpp -o src/rpi_sensor
chmod +x backend simulator_stress src/rpi_sensor start.sh

echo "[4/4] Running offline readiness checks"
node tools/workshop-check.js --files-only

echo ""
echo "Setup complete. Start PULSE with:"
echo "  ./start.sh"
echo ""
