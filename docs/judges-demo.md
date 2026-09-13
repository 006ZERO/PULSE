# PULSE: live demonstration guide

## Opening (30 seconds)

“PULSE is a sports-performance research prototype. It combines optical and movement sensors with local machine learning to explore changes in workload and recovery. Today we will show the measurements, compare them with a reference device, and demonstrate how the interface handles unreliable contact.”

## Rehearsal sequence

1. Start the complete stack on the Pi. Keep the accelerometer flat, Z-axis upward, during startup calibration. Open the dashboard through HTTP.
2. Name the athlete and session. Start recording; the experiment begins in Rest. Collect at least 30 seconds of stable readings. Enter the reference device and simultaneous reference heart rate, then capture a comparison.
3. Mark Exercise. Use a familiar, comfortable short activity with the volunteer's agreement. Keep the optical sensor secured. Explain that motion may reduce optical quality.
4. Show the measurements and model output. If an alert occurs, read the observed trends. They describe accompanying measurements, not proven model feature contributions. Do not increase exercise just to force an alert; a short experiment may produce none.
5. Mark Recovery when the volunteer stops. Show heart-rate change from that marker. Capture another reference comparison; capture the exercise comparison only when a simultaneous trustworthy reading is available.
6. Briefly remove optical contact. Verify Poor signal appears. Reattach and allow several valid beats. Separately stop the source during rehearsal and check that the dashboard clears stale measurements.
7. End and save. Open the experiment evidence details in session history. Export the current-session PDF, which includes phase times and reference comparisons. Download JSON before starting another session if you also need the valid measurement samples; phase markers and comparisons are saved with the session, while those samples are download-only. Up to 100 markers and comparisons are retained per session.

## Evidence to collect

The comparison form starts empty. Record real simultaneous readings and the reference device model. Signed error is PULSE minus reference HR; mean absolute error summarizes only the captured comparisons. Record sensor position, attachment, source mode, activity and relevant signal issues separately. A few comparisons demonstrate a test procedure, not general accuracy.

## Physical preparation

- Secure the sensor against shifting; route cables with strain relief and cover exposed connections.
- Label the sensor connections and enclosure. Keep optical openings unobstructed.
- Verify power stability and carry spare cables and a suitable power supply.
- Photograph the assembled wearable and explain its present limitations.

## Backup preparation

- Rehearse with the real Pi and reference device before the event.
- Record a 60–90 second real demonstration with participant permission; show its recording date when played.
- Capture dashboard screenshots and an exported PDF from that session.
- Keep a repository copy and installed dependencies on the Pi. Test the complete workflow with internet disconnected: fonts and jsPDF currently use external URLs, so PDF export may need internet or locally bundled dependencies.
- Keep simulator mode available and label it explicitly as simulated: `PULSE_SOURCE=simulator ./start.sh`. It cannot establish measurement accuracy.
- Run only one PULSE stack at a time. End/save before Ctrl+C; verify the source process has stopped before switching modes.

## Scope to communicate

The optical algorithm and fatigue model need physical and participant validation. SpO₂ is an uncalibrated estimate; respiration is estimated from motion. Avoid claims of injury prediction, clinical accuracy, or proven prevention. Physical enclosure work, reference measurements, screenshots, a recorded demonstration and full offline packaging require separate completion on the actual setup.
