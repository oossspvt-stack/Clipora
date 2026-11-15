import { createCaptionRenderer } from './adapter.mjs';

const presets = new Map((await (await fetch(new URL('./packs.json', import.meta.url))).json()).map(p=>[p.id,p]));
const words = ['Make','every','moment','worth','watching'].map((word,i)=>({word,start:i*.55,end:(i+1)*.55}));
const active = new Map();
let tick = 0;

async function mount(canvas) {
  const id = canvas.dataset.captionStyle;
  if (active.get(canvas)?.id === id) return;
  const preset = presets.get(id), entry = {id,started:performance.now(),renderer:null};
  active.set(canvas, entry);
  const note=canvas.closest('.caption-browser')?.querySelector('.caption-preview-note');
  if(note)note.textContent=preset?.engine==='canvas'?'Animated style preview':'Style preview';
  if (preset?.engine === 'canvas') {
    entry.renderer = await createCaptionRenderer(canvas, {style:id,words,duration:3.5});
  } else {
    const ctx=canvas.getContext('2d');
    const font=preset?.font_family || (id==='hype'?'Anton':'Poppins');
    await document.fonts.load(`90px "${font}"`);
    const caption=canvas.closest('.caption-browser')?.querySelector('.caption-preview-note');
    if(caption)caption.textContent=preset?.engine==='ass'?'Style preview · word timing is applied during export':'Style preview';
    entry.draw = t => {
      ctx.clearRect(0,0,canvas.width,canvas.height);
      const upper=preset?.uppercase ?? id!=='clean';
      ctx.font=`${preset?.bold === false ? 400 : 800} ${preset?.font_size || 100}px "${font}"`;
      ctx.textAlign='center';ctx.textBaseline='middle';ctx.lineJoin='round';
      const text=upper?'MAKE EVERY MOMENT':'Make every moment';
      const y=canvas.height*(preset?.position==='center'?.5:.8);
      if(preset?.background_enabled){ctx.fillStyle=preset.background_color;ctx.fillRect(80,y-75,canvas.width-160,150);}
      ctx.strokeStyle=preset?.outline_color || '#000';ctx.lineWidth=(preset?.outline || 4)*2;
      ctx.strokeText(text,canvas.width/2,y,canvas.width-100);
      ctx.fillStyle=preset?.primary_color || '#fff';ctx.fillText(text,canvas.width/2,y,canvas.width-100);
    };
  }
}
function scan(){document.querySelectorAll('canvas[data-caption-style]').forEach(c=>mount(c).catch(()=>{
  const note=c.closest('.caption-browser')?.querySelector('.caption-preview-note');
  if(note)note.textContent='Preview unavailable. The style remains selectable for export.';
}));}
function animate(now){
  for(const [canvas,e] of active){
    if(!canvas.isConnected){active.delete(canvas);continue;}
    if(!canvas.getClientRects().length)continue;
    const t=((now-e.started)/1000)%3.5;
    if(e.renderer)e.renderer.draw(t).catch(()=>{});else e.draw?.(t);
  }
  tick=requestAnimationFrame(animate);
}
new MutationObserver(scan).observe(document.body,{childList:true,subtree:true});
document.addEventListener('change',e=>{
  if(e.target.id!=='o_style')return;
  const canvas=e.target.closest('.caption-browser')?.querySelector('canvas');
  if(canvas){canvas.dataset.captionStyle=e.target.value;scan();}
});
scan();tick=requestAnimationFrame(animate);
window.addEventListener('pagehide',()=>cancelAnimationFrame(tick),{once:true});
