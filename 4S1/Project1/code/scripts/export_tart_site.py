"""Export saved research presentation only; never evaluates models."""
import json, re, shutil
from pathlib import Path
from markdown_it import MarkdownIt
ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT/'publish/tart-project1/dist'
shutil.copytree(ROOT/'code/webapp/static', OUT, dirs_exist_ok=True)
md = MarkdownIt('commonmark', {'html': False}).enable('table')
catalog = json.loads((OUT/'documents/index.json').read_text(encoding='utf-8'))
reports = [
 ('runtime', 'runtime-optimization-20260915', 'LISA runtime optimization', 'การลดเวลาประมวลผล LISA'),
 ('router', 'router-research-20260915', 'Learned router: accuracy–runtime trade-off', 'Router: ผลแลกเปลี่ยนความแม่นยำกับเวลา'),
 ('checkpoints', 'released-checkpoints-20260915', 'Released SSP-SAM and CoHD-Tiny', 'เปรียบเทียบ SSP-SAM และ CoHD-Tiny'),
 ('verifier', 'cohd-upgrade-20260915', 'CoHD verifier: 300-image test', 'ตัวตรวจสอบ CoHD: ทดสอบ 300 ภาพ'),
 ('cctv', 'cohd-cctv-20260915', 'CoHD Custom A/B: real CCTV', 'CoHD Custom A/B: ภาพ CCTV จริง'),
]
thai = {
 'runtime': '# การลดเวลาประมวลผล LISA\n\n## สิ่งที่เปลี่ยน\nใช้ KV cache ระหว่างสร้างข้อความ แล้วประมวลผล prefix สำหรับแบ่งส่วนภาพอีกครั้ง เป็นการปรับประสิทธิภาพ ไม่ใช่สถาปัตยกรรมใหม่\n\n## ผลที่วัดได้\nภาพพัฒนา 3 ภาพ ใช้เวลาส่วน LISA จาก 44.78–46.78 เหลือ 13.47–14.14 วินาที มาสก์และข้อความเหมือนเดิม\n\n## เวลาทั้งระบบ\nคำขอแบบ cold หนึ่งกรณีลดจาก 109.9159 เป็น 75.1975 วินาที ตัวเลข 13–14 วินาทีไม่ใช่เวลาทั้ง pipeline\n\n## ข้อจำกัด\nตัวอย่างน้อย อ่านวิธีและหลักฐานฉบับเต็มใน English\n',
 'router': '# ผลการทดลอง Router\n\n## วิธี\nพัฒนาบนข้อมูลเดิม 270 ภาพ แล้วล็อกวิธีและยืนยันบน 90 ภาพใหม่\n\n## ความแม่นยำ\nLISA positive IoU 73.065% ส่วน router 66.939% ลดลง 6.13 จุด การปฏิเสธกรณีไม่มีเป้าหมายเพิ่มจาก 0 เป็น 66.67%\n\n## เวลา\nส่วนโมเดลจาก 13.7526 เป็น 13.4961 วินาที ผลลดเวลายังไม่มีหลักฐานชัดเจนทางสถิติ\n\n## ข้อสรุป\nยังไม่บรรลุความแม่นยำและความเร็วที่ดีขึ้นพร้อมกัน อ่านระเบียบวิธีและข้อจำกัดฉบับเต็มใน English\n'
}
for slug, stem, en, th in reports:
    english = (ROOT/'docs'/f'{stem}.md').read_text(encoding='utf-8')
    tp = ROOT/'docs'/f'{stem}.th.md'
    translated = tp.read_text(encoding='utf-8') if tp.exists() else thai[slug]
    for language, text in [('source', english), ('en', english), ('th', translated)]:
        (OUT/'documents'/f'{slug}.{language}.md').write_text(text, encoding='utf-8')
        if language != 'source':
            html = re.sub(r'^<h1>.*?</h1>\s*', '', md.render(text), count=1, flags=re.S)
            # Reports contain workstation artifact links. Keep their labels, without broken public URLs.
            html = re.sub(r'<a href="(?!https?://|#)[^"]*">(.*?)</a>', r'\1', html, flags=re.S)
            (OUT/'documents'/f'{slug}.{language}.html').write_text(html, encoding='utf-8')
    catalog.append(dict(id=slug, progress=3, date='2026-09-15', title=dict(en=en, th=th), description=dict(en='Completed experiment · measured results and limitations', th='การทดลองที่เสร็จแล้ว · ผลวัดจริงและข้อจำกัด')))
(OUT/'documents/index.json').write_text(json.dumps(catalog, ensure_ascii=False, indent=2), encoding='utf-8')
evidence = OUT/'latest-evidence'
evidence.mkdir(exist_ok=True)
for p in (ROOT/'code/results/cohd_cctv_20260915/examples').glob('*.png'):
    shutil.copy2(p, evidence/p.name)
for name in ['runtime.json', 'size_diagnostic.json', 'data_audit.json', 'execution_audit.json', 'metric_checks.json']:
    shutil.copy2(ROOT/'code/results/cohd_cctv_20260915'/name, evidence/name)
