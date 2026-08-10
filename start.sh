
#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")"

if [ ! -d node_modules ] || [ ! -x .venv/bin/python ] || [ ! -x backend ] || [ ! -x src/rpi_sensor ]; then
  echo "PULSE is not prepared on this device. Running one-time setup..."
  ./setup.sh
fi

pkill -f "./backend"        2>/dev/null || true
pkill -f "simulator_stress" 2>/dev/null || true
pkill -f "node backends/server.js" 2>/dev/null || true
pkill -f "processor.py"     2>/dev/null || true
sleep 1

node tools/workshop-check.js --files-only || exit 1

./backend &
BACKEND_PID=$!
sleep 1
if [ "${PULSE_SOURCE:-hardware}" = "simulator" ]; then
  ./simulator_stress &
else
  ./src/rpi_sensor &
fi
SOURCE_PID=$!
sleep 1
node backends/server.js &
SERVER_PID=$!
sleep 2
.venv/bin/python backends/processor.py &
PROCESSOR_PID=$!

cleanup() {
  kill "$BACKEND_PID" "$SOURCE_PID" "$SERVER_PID" "$PROCESSOR_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

echo ""
echo "=============================="
echo "  PULSE is running!"
echo "  Open: http://localhost:3000"
echo "  Check: npm run workshop:check"
echo "=============================="

wait "$BACKEND_PID" "$SOURCE_PID" "$SERVER_PID" "$PROCESSOR_PID"

# replace simulator with ./src/rpi_sensor & if were working with real sensors
