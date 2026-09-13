from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'output/pdf/PULSE_Judges_Presentation.pdf'
OUT.parent.mkdir(parents=True,exist_ok=True)
c=canvas.Canvas(str(OUT),pagesize=(960,540))
c.setTitle('PULSE | Athlete performance research prototype')
c.setAuthor('PULSE')
WHITE='#F3F4F6'; MUTED='#A8AFBA'; BLUE='#4C8DFF'; TEAL='#55C3A3'; BG='#111315'
def text(x,y,s,size=18,color=WHITE,bold=False):
    c.setFillColor(HexColor(color));c.setFont('Helvetica-Bold' if bold else 'Helvetica',size);c.drawString(x,540-y,s)
def para(x,y,s,width=800,size=19,color=MUTED):
    p=Paragraph(s,ParagraphStyle('p',fontName='Helvetica',fontSize=size,leading=size*1.4,textColor=HexColor(color)))
    _,h=p.wrap(width,400);p.drawOn(c,x,540-y-h);return h
def page(n,label,title):
    c.setFillColor(HexColor(BG));c.rect(0,0,960,540,fill=1,stroke=0)
    text(42,40,'PULSE',18,bold=True);text(145,39,label.upper(),10,MUTED)
    text(42,110,title,34,bold=True)
    c.setStrokeColor(HexColor('#30363D'));c.line(42,44,918,44)
    text(42,516,'SPORTS-PERFORMANCE RESEARCH PROTOTYPE',9,MUTED)
    text(875,516,f'{n:02d} / 08',10,MUTED)
def finish():c.showPage()
def block(x,y,num,title,body,w=260):
    text(x,y,num,12,BLUE,True);text(x,y+31,title,21,bold=True);para(x,y+49,body,w,16)

page(1,'Project introduction','See workload. Follow recovery.')
para(42,144,'Optical sensing, movement data and local machine learning in one live athlete session.',780,25,WHITE)
text(42,272,'SENSE',13,BLUE,True);text(340,272,'INTERPRET',13,BLUE,True);text(642,272,'REVIEW',13,BLUE,True)
para(42,290,'Pulse and acceleration<br/>from a Raspberry Pi node.',250,18)
para(340,290,'Live signals, quality checks<br/>and a fatigue model score.',250,18)
para(642,290,'Athlete sessions, reference<br/>comparisons and PDF reports.',270,18)
text(42,432,'First place - Sport-Tech Hackathon 2026',16,TEAL,True)
para(42,450,'Workshop presentation | PULSE project team',800,12)
finish()

page(2,'The purpose','Make the session easier to understand.')
para(42,146,'A coach needs context: how the athlete is moving, how pulse changes, and what happens after activity stops.',820,22)
block(42,257,'01','Observe together','Place optical and movement measurements on the same live dashboard.')
block(346,257,'02','Keep context','Mark rest, exercise and recovery so changes can be discussed in sequence.')
block(650,257,'03','Review evidence','Keep session summaries and compare PULSE against a reference device.')
para(42,429,'Research question: can combined signals support useful workload and recovery observations?',830,18,TEAL)
finish()

page(3,'Engineering','Local processing, from sensor to screen.')
nodes=[('SENSORS','MAX30100 + ADXL345'),('C++','Acquisition + UDP'),('PYTHON','Quality + inference'),('BROWSER','Live dashboard')]
for i,(a,b) in enumerate(nodes):
    x=42+i*225
    c.setFillColor(HexColor('#20242A'));c.rect(x,285,201,82,fill=1,stroke=0)
    text(x+14,199,a,14,BLUE,True);para(x+14,215,b,175,13,WHITE)
    if i<3:text(x+205,216,'>',18,MUTED)
block(42,310,'ACQUISITION','Two I2C buses','MAX30100: bus 0, address 0x57.<br/>ADXL345: bus 1, address 0x53.',270)
block(346,310,'TRANSPORT','Shared packet','C++ receives UDP packets and writes shared memory for Python.',270)
block(650,310,'DELIVERY','WebSockets','The Node.js server sends telemetry to a browser on the local network.',270)
para(42,449,'Inference runs locally. The dashboard currently loads fonts and the PDF library from external services.',855,12)
finish()