# Archive depended on Flask APIs; its static counterpart points to preserved historical galleries.
(OUT/'progress-2-legacy.html').write_text('<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Historical evidence · tart.project1</title><h1>Historical evidence / หลักฐานย้อนหลัง</h1><p>The API-backed archive remains available in the local research viewer. This published static edition provides saved evidence below.</p><p>ฉบับออนไลน์แสดงผลที่บันทึกไว้ ไม่มีการรันโมเดล</p><a href="index.html#progress2">Progress 2: saved images, masks and results / ผล ภาพ และมาสก์</a>', encoding='utf-8')
index = (OUT/'index.html').read_text(encoding='utf-8').replace('Research progress · KMITL CE69-27', 'tart.project1 · KMITL research').replace('KMITL / CE69-27<small', 'tart.project1<small')
index = index.replace('</body>', '<script src="portal-latest.js"></script></body>')
(OUT/'index.html').write_text(index, encoding='utf-8')
routes = (OUT/'portal-routes.js').read_text(encoding='utf-8').replace("+' · KMITL CE69-27'", "+' · tart.project1'")
(OUT/'portal-routes.js').write_text(routes, encoding='utf-8')
(OUT/'portal-latest.js').write_text('''/* Presentation of previously measured results; no inference. */
const priorOverview=overview, priorProgress3=progress3;
function latestPanel(){return `<section class="panel"><p class="eyebrow">15 SEP 2026 · ${t('LATEST COMPLETED WORK','ผลล่าสุดที่เสร็จแล้ว')}</p><h2>${t('CoHD is fast. Small, distant people remain the main failure.','CoHD เร็ว แต่ยังพลาดคนตัวเล็กและคนไกล')}</h2><p>${t('Custom A/B did not reduce CCTV false negatives. The released model remains the default. Sliding-window inference has not yet been tested for CoHD.','Custom A/B ยังลดคนที่ตรวจไม่พบใน CCTV ไม่ได้ จึงคงโมเดลเดิมเป็นค่าเริ่มต้น ยังไม่ได้ทดสอบ sliding window กับ CoHD')}</p><ol><li>${t('Established baselines and tested prompt, refinement and routing methods. Joint accuracy and runtime gains remain unproven.','สร้าง baseline และทดสอบพรอมป์ต์ การปรับมาสก์ และ router ยังไม่ยืนยันผลดีขึ้นทั้งความแม่นยำและเวลา')}</li><li>${t('Compared released checkpoints: CoHD 78.01% positive IoU and 0.637 s/model stage on 90 reused images; accuracy superiority is not statistically established.','เปรียบเทียบ checkpoint: CoHD positive IoU 78.01% และ 0.637 วินาทีต่อส่วนโมเดล บน 90 ภาพที่นำมาใช้ซ้ำ ยังไม่ยืนยันว่าความแม่นยำเหนือกว่าทางสถิติ')}</li><li>${t('Trained Custom A/B and tested 120 CCTV frames from two viewpoints. MOTS coverage recall: original 61.23%, custom 60.66%; VIRAT box-adapter recall: both 1.74%.','ฝึก Custom A/B และทดสอบ CCTV 120 เฟรมจาก 2 มุมกล้อง MOTS coverage recall: เดิม 61.23% custom 60.66%; VIRAT recall จากการแปลงมาสก์เป็นกล่องเท่ากัน 1.74%')}</li></ol><p>${t('CCTV runtime ≈0.647 s/image (resident model). Coverage recall is not instance AP; the box adapter is not a native detector. Only “all people” was tested, in daytime scenes.','CCTV ใช้เวลาประมาณ 0.647 วินาทีต่อภาพเมื่อโหลดโมเดลแล้ว coverage recall ไม่ใช่ instance AP และการแปลงมาสก์เป็นกล่องไม่ใช่ detector โดยตรง ทดสอบเฉพาะ “all people” ในฉากกลางวัน')}</p><div class="doclinks"><a class="btn" href="#doc/cctv">${t('CCTV results','ผล CCTV')}</a><a class="btn secondary" href="#doc/checkpoints">${t('Checkpoint comparison','เปรียบเทียบ checkpoint')}</a><a class="btn secondary" href="#doc/verifier">${t('Verifier test','ผล verifier')}</a><a class="btn secondary" href="#doc/runtime">LISA runtime</a><a class="btn secondary" href="#doc/router">Router</a></div><details><summary>${t('Saved CCTV comparisons and audits','ภาพเปรียบเทียบ CCTV และผลตรวจสอบ')}</summary><p>${t('Columns: ground truth / original / Custom A / Custom B. Fixed 25/50/75% frame selections; zoom illustrates small-person failures.','คอลัมน์: ground truth / เดิม / Custom A / Custom B เลือกเฟรมตำแหน่ง 25/50/75% คงที่ ภาพขยายแสดงจุดที่พลาดคนตัวเล็ก')}</p>''' + ''.join(f'<a href="latest-evidence/{p.name}" target="_blank" rel="noopener"><img src="latest-evidence/{p.name}" loading="lazy" style="max-width:100%;height:auto" alt="CCTV comparison {p.stem}"></a>' for p in sorted(evidence.glob('*.png'))) + '''<p><a href="latest-evidence/runtime.json">Runtime JSON</a> · <a href="latest-evidence/size_diagnostic.json">Size diagnostic JSON</a> · <a href="latest-evidence/data_audit.json">Data audit JSON</a></p></details></section>`}
overview=function(){priorOverview();const old=root.querySelector('.panel');if(old)old.remove();root.querySelector('.heading').insertAdjacentHTML('afterend',latestPanel());};
progress3=function(){priorProgress3();root.insertAdjacentHTML('afterbegin',latestPanel());};
render();
''', encoding='utf-8')
print(f'Exported tart.project1: {len(catalog)} bilingual report entries; saved evidence only.')
