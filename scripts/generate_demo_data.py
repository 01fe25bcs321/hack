from pathlib import Path
import csv, json
from docx import Document
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

ROOT=Path(__file__).resolve().parents[1]/'data'/'demo'
ROOT.mkdir(parents=True,exist_ok=True)
(ROOT/'budget.json').write_text(json.dumps({'project':'Project Alpha','budget':'₹6,00,000','sponsor':'Northstar Systems','project_id':'ALPHA-2026'},ensure_ascii=False,indent=2),encoding='utf-8')
with open(ROOT/'milestones.csv','w',newline='',encoding='utf-8') as f:
    w=csv.DictWriter(f,fieldnames=['milestone','status','date']);w.writeheader();w.writerows([{'milestone':'Prototype','status':'Completed','date':'March 2026'},{'milestone':'Pilot','status':'In progress','date':'June 2026'}])
(ROOT/'manager_notes.txt').write_text('Project Alpha was completed in March 2026 for the prototype milestone. Current project budget is ₹5,00,000. The pilot is in progress. Northstar Systems is the sponsor.',encoding='utf-8')
d=Document();d.add_heading('Project Alpha Status',0);d.add_paragraph('Project Alpha prototype was completed in March 2026. The current budget is ₹6,00,000. The pilot is in progress.');t=d.add_table(rows=1,cols=2);t.rows[0].cells[0].text='Owner';t.rows[0].cells[1].text='Northstar Systems';d.save(ROOT/'team_status.docx')
pdf=canvas.Canvas(str(ROOT/'project_report.pdf'),pagesize=A4);pdf.setFont('Helvetica',16);pdf.drawString(60,780,'Project Alpha Report');pdf.setFont('Helvetica',11);pdf.drawString(60,750,'Project Alpha prototype was completed in March 2026.');pdf.drawString(60,730,'The approved project budget is ₹5,00,000.');pdf.drawString(60,710,'The pilot phase is currently in progress.');pdf.save()
print(ROOT)
