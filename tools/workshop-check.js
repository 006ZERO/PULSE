const fs = require('fs');
const path = require('path');
const http = require('http');

const root = path.join(__dirname, '..');
const filesOnly = process.argv.includes('--files-only');
const checks = [];

function check(name, ok, detail, required = true) {
  checks.push({ name, ok: Boolean(ok), detail, required });
}

const requiredFiles = [
  'dashboard.html',
  'backend.cpp',
  'src/sensor_packet.hpp',
  'backends/server.js',
  'backends/processor.py',
  'fatigue_model.pkl',
  'fatigue_scaler.pkl'
];

for (const relative of requiredFiles) {
  const target = path.join(root, relative);
  check(relative, fs.existsSync(target) && fs.statSync(target).size > 0, 'required project file');
}

for (const dependency of ['express', 'ws']) {
  try {
    require.resolve(dependency, { paths: [root] });
    check(`Node dependency: ${dependency}`, true, 'installed');
  } catch {
    check(`Node dependency: ${dependency}`, false, 'run npm install');
  }
}

if (process.platform === 'linux') {
  for (const binary of ['backend', 'src/rpi_sensor']) {
    const target = path.join(root, binary);
    let executable = false;
    try { fs.accessSync(target, fs.constants.X_OK); executable = true; } catch {}
    check(`Executable: ${binary}`, executable, executable ? 'ready' : 'missing or not executable');
  }
} else {
  check('Hardware runtime', true, 'Linux/Pi executables are checked on the workshop device', false);
}

function printAndExit() {
  console.log('\nPULSE workshop readiness\n');
  for (const item of checks) {
    const mark = item.ok ? 'PASS' : item.required ? 'FAIL' : 'INFO';
    console.log(`${mark.padEnd(4)}  ${item.name.padEnd(34)} ${item.detail}`);
  }
  const failures = checks.filter(item => item.required && !item.ok);
  console.log(`\n${failures.length ? `${failures.length} required check(s) failed.` : 'All required checks passed.'}\n`);
  process.exitCode = failures.length ? 1 : 0;
}

if (filesOnly) {
  printAndExit();
} else {
  const request = http.get('http://localhost:3000/api/health', { timeout: 2500 }, response => {
    let body = '';
    response.on('data', chunk => body += chunk);
    response.on('end', () => {
      try {
        const health = JSON.parse(body);
        check('Dashboard server', health.server === 'ok', `HTTP ${response.statusCode}`);
        check('Sensor telemetry', health.telemetry === 'live', health.telemetry === 'live' ? 'packets arriving' : 'no packet in the last 3 seconds');
        check('Session storage', Number.isInteger(health.sessions), `${health.sessions || 0} saved session(s)`);
      } catch {
        check('Dashboard server', false, 'invalid health response');
      }
      printAndExit();
    });
  });
  request.on('timeout', () => request.destroy(new Error('timeout')));
  request.on('error', () => {
    check('Dashboard server', false, 'start PULSE before the live readiness check');
    check('Sensor telemetry', false, 'dashboard server unavailable');
    printAndExit();
  });
}
