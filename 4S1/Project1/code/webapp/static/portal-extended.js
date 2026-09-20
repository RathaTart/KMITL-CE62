/* Display only. All scores, intervals and decisions were computed remotely. */
function extendedResultDetails(s) {
  const delta = value => `${value >= 0 ? '+' : ''}${(100 * value).toFixed(2)}`;
  const interval = values => values.map(delta).join(' … ');
  const rows = Object.entries(s.paired).filter(([,row]) => row.status === 'primary');
  return `<h2>${t('How certain is the improvement?','ผลที่ดีขึ้นมีความแน่นอนเพียงใด')}</h2><p class="muted">${t('Differences are percentage points. Adjusted intervals account for six comparisons. Balanced score gives equal weight to positive-mask IoU and correct no-target rejection.','ผลต่างมีหน่วยเป็นจุดเปอร์เซ็นต์ ช่วงความเชื่อมั่นปรับสำหรับการเปรียบเทียบ 6 ครั้ง คะแนนสมดุลให้น้ำหนัก IoU เมื่อมีเป้าหมายและการปฏิเสธเมื่อไม่มีเป้าหมายเท่ากัน')}</p><div class="tablewrap"><table><thead><tr><th>${t('Primary vs','วิธีหลักเทียบกับ')}</th><th>${t('Positive IoU difference','ผลต่าง IoU มีเป้าหมาย')}</th><th>${t('Adjusted interval','ช่วงความเชื่อมั่นที่ปรับแล้ว')}</th><th>${t('Balanced-score difference','ผลต่างคะแนนสมดุล')}</th><th>${t('Adjusted interval','ช่วงความเชื่อมั่นที่ปรับแล้ว')}</th></tr></thead><tbody>${rows.map(([key,r]) => `<tr><th scope="row">${nm(key.split('__vs__')[1])}</th><td>${delta(r.positive_mean_delta)}</td><td>${interval(r.positive_bonferroni_99_167ci)}</td><td>${delta(r.balanced_mean_delta)}</td><td>${interval(r.balanced_bonferroni_99_167ci)}</td></tr>`).join('')}</tbody></table></div><p>${t('The primary pipeline was selected on 90 development images before this 180-image test. Other variants are ablations, not alternative winners chosen after testing.','เลือก pipeline หลักจากภาพพัฒนา 90 ภาพก่อนทดสอบชุดนี้ 180 ภาพ วิธีอื่นใช้ตรวจผลของแต่ละส่วน ไม่ใช่การเปลี่ยนผู้ชนะหลังเห็นคะแนนทดสอบ')}</p><div class="doclinks"><a href="extended-assets/method_lock.json" download>${t('Frozen pipeline','สูตร pipeline ที่ล็อกไว้')} JSON ↓</a><a href="extended-assets/development.json" download>${t('All development configurations','การตั้งค่าที่ทดลองบนชุดพัฒนาทั้งหมด')} JSON ↓</a><a href="extended-assets/candidate_matching_diagnostic.json" download>${t('One-to-one proposal diagnostic','วิเคราะห์กรอบผู้สมัครแบบจับคู่หนึ่งต่อหนึ่ง')} JSON ↓</a></div>`;
}

function extendedDecisionText(prediction) {
  const d=prediction.decisions;if(!d)return '';
  const parts=[];
  if(typeof d.rejected==='boolean')parts.push(d.rejected?t('Verifier: rejected','ตัวตรวจสอบ: ปฏิเสธ'):t('Verifier: retained','ตัวตรวจสอบ: เก็บมาสก์'));
  if(Number.isFinite(d.verification_score))parts.push(t('Yes score','คะแนน yes')+' '+d.verification_score.toFixed(3));
  if(Number.isFinite(prediction.target_total)&&prediction.target_total>0)parts.push(t('Target coverage ≥50%','ครอบคลุมเป้าหมาย ≥50%')+` ${prediction.target_hit}/${prediction.target_total}`);
  if(Number.isFinite(prediction.distractor_total)&&prediction.distractor_total>0)parts.push(t('Distractor coverage ≥50%','ครอบคลุมบุคคลอื่น ≥50%')+` ${prediction.distractor_hit}/${prediction.distractor_total}`);
  return parts.length?' · '+parts.join(' · '):'';
}
