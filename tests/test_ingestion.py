from pathlib import Path
from backend.app.services.ingestion import extract_file

def test_txt_extraction(tmp_path: Path):
    p=tmp_path/'x.txt';p.write_text('Project Alpha completed in March 2026.',encoding='utf-8')
    result=extract_file(str(p));assert 'Project Alpha' in result.text

def test_json_extraction(tmp_path: Path):
    p=tmp_path/'x.json';p.write_text('{"budget":"₹5,00,000"}',encoding='utf-8')
    assert 'budget' in extract_file(str(p)).text
