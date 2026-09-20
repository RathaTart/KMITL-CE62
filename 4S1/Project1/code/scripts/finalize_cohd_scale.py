"""Generate decision record and bilingual report from remote scored results."""
import json,platform,hashlib,subprocess
from pathlib import Path
assert platform.node()=='cenara70hx'
O=Path('/home/osta/lisa-eval/code/results/cohd_scale_20260915');C=O.parents[1]
data=json.loads((O/'analysis.json').read_text());lock=json.loads((O/'method_lock.json').read_text());examples=json.loads((O/'examples.json').read_text());names={'original':'Original CoHD','scale704_guard':'Scale 704 + guard','scale768_guard':'Scale 768 + guard'}
conf=data['confirmation'];summary=conf['measured_summary'];base=summary['original'];primary=summary[lock['primary']];bm=base['metrics']['MOTS'];pm=primary['metrics']['MOTS'];bv=base['metrics']['PersonPath22'];pv=primary['metrics']['PersonPath22'];size=conf['methods'];small=lambda k:sum(size[k]['size'][group]['tp'] for group in ['under32','32to63']);smalltotal=sum(size['original']['size'][g]['gt'] for g in ['under32','32to63'])
decision=dict(runtime_pass=primary['runtime_mean']<=base['runtime_mean']*1.05,mots_iou_preserved=pm['positive_iou']>=bm['positive_iou']-.01,mots_fp_controlled=pm['pixel_fp']<=bm['pixel_fp']*1.10,virat_fp_controlled=pv['fp']<=bv['fp']*1.10,mots_small_improved=pm['small_instance_recall50']>bm['small_instance_recall50'],virat_small_improved=small(lock['primary'])>small('original'))
decision['all_primary_cctv_criteria_pass']=all(decision.values());data['decision']=decision
def pct(x):return f'{100*x:.2f}%'
methods=['original']+lock['selected']
table='| Method | MOTS mean IoU | MOTS coverage >=50% | MOTS small coverage | VIRAT matched / GT | VIRAT FP | VIRAT <64px matched / GT | Mean seconds/image |\n|---|---:|---:|---:|---:|---:|---:|---:|\n'
for k in methods:
 r=summary[k];m=r['metrics']['MOTS'];v=r['metrics']['PersonPath22'];table+=f'| {names[k]} | {pct(m["positive_iou"])} | {pct(m["instance_coverage_recall50"])} | {pct(m["small_instance_recall50"])} ({m["small_instances"]} observations) | {v["tp"]} / {v["tp"]+v["fn"]} | {v["fp"]} | {small(k)} / {smalltotal} | {r["runtime_mean"]:.4f} |\n'
langtable='| Method | Hat mask IoU (12 images) | Clothing mask IoU (12 images) | Correct absence (8 images) | Mean seconds/image |\n|---|---:|---:|---:|---:|\n'
for k in methods:
 g=data['language']['methods'][k]['language'];s=data['language']['measured_summary'][k];langtable+=f'| {names[k]} | {pct(g["hat"]["mean_iou"])} | {pct(g["clothing"]["mean_iou"])} | {g["absent"]["empty"]} / {g["absent"]["n"]} | {s["runtime_mean"]:.4f} |\n'
