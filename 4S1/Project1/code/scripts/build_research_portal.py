"""Build the bilingual static portal from saved evidence. Never runs evaluation.

Run after the existing evidence-page builders. Original research Markdown and
legacy pages are preserved; translated Markdown is authored in static/documents.
Requires markdown-it-py (only for rendering authored Markdown).
"""
import csv
import json
import re
import shutil
from pathlib import Path
from markdown_it import MarkdownIt

CODE = Path(__file__).resolve().parents[1]
ROOT = CODE.parent
STATIC = CODE / 'webapp/static'
DOCS = STATIC / 'documents'
DOCS.mkdir(exist_ok=True)
CATALOG = [
    ('camouflage', 2, '2026-08-24', 'blip2-vs-lisa-experiment.md',
     'Camouflage: BLIP-2 pipeline vs LISA', 'ภาพพรางตัว: BLIP-2 pipeline เทียบ LISA',
     '180 paired requests, prompt conditions, mask accuracy and component compute.', '180 คำขอจับคู่ พรอมป์ต์แต่ละแบบ ความแม่นยำมาสก์ และเวลาส่วนคำนวณ'),
    ('pilot', 2, '2026-08-25', 'grefcoco-mots-pilot-report.md',
     'Language and small-person experiments', 'การทดลองภาษาและบุคคลขนาดเล็ก',
     'The 30-expression pilot, 12-frame MOTS pilot and completed 60-frame study.', 'Pilot ภาษา 30 คำอธิบาย MOTS ระยะแรก 12 เฟรม และผลเต็ม 60 เฟรม'),
    ('attribute', 3, '2026-09-14', 'attribute-research-20260914.md',
     'Detailed person descriptions', 'คำอธิบายบุคคลแบบละเอียด',
     'Prompt repair, direct grounding, crop verification, context selection and controls.', 'แก้พรอมป์ต์ ระบุตำแหน่งตรง ตรวจภาพครอป เลือกจากบริบท และตัวควบคุม'),
    ('upgrade', 3, '2026-09-14', 'model-upgrade-research-20260914.md',
     'Learned boundary gate', 'ชั้นปรับขอบมาสก์แบบเรียนรู้',
     '161 trainable parameters, development ablations and 120 reserved expressions.', '161 พารามิเตอร์ที่ฝึกได้ ablation ชุดพัฒนา และ 120 คำอธิบายที่กันไว้'),
    ('dataset', 3, '2026-09-14', 'dataset-decision-20260914.md',
     'Dataset decision and evaluation policy', 'การเลือกชุดข้อมูลและนโยบายประเมิน',
     'Why gRefCOCO is primary, HumanRef is secondary and test images must be locked.', 'เหตุผลใช้ gRefCOCO เป็นหลัก HumanRef เป็นรอง และการล็อกชุดทดสอบ'),
    ('training', 3, '2026-09-14', 'training-free-study-20260914.md',
     'Training-free study: 60 new images', 'การทดลองไม่ฝึกน้ำหนัก: 60 ภาพใหม่',
     'Frozen selection and refinement, final scores, uncertainty and candidate diagnostics.', 'เลือกและปรับมาสก์ด้วยน้ำหนักคงที่ คะแนนสุดท้าย ความไม่แน่นอน และการวิเคราะห์ผู้สมัคร'),
    ('roadmap', 3, '2026-09-14', 'surveillance-research-roadmap-20260914.md',
     'Fixed-camera CCTV research roadmap', 'แผนวิจัยกล้องวงจรปิดติดตั้งอยู่กับที่',
     'Dataset suitability, architecture options, split audit and the next controlled experiments.', 'ความเหมาะสมของข้อมูล ทางเลือกสถาปัตยกรรม การตรวจ split และการทดลองถัดไป'),
]

if (ROOT/'docs/training-free-extended-20260915.md').exists():
    CATALOG.append(('extended', 3, '2026-09-15', 'training-free-extended-20260915.md',
                    'Custom training-free pipeline: 180 new images', 'pipeline ไม่ฝึกน้ำหนักที่สร้างเอง: 180 ภาพใหม่',
                    'Development sweeps, frozen custom pipeline, held-out comparisons and every saved mask.',
                    'การทดลองชุดพัฒนา สูตร pipeline ที่ล็อกไว้ ผลชุดทดสอบใหม่ และมาสก์ทุกกรณี'))
def read(path):
    return json.loads(path.read_text(encoding='utf-8'))

def asset(path, name):
    """Copy saved evidence byte-for-byte; no resizing or metric calculation."""
    dest = STATIC / 'progress-2-assets' / name
    dest.parent.mkdir(exist_ok=True)
    if not path.is_file():
        raise FileNotFoundError(path)
    shutil.copy2(path, dest)
    return 'progress-2-assets/' + name

def rows(path):
    with path.open(encoding='utf-8') as file:
        return list(csv.DictReader(file))

