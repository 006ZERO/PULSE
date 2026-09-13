/* Workshop observations are descriptive rules, not model feature attribution. */
(() => {
  const panel = document.createElement('section');
  panel.className = 'timeline-panel';
  panel.innerHTML = `<h3>Live experiment</h3>
    <p style="margin:8px 0;color:var(--muted)">Mark each phase as it happens. Alerts depend on measurements; they are never forced.</p>
    <div id="experiment-controls"><button class="button" data-phase="Rest">Rest</button> <button class="button" data-phase="Exercise">Exercise</button> <button class="button" data-phase="Recovery">Recovery</button></div>
    <p id="experiment-phase" style="margin:10px 0">Start a session to mark phases.</p>
    <p id="experiment-observations" aria-live="polite">Waiting for valid readings.</p>
    <details style="margin-top:16px"><summary>Reference-device validation</summary>
    <p style="margin:10px 0">Enter a simultaneous reference HR. PULSE captures its latest valid reading. Signed error = PULSE − reference. Download results before leaving this page.</p>
    <label>Reference device <input id="reference-device" class="field" maxlength="80" placeholder="Device name/model"></label>
    <label>Reference HR (BPM) <input id="reference-hr" class="field" type="number" min="30" max="240" step="1"></label>
    <button class="button" id="capture-reference">Capture comparison</button> <button class="button" id="download-evidence">Download session evidence</button>
    <p id="reference-status" role="status"></p><div id="reference-results"></div></details>`;
  document.querySelector('.timeline-panel').after(panel);
  const el = id => document.getElementById(id);
  let phase = '', events = [], comparisons = [], samples = [], latest = null, recoveryHR = null;
  const currentTime = () => Math.floor((Date.now() - sessionStart) / 1000);
  const evidence = () => ({events:events.slice(0,100),comparisons:comparisons.slice(0,100)});
  const originalSave = saveSession;
  saveSession = record => originalSave({...record,evidence:evidence()});
  function comparisonTable(rows) {
    const table=document.createElement('table');table.style.cssText='width:100%;text-align:left;margin-top:12px;line-height:2';
    const head=table.createTHead().insertRow();
    ['Condition','Reference device','Reference HR','PULSE HR','Error (BPM)'].forEach(title=>{const th=document.createElement('th');th.textContent=title;head.appendChild(th)});
    const body=table.createTBody();
    rows.forEach(r=>{const row=body.insertRow();[r.phase,r.device,r.reference,r.pulse,`${r.error>=0?'+':''}${r.error}`].forEach(v=>row.insertCell().textContent=v)});
    return table;
  }
  const originalHistory = renderHistory;
  renderHistory = function() {
    originalHistory();
    savedSessions.filter(s=>s.evidence?.events?.length || s.evidence?.comparisons?.length).forEach(s=>{
      const details=document.createElement('details'),summary=document.createElement('summary'),phases=document.createElement('p');
      details.style.padding='12px';summary.textContent=`${s.athlete} — ${s.title}: experiment evidence`;
      phases.textContent=s.evidence.events.map(e=>`${formatDuration(e.seconds)} ${e.phase}`).join(' → ');
      details.append(summary,phases,comparisonTable(s.evidence.comparisons));el('history-list').appendChild(details);
    });
  };
  window.appendWorkshopReport = doc => {
    doc.addPage();let y=20;
    const line=text=>{if(y>275){doc.addPage();y=20}doc.text(String(text),14,y);y+=7};
    doc.setFont('helvetica','normal');doc.setFontSize(10);doc.setTextColor(30,30,30);
    line('Experiment evidence');line('Observed trends are not model feature attribution.');
    events.forEach(e=>line(`${formatDuration(e.seconds)}  ${e.phase}`));
    line('Condition | Reference HR | PULSE HR | Error (BPM)');
    if(!comparisons.length)line('No reference comparisons recorded.');
    comparisons.forEach(r=>{line(`${r.phase} | ${r.reference} | ${r.pulse} | ${r.error>=0?'+':''}${r.error}`);doc.splitTextToSize(`Reference device: ${r.device}`,180).forEach(line)});
  };
  const fresh = () => latest && Date.now() - latest.at < 3000;
  function mark(name) {
    if (!sessionActive) return;
    phase = name;
    events.push({phase, seconds: currentTime()});
    if (phase === 'Recovery') recoveryHR = fresh() ? latest.hr : null;
    el('experiment-phase').textContent = events.map(e => `${formatDuration(e.seconds)} ${e.phase}`).join(' → ');
  }
  panel.querySelectorAll('[data-phase]').forEach(b => b.onclick = () => mark(b.dataset.phase));
  function observations(d) {
    const rest = samples.filter(s => s.phase === 'Rest');
    const reasons = [];
    if (rest.length >= 10) {
      const baseline = rest.reduce((a,s) => a+s.hr,0)/rest.length;
      const delta = latest.hr-baseline;
      reasons.push(`Heart rate ${delta >= 0 ? '+' : ''}${Math.round(delta)} BPM versus recorded rest (${Math.round(baseline)} BPM).`);
    } else reasons.push('Rest baseline needs at least 10 valid seconds.');
    if (Number.isFinite(d.movement_trend) && d.movement_trend < 1)
      reasons.push(`Acceleration magnitude decreased ${Math.round((1-d.movement_trend)*100)}% across the recent model window (includes gravity).`);
    if (phase === 'Recovery' && recoveryHR !== null)
      reasons.push(`Heart rate change since recovery began: ${Math.round(latest.hr-recoveryHR)} BPM.`);
    const prefix = d.fatigue_warning ? 'Why this alert? Model threshold crossed. Observed alongside the alert: ' : 'Observed measurements: ';
    el('experiment-observations').textContent = prefix + reasons.join(' ') + ' These observations do not establish the model’s causal reasons.';
  }
  function invalidate() {
    latest = null;
    if (!sessionActive) return;
    metric('hr-val','—','BPM'); metric('spo2-val','—','SpO₂');
    metric('rr-val','—','BR/MIN'); metric('mag-val','—','G');
    el('fatigue-score').textContent = '—'; el('fatigue-bar').style.width = '0';
    el('fatigue-banner').style.display = 'none'; updateRecovery(false,0,0);
    el('ts-val').textContent = 'Poor signal';
    el('experiment-observations').textContent = 'Poor signal — observations paused. Previous chart points are historical.';
  }
  const originalUpdate = update;
  update = function(d) {
    const valid = Number.isFinite(d.heart_rate) && d.heart_rate >= 35 && d.heart_rate <= 230 && Number.isFinite(d.spo2) && d.spo2 > 0 && d.signal_quality >= 25 && d.sensor_health?.timestamp !== 'stale' && d.sensor_health?.pulse !== 'fault';
    if (!valid) { updateSensorHealth(d,0,0); invalidate(); return; }
    originalUpdate(d);
    if (!sessionActive) return;
    latest = {hr:d.heart_rate,at:Date.now(),quality:d.signal_quality};
    if (!samples.length || currentTime() !== samples[samples.length-1].seconds)
      samples.push({seconds:currentTime(),phase,hr:d.heart_rate,spo2:d.spo2,quality:d.signal_quality,fatigue:d.fatigue_score});
    observations(d);
  };
  const originalStart = startSession;
  startSession = function() {
    originalStart();
    if (!sessionActive) return;
    phase=''; events=[]; comparisons=[]; samples=[]; latest=null; recoveryHR=null;
    el('reference-results').textContent=''; el('reference-status').textContent=''; mark('Rest');
  };
  el('capture-reference').onclick = () => {
    const reference=Number(el('reference-hr').value), device=el('reference-device').value.trim();
    if (!sessionActive || !fresh() || !phase || !device || !Number.isFinite(reference) || reference<30 || reference>240) {
      el('reference-status').textContent='A live session, valid PULSE signal, phase, device name and reference HR (30–240) are required.'; return;
    }
    if(comparisons.length>=100){el('reference-status').textContent='100 comparisons captured; download evidence or end this session.';return;}
    comparisons.push({phase,seconds:currentTime(),device,reference,pulse:latest.hr,error:latest.hr-reference,quality:latest.quality});
    el('reference-status').textContent=`${comparisons.length} comparisons captured. Mean absolute error: ${(comparisons.reduce((s,r)=>s+Math.abs(r.error),0)/comparisons.length).toFixed(1)} BPM (this session only).`;
    el('reference-results').replaceChildren(comparisonTable(comparisons));
  };
  el('download-evidence').onclick = () => {
    const blob=new Blob([JSON.stringify({athlete:athleteName,title:sessionTitle,started:new Date(sessionStart).toISOString(),events,comparisons,samples,notes:'Manual phase markers and reference entries. Observational rules are not model attribution. Source mode must be documented by the operator.'},null,2)],{type:'application/json'});
    const url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download=`pulse-evidence-${sessionStart}.json`;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
  };
  setInterval(()=>{if(sessionActive && !fresh()) invalidate();},1000);
})();