en=f'''# CoHD small-person scale study — 15 September 2026

## What we tested

Continued the original CoHD baseline with no new weight training. The primary **Scale 704 + guard** uses AMP float16, 704-square input, a bilinear adapter to the decoder's learned spatial-projection grid, and a small-component shape guard. A locked 768-resolution variant is secondary. These are experimental inference adaptations, not a newly established architecture or a replacement silently installed as default.

The original model has fixed spatial projection lengths 900/3600/14400. Simply changing image size failed. The adapter resamples the input to those projection MLPs while retaining higher-resolution attention maps elsewhere. Original model/checkpoint files were not edited.

The guard keeps components with >=4096 pixels, or height >=20 original-image pixels and width/height <=1.2. It can remove valid crouching, wide or fragmented people, and these absolute-size rules may not transfer to other cameras. It is not a learned semantic person classifier.

## Development and locked confirmation

Development used 24 explicitly reused CCTV frames (12 MOTS / 12 VIRAT). We tested AMP, several sizes, four overlapping tiles, full image plus top/central crops, and four shape-filter configurations. AMP480 alone reduced runtime but did not recover people; tiles and crops had quality/false-positive trade-offs. Full details remain in the development summaries.

The primary and secondary were locked before confirmation. Confirmation contains 120 previously unscored frames: 60 MOTS20-02 native human-mask frames and 60 PersonPath22/VIRAT courtyard native-box frames. Their cameras are already explored; new frame hashes do not make this an unseen-camera test. Nearby frames and repeated people are correlated.

## CCTV confirmation results

{table}

MOTS coverage counts a person when >=50% of their native mask is covered; it is not one-to-one detector AP. VIRAT uses the pre-existing connected-component mask-to-box adapter and Hungarian IoU>=0.5 matching with ignore handling; it is not official tracking/native detection AP. Small means original-image height <64 pixels. Per-size results under32/32to63/64plus are in analysis.json. Improved recall must still be read alongside its absolute level and false positives.

## Runtime and primary criteria

The mean full-image request includes loading the image, preprocessing, text, all inference passes, coordinate restoration and shape filtering. It excludes one-time model initialization, scoring and visualization. Paired ordering rotates after per-variant warm-up. Every variant uses the same CMP70HX GPU and PyTorch environment; no cached image features.

Primary acceptance checks (true/false): `{json.dumps(decision)}`.

These are pilot acceptance criteria, not statistical proof of generalization. Timing bootstrap intervals describe within-run request variation only. See analysis.json for per-domain metrics and uncertainty. Do not use a faster GPU-only substage as full request latency.

## Hat, clothing and absent-target prompts

{langtable}

**Descriptive-language accuracy did not improve.** The primary hat IoU is 70.74% versus original 71.52%; it covers 7/51 distractor people versus 3/51, while correctly returning empty on 2/8 absent cases versus 3/8. More target coverage came with more incorrect-person coverage. The CCTV acceptance result must not be described as a general language-segmentation upgrade.

This is a 32-image **reused gRefCOCO diagnostic**, selected before predictions: 12 native hat/cap descriptions, 12 clothing descriptions and 8 absent-target descriptions, each on a distinct image with multiple annotated people. Native human expressions and COCO person masks are used. Zero current fine-tuning was performed. This is not fresh held-out language evidence and not a claim about reading a tiny hat in CCTV. Target and distractor coverage are saved separately in analysis.json; a better person mask is not automatically correct attribute binding.

## Evidence, reproducibility and limitations

The 24 original development masks reproduced the historical masks: {data['audit']['original_development_masks_equal']}/24 exact. New confirmation/development hash overlap: {data['audit']['confirmation_hash_overlap_with_dev']}. Language images overlapping official gRefCOCO train: {data['audit']['language_upstream_train_overlap']}; foundation pretraining overlap is not ruled out.

Saved outputs include every mask and per-image score, all per-image request timings, failed direct-resize controls, shape-rule sweeps, locked manifests, source snapshots, and fixed-position comparisons. CCTV examples use 25/50/75% positions per source; language examples use first/middle per group. The cyan zoom uses GT only to show small targets after evaluation; GT never chooses inference crops.

Preserve Original as the default until broader camera and language validation. No additional CCTV attribute labels were invented. Daytime fixed-camera evidence does not establish night, arbitrary-camera or long descriptive-relation performance.

## Run on cenara70hx

```bash
/home/osta/lisa-eval/released-models/.venv/bin/python scripts/infer_cohd_scale.py --image /absolute/image.jpg --text "the person wearing a hat" --method scale704_guard --out /absolute/new_output
```

This command accepts any text but that alone does not guarantee it selects the right person. Use `--method original` for the preserved baseline. Existing output folders are never overwritten.

## Sources

- [CoHD official code](https://github.com/RobertLuo1/CoHD)
- [Slicing Aided Hyper Inference](https://arxiv.org/abs/2202.06934): established motivation for crop inference, not a novelty claim for this work.
- [PyTorch mixed precision](https://docs.pytorch.org/docs/stable/notes/amp_examples.html)
'''
th=f'''# CoHD: ทดลองคนตัวเล็กและเวลาใกล้เดิม — 15 กันยายน 2569

## วิธีใหม่ที่ทดสอบ

**Scale 704 + guard** ใช้ CoHD เดิมโดยไม่ฝึกน้ำหนักเพิ่ม ประมวลผลแบบ AMP float16 เพิ่มภาพเป็น 704×704 และเพิ่มตัวปรับขนาดก่อนส่วน projection ที่โมเดลเดิมล็อกขนาดไว้ ใช้ตัวกรองชิ้นมาสก์เล็กเพื่อลดสิ่งรบกวน มีรุ่น 768 เป็นตัวเปรียบเทียบรองที่ล็อกไว้ก่อนทดสอบ

ตัวกรองเก็บชิ้นมาสก์ที่มีอย่างน้อย 4096 พิกเซล หรือมีความสูงอย่างน้อย 20 พิกเซลและอัตราส่วนกว้าง/สูงไม่เกิน 1.2 กฎนี้อาจลบคนที่นั่ง ก้ม ตัวกว้าง หรือมาสก์ขาดเป็นชิ้น จึงยังไม่ใช่ตัวจำแนกคนที่รับประกันใช้ได้ทุกกล้อง

## ข้อมูลและการเลือกวิธี

พัฒนาบน CCTV เดิม 24 เฟรม ทดลอง AMP ขนาดภาพ การแบ่ง 4 tile ภาพเต็มร่วมครอป และกฎกรองรูปร่าง 4 แบบ จากนั้นล็อกวิธีหลัก/รองก่อนประเมิน **120 เฟรมที่ยังไม่เคยวัดผล** ประกอบด้วย MOTS 60 และ VIRAT 60

เฟรมใหม่ยังมาจากมุมกล้องที่เคยสำรวจแล้วและคนเดิมอาจปรากฏหลายเฟรม จึงเป็นการยืนยันภายในกล้องเดิม ไม่ใช่ผลยืนยันกล้องใหม่โดยอิสระ

## ผล CCTV ที่วัดจริง

{table}

Mean IoU คือความตรงของมาสก์เฉลี่ย Coverage ของ MOTS นับว่าครอบคลุมคนอย่างน้อยครึ่งมาสก์ ส่วน VIRAT แปลงมาสก์เป็นกล่องแล้วจับคู่กับกล่องคนจริงแบบหนึ่งต่อหนึ่ง จึงเป็นคนละตัวชี้วัด ไม่ใช่ AP ของ detector คนตัวเล็กหมายถึงสูงน้อยกว่า 64 พิกเซลในภาพต้นฉบับ ต้องอ่านจำนวนคนที่ยังพลาดและ false positive ประกอบ แม้คะแนนดีขึ้น

## เวลาและเงื่อนไขสำเร็จ

จับเวลาภาพเต็ม รวมอ่านภาพ เตรียมอินพุต ข้อความ ทุก pass คืนพิกัด และกรองมาสก์ ไม่รวมโหลดโมเดลครั้งแรก การคำนวณคะแนน หรือวาดภาพ ทุกรุ่นรัน GPU เดียวกัน สลับลำดับวิธีและ warm-up ก่อนวัด ไม่มีการใช้ cache คุณลักษณะภาพแทน inference

ผลเกณฑ์หลัก (true = ผ่าน): `{json.dumps(decision)}`

นี่เป็นเกณฑ์ของการทดลองนำร่อง ไม่ใช่ข้อพิสูจน์ความเหนือกว่าทั่วไป ค่าเวลาและช่วง bootstrap แบบจับคู่เก็บใน analysis.json

## ทดสอบคำอธิบายหมวกและเสื้อผ้า

{langtable}

**ความแม่นการเลือกตามคำอธิบายยังไม่ดีขึ้น** รุ่นหลักได้ IoU หมวก 70.74% เทียบเดิม 71.52% ครอบคลุมคนอื่นผิด 7/51 เทียบเดิม 3/51 และปฏิเสธเมื่อไม่มีเป้าหมายถูก 2/8 เทียบเดิม 3/8 แม้ครอบคลุมเป้าหมายเพิ่มแต่ก็ครอบคลุมคนอื่นเพิ่ม จึงห้ามนำผลผ่านเกณฑ์ CCTV ไปอ้างว่าเลือกคนตามภาษาเก่งขึ้นทั่วไป

ใช้ภาพ gRefCOCO เดิม 32 ภาพที่มีคำอธิบายและมาสก์คนกำกับโดยมนุษย์: หมวก 12 เสื้อผ้า 12 และไม่มีเป้าหมาย 8 ภาพ เลือกก่อนดูผลโมเดล ไม่ได้สร้างป้ายหมวกขึ้นเองและไม่ได้ใช้ชุดนี้ปรับน้ำหนัก

นี่เป็นการวิเคราะห์ภาษาบนภาพ COCO ที่นำมาใช้ซ้ำ **ยังไม่พิสูจน์ว่าอ่านหมวกของคนไกลใน CCTV ได้** จำนวนเป้าหมายและคนอื่นที่มาสก์ครอบคลุมบันทึกแยกใน analysis.json การตรวจพบคนมากขึ้นไม่เท่ากับเลือกคนตามคุณลักษณะถูกทุกข้อ

## หลักฐานและข้อจำกัด

มาสก์ baseline ชุดพัฒนาเหมือนผลเดิมทุกพิกเซล {data['audit']['original_development_masks_equal']}/24 ภาพ เฟรมยืนยันไม่ซ้ำ hash กับชุดพัฒนา และภาพภาษาไม่ซ้ำ official gRefCOCO train จำนวน {data['audit']['language_upstream_train_overlap']} ภาพ แต่ไม่รับประกันว่าไม่เคยปรากฏใน pretraining อื่น

เก็บผลรายภาพ มาสก์ เวลา manifest ที่ล็อก โค้ด ผลทดลองที่ล้มเหลว และภาพเปรียบเทียบตำแหน่งคงที่ไว้ทั้งหมด กรอบขยายสีฟ้าเลือกจาก GT เฉพาะตอนแสดงหลักฐานหลังประเมิน ไม่ได้ใช้เลือก crop ตอน inference

ยังคง Original เป็นค่าเริ่มต้น ต้องทดสอบกล้องใหม่และภาษาเพิ่มก่อนใช้อ้างผลทั่วไป ไม่อ้างผลกลางคืนหรือการระบุหมวกใน CCTV จากชุดนี้ อ่านรายละเอียดการทำซ้ำและแหล่งอ้างอิงในฉบับอังกฤษ
'''
(O/'cohd-scale-20260915.md').write_text(en);(O/'cohd-scale-20260915.th.md').write_text(th);(O/'analysis.json').write_text(json.dumps(data,indent=2));(O/'web-data.json').write_text(json.dumps(dict(analysis=data,examples=examples,lock=lock),indent=2));print(json.dumps(decision,indent=2))
