
#!/bin/bash
cd "$(dirname "$0")"

pkill -f "./backend"        2>/dev/null
pkill -f "simulator_stress" 2>/dev/null
pkill -f "node backends/server.js" 2>/dev/null
pkill -f "processor.py"     2>/dev/null
sleep 1

node tools/workshop-check.js --files-only || exit 1

./backend &
sleep 1
if [ "${PULSE_SOURCE:-hardware}" = "simulator" ]; then
  ./simulator_stress &
else
  ./src/rpi_sensor &
fi
sleep 1
node backends/server.js &
sleep 2
python3 backends/processor.py &

echo ""
echo "=============================="
echo "  PULSE is running!"
echo "  Open: http://localhost:3000"
echo "  Check: npm run workshop:check"
echo "=============================="

wait

# replace simulator with ./src/rpi_sensor & if were working with real sensors