def build_progress2():
    result = {}
    camo = ROOT / 'dataset/Military Personnel Dataset dataset/CamouflageData'
    p1 = CODE / 'results/camouflage'
    p2 = CODE / 'results/blip2_grounded_sam'
    records1 = {(r['item_id'], r['prompt_id']): r for r in rows(p1 / 'per_image.csv')}
    items = []
    for r in rows(p2 / 'per_image.csv'):
        item, prompt = r['item_id'], r['prompt_id']
        stem = item + '__' + prompt
        prior = records1[item, prompt]
        predictions = {}
        for key, folder, row in [('p1', p1, prior), ('p2', p2, r)]:
            predictions[key] = dict(src=asset(folder/'masks'/f'{stem}.png', f'camo_{stem}_{key}.png'),
                                    iou=float(row['iou']), instruction=row.get('instruction'), answer=row.get('answer'))
        items.append(dict(expression=prior['instruction'], case_type=prompt, item_id=item,
                          image=asset(camo/'img'/f'{item}.jpg', f'camo_{item}.jpg'),
                          gt=asset(camo/'gt'/f'{item}.png', f'camo_{item}_gt.png'), predictions=predictions))
    result['camouflage'] = dict(items=items, summary={key: read(folder/'summary.json')['overall'] for key, folder in [('p1', p1), ('p2', p2)]},
                               downloads=[asset(p1/'summary.json', 'camouflage_p1_summary.json'), asset(p2/'summary.json', 'camouflage_p2_summary.json')])
    for key, folder_name in [('mots', 'mots_small_person_p1_p2'), ('pilot', 'grefcoco_pilot_p1_p2')]:
        folder = CODE / 'results' / folder_name
        summary = read(folder / 'summary.json')
        all_rows = {s: rows(folder/f'{s}_per_image.csv') for s in summary['systems']}
        indices = {s: {(r['item_id'], r['prompt_id']): r for r in rr} for s, rr in all_rows.items()}
        items = []
        for r in all_rows['p1']:
            item, prompt = r['item_id'], r['prompt_id']
            predictions = {}
            for s, index in indices.items():
                row = index[item, prompt]
                predictions[s] = dict(src=asset(folder/row['mask_rel'], f'{key}_{item}_{s}.png'), iou=float(row['iou']),
                                      instruction=row.get('instruction'), answer=row.get('answer'), coverage=row.get('instance_coverage_50'))
            items.append(dict(expression=r['expression'], case_type=r['case_type'], item_id=item,
                              image=asset(folder/r['image_rel'], f'{key}_{item}.jpg'),
                              gt=asset(folder/r['ground_truth_rel'], f'{key}_{item}_gt.png'), predictions=predictions))
        result[key] = dict(items=items, summary={s:v['overall'] for s,v in summary['systems'].items()}, downloads=[asset(folder/'summary.json', f'{key}_summary.json')])
    return result

def main():
    md = MarkdownIt('commonmark', {'html': False}).enable('table')
    catalog = []
    for slug, progress, date, source, en, th, desc_en, desc_th in CATALOG:
        original = (ROOT/'docs'/source).read_text(encoding='utf-8')
        (DOCS/f'{slug}.source.md').write_text(original, encoding='utf-8')
        (DOCS/f'{slug}.en.md').write_text(original, encoding='utf-8')
        for language in ('en', 'th'):
            path = DOCS / f'{slug}.{language}.md'
            text = path.read_text(encoding='utf-8')
            if language == 'th' and not any('\u0e00' <= c <= '\u0e7f' for c in text):
                raise ValueError(f'Missing Thai translation: {path}')
            rendered = md.render(text)
            # The portal supplies one page title; avoid repeating it in the reader.
            rendered = re.sub(r'^<h1>.*?</h1>\s*', '', rendered, count=1, flags=re.S)
            (DOCS/f'{slug}.{language}.html').write_text(rendered, encoding='utf-8')
        catalog.append(dict(id=slug, progress=progress, date=date, title=dict(en=en, th=th), description=dict(en=desc_en, th=desc_th)))
    (DOCS/'index.json').write_text(json.dumps(catalog, ensure_ascii=False, indent=2), encoding='utf-8')
    data = {}
    for key, filename, marker in [('attribute','attribute-research.html','const SETS='),('upgrade','model-upgrade.html','const SETS='),('training','training-free.html','const D=')]:
        path = STATIC / filename
        legacy = path.with_stem(path.stem+'-legacy')
        html = path.read_text(encoding='utf-8')
        if marker in html:
            shutil.copy2(path, legacy)
        else:
            html = legacy.read_text(encoding='utf-8')
        data[key] = json.JSONDecoder().raw_decode(html.split(marker, 1)[1])[0]
        # Preserve readable archival entry points across evidence regeneration.
        if 'legacy-readable.css' not in html:
            head = '<script src="local-viewer-route.js"></script><link rel="stylesheet" href="legacy-readable.css">'
            html = html.replace('<meta charset="utf-8">', '<meta charset="utf-8">'+head, 1)
            html = html.replace('<main>', '<main><a class="archive-return" href="index.html#home">← Research progress / กลับหน้าความก้าวหน้า</a>', 1)
            legacy.write_text(html, encoding='utf-8')
        target = f'index.html#experiment/{key}'
        path.write_text(f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta http-equiv="refresh" content="0;url={target}"><title>Research progress · KMITL</title></head><body><a href="{target}">Open the bilingual research portal / เปิดบันทึกวิจัยสองภาษา</a></body></html>', encoding='utf-8')
    if (STATIC/'extended-assets/data.json').exists():
        data['extended'] = read(STATIC/'extended-assets/data.json')
    data['progress2'] = build_progress2()
    (STATIC/'portal-data.json').write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')
    print(f'Built {len(catalog)} documents in 2 languages; {sum(sum(len(s["items"]) for s in value) if isinstance(value,list) else len(value["items"]) for key,value in data.items() if key!="progress2")} displayed Progress 3 cases; {sum(len(s["items"]) for s in data["progress2"].values())} Progress 2 cases.')

if __name__ == '__main__':
    main()

