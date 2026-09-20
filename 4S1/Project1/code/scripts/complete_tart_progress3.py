"""Copy and format measured evidence, without experimental computation."""
import json, re, shutil
from pathlib import Path
from markdown_it import MarkdownIt
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'publish/tart-project1/dist'
md=MarkdownIt('commonmark', {'html':False}).enable('table')
catalog=json.loads((OUT/'documents/index.json').read_text(encoding='utf-8'))
for slug,stem,en,th in [
 ('verifier-protocol','cohd-upgrade-protocol-20260915','CoHD verifier: locked protocol','CoHD verifier: ระเบียบวิธีที่ล็อกไว้'),
 ('cctv-protocol','cohd-cctv-protocol-20260915','CCTV: training and test protocol','CCTV: ระเบียบวิธีฝึกและทดสอบ')]:
    original=(ROOT/'docs'/f'{stem}.md').read_text(encoding='utf-8')
    for lang in ['en','th','source']:
        text=original if lang!='th' else '# '+th+'\n\nระเบียบวิธีต้นฉบับด้านล่างเป็นภาษาอังกฤษเพื่อคงรายละเอียดและค่าที่ล็อกไว้ครบถ้วน อ่านรายงานผลภาษาไทยจากหน้า Progress 3 ประกอบ\n\n'+original
        (OUT/'documents'/f'{slug}.{lang}.md').write_text(text,encoding='utf-8')
        if lang!='source':
            html=re.sub(r'^<h1>.*?</h1>\s*','',md.render(text),count=1,flags=re.S)
            html=re.sub(r'<a href="(?!https?://|#)[^"]*">(.*?)</a>',r'\1',html,flags=re.S)
            (OUT/'documents'/f'{slug}.{lang}.html').write_text(html,encoding='utf-8')
    if not any(d['id']==slug for d in catalog):
        catalog.append(dict(id=slug,progress=3,date='2026-09-15',title=dict(en=en,th=th),description=dict(en='Original locked protocol, including training, selection and evaluation rules.',th='ระเบียบวิธีต้นฉบับภาษาอังกฤษ ครบเงื่อนไขฝึก เลือกโมเดล และประเมิน')))
(OUT/'documents/index.json').write_text(json.dumps(catalog,ensure_ascii=False,indent=2),encoding='utf-8')
groups=[('runtime','runtime_optimization_20260915'),('checkpoints','released_checkpoints_20260915'),('verifier','cohd_upgrade_20260915'),('cctv','cohd_cctv_20260915')]
links=[]
for slug,folder in groups:
    source=ROOT/'code/results'/folder
    target=OUT/'research-evidence'/slug
    target.mkdir(parents=True,exist_ok=True)
    selected=list(source.glob('*.json'))
    for sub in ['test_results','regression_results']:
        selected+=list((source/sub).glob('*.json'))
    selected+=list(source.glob('examples.png'))
    entries=[]
    for p in sorted(selected):
        name=(p.parent.name+'_' if p.parent!=source else '')+p.name
        shutil.copy2(p,target/name)
        entries.append(f'<li><a href="research-evidence/{slug}/{name}">{name}</a></li>')
    links.append('<h2>'+slug+'</h2><ul>'+''.join(entries)+'</ul>')
(OUT/'progress3-evidence.html').write_text('<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Progress 3 evidence · tart.project1</title><link rel="stylesheet" href="portal-readable.css"><main style="max-width:1000px;margin:auto;padding:32px"><a href="index.html#progress3">← Progress 3</a><h1>Saved experimental evidence / หลักฐานการทดลอง</h1><p>Original exported scores, protocols, per-expression results, split audits and timing records. No metrics are recomputed by this website. Model weights and raw training caches remain in the research workspace.</p><p>ตัวเลขจากการทดลองที่บันทึกไว้ ไม่มีการคำนวณผลใหม่บนเว็บ น้ำหนักโมเดลและ cache สำหรับฝึกเก็บในพื้นที่วิจัย</p>'+''.join(links)+'</main></html>',encoding='utf-8')
path=OUT/'portal-latest.js'
script=path.read_text(encoding='utf-8')
script += '''
const completeProgress3=progress3;
progress3=function(){completeProgress3();root.insertAdjacentHTML('beforeend',`<section class="panel"><h2>${t('Complete Progress 3 record','บันทึก Progress 3 ทั้งหมด')}</h2><p>${t('Completed experiments and original protocols, in chronological order. Runtime and router Thai editions are summaries; their English downloads preserve the full records. Protocols preserve the English original.','การทดลองที่เสร็จแล้วและระเบียบวิธีต้นฉบับตามลำดับเวลา ฉบับไทยของ runtime และ router เป็นบทสรุป ฉบับอังกฤษเก็บรายละเอียดเต็ม ระเบียบวิธีเก็บต้นฉบับภาษาอังกฤษ')}</p>${docCards(3)}<p><a class="btn" href="progress3-evidence.html">${t('Download saved results, audits and protocols','เปิดผลรายกรณี audit และ protocol ที่บันทึกไว้')}</a></p><h3>${t('Next experiment — not executed','การทดลองถัดไป — ยังไม่ได้ทำ')}</h3><p>${t('Compare original and Custom A with full-image versus full-image plus sliding windows, using matched settings and a new locked CCTV test. Measure small-person recall, false positives and full-image latency including all tiles. No improvement is claimed in advance.','เปรียบเทียบเดิมและ Custom A แบบภาพเต็มกับภาพเต็มร่วม sliding window โดยใช้เงื่อนไขเท่ากันและล็อกชุด CCTV ใหม่ วัด recall คนตัวเล็ก false positive และเวลาต่อภาพที่รวมทุก tile ยังไม่อ้างว่าจะดีขึ้นก่อนทดลอง')}</p></section>`);};
render();
'''
path.write_text(script,encoding='utf-8')
print('Complete Progress 3 library:',len(catalog),'documents; raw evidence copied.')
