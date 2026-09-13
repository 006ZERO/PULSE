from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle
from reportlab.graphics.barcode import qr
from reportlab.graphics.shapes import Drawing
from reportlab.graphics import renderPDF
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'output/pdf/PULSE_Judges_Presentation.pdf'
OUT.parent.mkdir(parents=True,exist_ok=True)
c=canvas.Canvas(str(OUT),pagesize=(1280,720));c.setTitle('PULSE - See the effort. Understand the recovery.');c.setAuthor('PULSE project team')
W='#F5F6F8';M='#A9B2BE';B='#4C8DFF';T='#55C3A3';D='#101316';L='#303841'
def rect(x,y,w,h,col):
 c.setFillColor(HexColor('#'+col.lstrip('#')));c.rect(x,720-y-h,w,h,fill=1,stroke=0)
def txt(x,y,s,size=22,col=W,bold=False):
 c.setFillColor(HexColor('#'+col.lstrip('#')));c.setFont('Helvetica-Bold' if bold else 'Helvetica',size);c.drawString(x,720-y,s)
def p(x,y,s,w=1000,size=24,col=M):
 a=Paragraph(s,ParagraphStyle('s',fontName='Helvetica',fontSize=size,leading=size*1.3,textColor=HexColor(col)));_,h=a.wrap(w,600);a.drawOn(c,x,720-y-h)
def line(x,y,x2,y2,col=L,width=1):
 c.setStrokeColor(HexColor(col));c.setLineWidth(width);c.line(x,720-y,x2,720-y2)
def base(n,kicker):
 rect(0,0,1280,720,D);txt(52,45,'PULSE',22,bold=True);txt(175,44,kicker.upper(),11,M)
 line(52,666,1228,666);txt(52,691,'PULSE  /  SPORTS-PERFORMANCE RESEARCH PROTOTYPE',10,M);txt(1160,691,f'{n:02d} / 09',11,M)
def end():c.showPage()
def title(a,b=None):
 txt(52,133,a,48,bold=True)
 if b:txt(52,192,b,48,bold=True)
def tag(x,y,a,b):txt(x,y,a,13,B,True);p(x,y+16,b,320,23,W)

base(1,'Sport-Tech Hackathon 2026 / first place')
txt(52,230,'See the effort.',76,bold=True);txt(52,317,'Understand',76,bold=True);txt(52,404,'the recovery.',76,bold=True)
p(56,453,'A live view of pulse, movement and workload.<br/>Built around a Raspberry Pi.',650,25)
for i,h in enumerate([30,44,24,78,132,210,265,305,280,230,190,154,126,112]):
 rect(805+i*27,550-h,10,h,B if i<9 else T)
txt(800,593,'EFFORT',13,B,True);txt(1065,593,'RECOVERY',13,T,True)
txt(800,620,'Concept graphic - not recorded data',11,M)
end()

base(2,'The coaching question');title('The number is only','part of the story.')
txt(70,344,'PULSE',18,B,True);txt(455,344,'MOVEMENT',18,B,True);txt(880,344,'RECOVERY',18,T,True)
txt(70,433,'How hard?',40,bold=True);txt(455,433,'What changed?',40,bold=True);txt(880,433,'What next?',40,bold=True)
line(410,300,410,483);line(835,300,835,483)
p(70,457,'Read cardiovascular response.',320,20);p(455,457,'Track the activity context.',320,20);p(880,457,'Observe after stopping.',300,20)
p(52,573,'PULSE brings these observations into one session a coach can review.',1150,29,W);end()

base(3,'The product');title('One session. A shared view.')
rect(52,182,1176,360,'1B2026')
rect(52,182,163,360,'171B20');txt(70,215,'PULSE',18,bold=True)
for i,s in enumerate(['Live session','Athlete overview','Session history']):txt(70,274+i*46,s,13,B if i==0 else M)
txt(244,222,'Performance monitor',25,bold=True)
for x,a,u in [(244,'Heart rate','BPM'),(482,'Blood oxygen','SpO2'),(720,'Movement','G'),(958,'Elapsed','TIME')]:
 txt(x,268,a,12,M);txt(x,310,'--',32,bold=True);txt(x+56,309,u,10,M)
rect(244,335,633,177,'14181D');txt(266,363,'Heart rate activity',15,bold=True)
for y in [390,430,470]:line(266,y,854,y)
txt(429,445,'Waiting for valid readings',15,M)
txt(910,367,'Fatigue model',15,bold=True);txt(910,417,'-- / 100',34,B,True);txt(910,457,'Quality-aware display',15,M)
txt(53,563,'Dashboard schematic based on the implemented interface; no sample readings shown.',12,M)
tag(52,605,'LIVE','Watch signals together.');tag(475,605,'REVIEW','Switch athletes and sessions.');tag(890,605,'EXPORT','Take the evidence away.');end()