page(4,'Live experiment','One athlete. Three visible phases.')
block(42,171,'01 / REST','Establish a baseline','Start recording. Collect stable pulse readings and capture a simultaneous reference HR.',265)
block(346,171,'02 / EXERCISE','Observe the response','Mark a short, familiar activity. Watch movement, pulse and signal quality change.',265)
block(650,171,'03 / RECOVERY','Follow the change','Mark the stop. Show pulse change from recovery onset and take another comparison.',265)
para(42,351,'Then: end and save the session, open its evidence in history, and export the PDF.',840,23,WHITE)
para(42,428,'An alert is not guaranteed during a short trial. Demonstrate the actual response; do not force fatigue.',835,16,TEAL)
finish()

page(5,'Interpretation','Explain what is observed.')
para(42,149,'When the fatigue threshold is crossed, the dashboard adds measurement context.',820,21)
block(42,236,'BASELINE','Pulse versus rest','Difference from the recorded resting average, after enough valid samples.',265)
block(346,236,'MOVEMENT','Recent signal trend','Percentage change in acceleration magnitude across the model window; gravity is included.',265)
block(650,236,'RECOVERY','Change after stopping','Heart-rate change from the manually marked start of recovery.',265)
para(42,415,'These are descriptive observations alongside the model output, not proven causes or model feature contributions.',850,18,TEAL)
finish()

page(6,'Measurement validation','Show the error. Keep the evidence.')
para(42,143,'Capture simultaneous readings and record the reference device. No measured validation results are claimed in this presentation.',860,18)
headers=['CONDITION','REFERENCE HR','PULSE HR','ERROR']
xs=[58,300,520,730]
for x,s in zip(xs,headers):text(x,230,s,12,BLUE,True)
for i,phase in enumerate(['Rest','Exercise','Recovery']):
    y=278+i*46
    c.setStrokeColor(HexColor('#30363D'));c.line(42,540-y+30,918,540-y+30)
    for x,s in zip(xs,[phase,'To be measured','To be measured','Not available']):text(x,y,s,17)
para(42,404,'Signed error = PULSE HR - reference HR. The dashboard also computes mean absolute error for captured comparisons.',860,16,TEAL)
para(42,460,'Next: compare at rest, during activity and recovery across participants and repeated sessions.',855,13)
finish()

page(7,'Trust and limitations','Know when a reading is unreliable.')
block(42,166,'LIVE CHECK','Remove contact','Demonstrate Poor signal. Invalid readings should clear instead of appearing as a believable pulse.',265)
block(346,166,'TRANSPORT CHECK','Stop the source','Repeated old packets are not forwarded as fresh measurements. Verify this during rehearsal.',265)
block(650,166,'RECOVERY CHECK','Restore contact','Allow several valid beats before discussing the resumed measurements.',265)
para(42,354,'Current limits',20,18,BLUE) if False else None
text(42,359,'CURRENT LIMITS',12,BLUE,True)
para(42,375,'SpO2 uses an uncalibrated optical estimate. Respiration is estimated from movement. The pulse algorithm and fatigue model still require physical validation. This is not a medical device or demonstrated injury-prevention system.',860,17)
finish()

page(8,'Next steps','Turn a working prototype into evidence.')
block(42,167,'BUILD','Secure the wearable','Enclosure, stable attachment, strain relief and reliable power. Test in the final wearing position.',265)
block(346,167,'VALIDATE','Repeat the experiment','Reference-device comparisons, participant trials, motion testing and a 20-30 minute stability run.',265)
block(650,167,'DEMONSTRATE','Prepare the fallback','Clearly labeled simulator, a real recorded demo, screenshots and a tested offline setup.',265)
para(42,370,'Seeking feedback on the experiment, sensor placement and validation protocol.',850,24,WHITE)
text(42,457,'Code and setup guide: github.com/006ZERO/PULSE',16,TEAL)
c.linkURL('https://github.com/006ZERO/PULSE',(42,72,510,99),relative=0)
finish();c.save()
print(OUT)
