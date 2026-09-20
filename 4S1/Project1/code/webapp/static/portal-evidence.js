/* Presentation only: real saved images and mask overlays, no model execution. */
let maskDisplay = localStorage.getItem('research-mask-display') || 'overlay';
function testedImages() {
  if (typeof DATA === 'undefined' || !DATA) return;
  const route = location.hash.slice(1) || 'home';
  if (!['home', 'progress2', 'progress3'].includes(route) || root.querySelector('.tested-images')) return;
  const latest = DATA.extended ? [DATA.extended.items[0], 'experiment/extended', t('Training-free · 180 new images · 15 Sep','ไม่ฝึกน้ำหนัก · ภาพใหม่ 180 ภาพ · 15 ก.ย.')] : [DATA.training.items[0], 'experiment/training', t('Training-free · new testA subset','ไม่ฝึกน้ำหนัก · testA ชุดใหม่')];
  const samples = route === 'progress3' ? [
    [DATA.attribute[0].items[0], 'experiment/attribute', t('Attribute selection · development','เลือกตามคุณลักษณะ · ชุดพัฒนา')],
    [DATA.upgrade[0].items[0], 'experiment/upgrade', t('Learned boundary gate · reserved set','ชั้นปรับขอบที่เรียนรู้ · ชุดกันไว้')],
    latest
  ] : [
    [DATA.progress2.camouflage.items[0], 'history/camouflage', t('Progress 2 · Camouflage','Progress 2 · ภาพพรางตัว')],
    [DATA.progress2.mots.items[0], 'history/mots', t('Progress 2 · Small pedestrians','Progress 2 · คนเดินถนนขนาดเล็ก')],
    ...(route === 'progress2' ? [[DATA.progress2.pilot.items[0], 'history/pilot', t('Progress 2 · Person descriptions','Progress 2 · คำอธิบายบุคคล')]] : [latest])
  ];
  const section=document.createElement('section');section.className='tested-images';
  section.innerHTML=`<div class="row"><h2>${t('Images from the experiments','ภาพที่ใช้ในการทดลอง')}</h2><span class="muted">${t('Open an image to compare predictions','เปิดภาพเพื่อเปรียบเทียบผลทำนาย')}</span></div><div class="sample-grid">${samples.map(([item,route,label])=>`<a class="sample-card" href="#${route}"><img src="${esc(item.image)}" alt="${esc(label)}"><div><span class="sample-label">${label}</span><p lang="en">“${esc(item.expression)}”</p><span class="sample-action">${t('View image, masks & details','ดูภาพ มาสก์ และรายละเอียด')} →</span></div></a>`).join('')}</div>`;
  root.querySelector('.heading')?.after(section);
}
function loadEvidenceImage(src) {
  return new Promise((resolve,reject)=>{const image=new Image();image.onload=()=>resolve(image);image.onerror=reject;image.src=src});
}
async function addMaskOverlay(figure,source,mask,index) {
  if(figure.dataset.overlayPrepared)return;
  figure.dataset.overlayPrepared='true';
  const canvas=document.createElement('canvas');
  if(typeof canvas.getContext!=='function')return;
  try {
    const [image,binary]=await Promise.all([loadEvidenceImage(source),loadEvidenceImage(mask.src)]);
    if(!figure.isConnected)return;
    canvas.width=image.naturalWidth;canvas.height=image.naturalHeight;
    const ctx=canvas.getContext('2d');if(!ctx)return;
    ctx.drawImage(binary,0,0,canvas.width,canvas.height);
    const layer=ctx.getImageData(0,0,canvas.width,canvas.height);
    const color=index===1?[16,185,129]:[255,103,55];
    for(let i=0;i<layer.data.length;i+=4){const inside=layer.data[i]>127;layer.data[i]=color[0];layer.data[i+1]=color[1];layer.data[i+2]=color[2];layer.data[i+3]=inside?130:0;}
    const buffer=document.createElement('canvas');buffer.width=canvas.width;buffer.height=canvas.height;
    buffer.getContext('2d').putImageData(layer,0,0);
    ctx.clearRect(0,0,canvas.width,canvas.height);ctx.drawImage(image,0,0);ctx.drawImage(buffer,0,0);
    canvas.className='mask-overlay';canvas.setAttribute('role','img');canvas.setAttribute('aria-label',mask.alt+' · '+t('overlay on original image','ซ้อนบนภาพต้นฉบับ'));
    mask.after(canvas);updateMaskDisplay();
  }catch{figure.dataset.overlayPrepared='failed';}
}
function updateMaskDisplay(){
  root.querySelectorAll('.views figure').forEach((figure,index)=>{
    const overlay=figure.querySelector('canvas.mask-overlay');if(!overlay)return;
    const image=figure.querySelector('img');image.hidden=maskDisplay==='overlay';overlay.hidden=maskDisplay!=='overlay';
  });
  root.querySelectorAll('[data-mask-mode]').forEach(button=>button.setAttribute('aria-pressed',String(button.dataset.maskMode===maskDisplay)));
}
function decorateMaskViews(){
  const views=root.querySelector('.views');if(!views)return;
  if(!root.querySelector('.mask-toolbar')){
    const toolbar=document.createElement('div');toolbar.className='mask-toolbar';
    toolbar.innerHTML=`<div><strong>${t('Compare on the original image','เปรียบเทียบบนภาพต้นฉบับ')}</strong><p><span class="legend-dot ground"></span>${t('Ground truth','คำตอบอ้างอิง')} <span class="legend-dot prediction"></span>${t('Model prediction','ผลทำนายโมเดล')}</p></div><div class="mask-buttons" role="group" aria-label="${t('Mask display','การแสดงมาสก์')}"><button data-mask-mode="overlay">${t('Overlay','ซ้อนบนภาพ')}</button><button data-mask-mode="binary">${t('Binary masks','มาสก์ขาวดำ')}</button></div>`;
    views.before(toolbar);toolbar.querySelectorAll('[data-mask-mode]').forEach(button=>button.onclick=()=>{maskDisplay=button.dataset.maskMode;localStorage.setItem('research-mask-display',maskDisplay);updateMaskDisplay()});
  }
  const figures=[...views.querySelectorAll('figure')],source=figures[0]?.querySelector('img')?.src;if(!source)return;
  figures.slice(1).forEach((figure,i)=>{const mask=figure.querySelector('img');if(mask)addMaskOverlay(figure,source,mask,i+1)});
  updateMaskDisplay();
}
testedImages();decorateMaskViews();