base(4,'Engineering');title('From wearable to browser.','Inference stays on the Pi.')
steps=[('01','SENSE','MAX30100 optical sensor<br/>ADXL345 accelerometer'),('02','TRANSPORT','C++ acquisition<br/>UDP + shared memory'),('03','INTERPRET','Python signal checks<br/>Random Forest model'),('04','DISPLAY','Node.js + WebSockets<br/>Local browser dashboard')]
for i,(a,b,d) in enumerate(steps):
 x=52+i*300;txt(x,295,a,58,'29343F',True);line(x,320,x+255,320,B,3);txt(x,363,b,21,B,True);p(x,387,d,260,20)
 if i<3:txt(x+265,363,'>',24,M)
p(52,540,'One pipeline for the real sensors and the clearly labeled stress simulator.',1150,28,W)
p(52,597,'Current web dependencies: fonts and PDF library load externally. Full offline packaging still needs testing.',1150,15);end()

base(5,'The live demonstration');title('Rest. Move. Recover.')
for i,(num,name,desc) in enumerate([('01','REST','Capture a stable baseline and a simultaneous reference pulse.'),('02','EXERCISE','Mark the activity. Watch pulse, movement and signal quality.'),('03','RECOVERY','Mark the stop. Follow the change from recovery onset.')]):
 x=52+i*400;txt(x,285,num,74,B if i<2 else T,True);txt(x,344,name,25,bold=True);p(x,374,desc,335,24)
rect(52,532,1176,81,'20262D');txt(76,582,'End session',25,bold=True);txt(317,582,'>',25,M);txt(380,582,'Show history',25,bold=True);txt(650,582,'>',25,M);txt(726,582,'Export evidence',25,T,True)
txt(52,641,'An alert depends on the observed signals. A short trial may produce no alert.',16,M);end()

base(6,'Interpreting an alert');title('Give the alert context.')
p(52,197,'The model produces a score.<br/>The interface adds observable trends.',480,30,W)
p(52,375,'Enough valid rest samples are required before baseline comparisons appear.',420,21)
for i,(a,b) in enumerate([('Pulse versus rest','Change from the recorded resting average.'),('Recent movement trend','Change in acceleration magnitude, including gravity.'),('Recovery response','Pulse change since recovery was marked.')]):
 y=212+i*116;line(609,y,1220,y);txt(624,y+37,a,26,T,True);p(624,y+50,b,575,19)
p(52,579,'These descriptions accompany the alert. They are not model feature attribution or evidence of causation.',1150,23,M);end()

base(7,'Demonstrating trust');title('A missing reading','is an honest answer.')
for i,(a,b,col) in enumerate([('VALID CONTACT','Show accepted measurements.',T),('REMOVE CONTACT','Poor signal. Values clear.',B),('RESTORE CONTACT','Wait for valid readings to resume.',T)]):
 x=52+i*400;line(x,296,x+340,296,col,4);txt(x,345,a,20,col,True);p(x,370,b,340,27,W)
p(52,505,'Rehearsal check: stop the source and verify stale values clear too.',1140,28,W)
p(52,579,'Signal handling is implemented. Its behavior on the assembled wearable must still be verified.',1140,21);end()

base(8,'The evidence standard');title('Measure accuracy.','Then make the claim.')
txt(52,294,'PAIR',18,B,True);p(52,319,'PULSE + reference device<br/>Same moment. Same condition.',410,26,W)
txt(52,455,'REPEAT',18,T,True);p(52,480,'Rest, exercise and recovery.<br/>Multiple sessions and participants.',430,24,W)
rect(582,252,646,330,'1B2026');txt(610,294,'VALIDATION PROTOCOL',13,B,True)
for i,(a,b) in enumerate([('Record','Reference model, PULSE HR, time, phase'),('Calculate','Signed error and mean absolute error'),('Retain','Session evidence + exported report')]):
 y=341+i*75;txt(610,y,a,20,bold=True);p(610,y+9,b,574,17)
p(52,612,'No measured accuracy results are claimed here. Physical validation is the next milestone.',1140,20,T);end()

base(9,'The next milestone');title('From a hackathon winner','to a tested wearable.')
tag(52,290,'BUILT','Sensor-to-dashboard pipeline.<br/>Sessions and evidence export.')
tag(468,290,'NEXT','Secure the enclosure.<br/>Run reference-device trials.')
tag(878,290,'SEEKING','Feedback on the protocol.<br/>A supervised pilot opportunity.')
p(52,438,'See the effort. Understand the recovery.',940,38,W)
p(52,505,'Research prototype: uncalibrated SpO2 estimate, motion-based respiration and a fatigue model requiring validation. No clinical or injury-prevention claim.',930,18)
txt(52,620,'github.com/006ZERO/PULSE',20,T)
c.linkURL('https://github.com/006ZERO/PULSE',(52,89,470,119),relative=0)
q=qr.QrCodeWidget('https://github.com/006ZERO/PULSE');bounds=q.getBounds();d=Drawing(115,115,transform=[115/(bounds[2]-bounds[0]),0,0,115/(bounds[3]-bounds[1]),0,0]);d.add(q);rect(1085,488,125,125,'FFFFFF');renderPDF.draw(d,c,1090,112)
end();c.save();print(OUT)
