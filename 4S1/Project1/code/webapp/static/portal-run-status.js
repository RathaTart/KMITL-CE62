/* Progress counters only. Experiment scores remain hidden until evaluation completes. */
async function showExtendedRunStatus() {
  const route=location.hash.slice(1)||'home';
  if(!['home','progress3'].includes(route)||DATA?.extended){document.getElementById('extended-run-status')?.remove();return;}
  try {
    const response=await fetch('extended-status.json',{cache:'no-store'});if(!response.ok)return;
    const status=await response.json();
    if(!['home','progress3'].includes(location.hash.slice(1)||'home'))return;
    let panel=document.getElementById('extended-run-status');
    if(!panel){panel=document.createElement('section');panel.id='extended-run-status';panel.className='notice';root.querySelector('.heading')?.after(panel);}
    const counts=status.counts||{};
    panel.innerHTML=`<strong>${t('New 180-image experiment','การทดลองใหม่ 180 ภาพ')}</strong><p>${status.state==='complete'?t('Results are ready. Reload to view the completed comparison.','ผลพร้อมแล้ว โหลดหน้าใหม่เพื่อดูการเปรียบเทียบที่เสร็จสมบูรณ์'):status.state==='attention'?t('The run needs inspection. Historical results remain available.','คิวต้องได้รับการตรวจสอบ ผลทดลองเดิมยังเปิดได้ตามปกติ'):t('Remote processing is in progress. These are completion counts, not scores.','กำลังประมวลผลบนเครื่องระยะไกล ตัวเลขนี้คือจำนวนที่ทำเสร็จ ไม่ใช่คะแนน')}</p>${status.state==='running'?`<p>LISA ${Number(counts.LISA||0)}/180 · Qwen LISA ${Number(counts.Qwen_LISA||0)}/180 · Qwen presence ${Number(counts.Qwen_presence||0)}/180</p>`:''}${status.state==='complete'?`<button class="btn" id="reload-extended">${t('Load results','โหลดผลทดลอง')}</button>`:''}<small>${t('Last checked','ตรวจล่าสุด')}: ${esc(status.updated_utc||'')}</small>`;
    document.getElementById('reload-extended')?.addEventListener('click',()=>location.reload());
  }catch{}
}
showExtendedRunStatus();setInterval(showExtendedRunStatus,15000);window.addEventListener('hashchange',showExtendedRunStatus);
