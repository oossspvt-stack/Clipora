"""Build a read-only visual preview from the application's existing pages."""
from pathlib import Path
import json
import shutil

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'preview-dist'
BASE = '/Clipora'
OUT.mkdir(exist_ok=True)
shutil.copytree(ROOT/'web/brand', OUT/'brand', dirs_exist_ok=True)
assets=OUT/'assets'; assets.mkdir(exist_ok=True)
for name in ['ascii.js','gradient-ascii.js']:
    shutil.copy2(ROOT/'web'/name,assets/name)

status={'user':{'name':'Preview','email':'','role':'user','is_admin':False,'verified':True},'accounts':False,'styles':{'bounce':'Bounce','hype':'Hype','clean':'Clean'},'layouts':{'blur':'Blurred background','zoom':'Zoom','crop':'Centre crop'},'ai':{'ready':False,'today_calls':0,'today_tokens':0},'links':{'repo':'https://github.com/oossspvt-stack/Clipora','follow':'https://t.me/BMG009'},'tour':False,'unread':0,'no_ffmpeg':False,'disk_full':False,'max_upload_mb':1000,'upload_part_mb':40,'max_batch':5,'connect':{},'youtube':False}
fixture={'/api/status':status,'/api/public':{'accounts':False,'authed':True,'google':False},'/api/sync':{'v':'preview','jobs':[],'creators':[],'accounts':[]},'/api/overview':{'creators':[],'daily':[],'posts':[],'recording':0,'paused':False},'/api/notices':{'items':[],'unread':0},'/api/usage':{'ready':False,'provider':'','model':'','today_calls':0,'today_tokens':0,'daily':[],'models':[],'jobs':[]}}
shim='''<script>
const previewBase='/Clipora';
const previewPath=()=>location.pathname.replace(/^\\/Clipora/,'')||'/';
const previewFixtures=FIXTURES;
const previewFetch=window.fetch.bind(window);
window.fetch=async(input,options={})=>{
 const raw=typeof input==='string'?input:input.url;
 const u=new URL(raw,location.href);
 const p=u.pathname.replace(/^\\/Clipora/,'');
 if(p.startsWith('/api/')){
  const method=(options.method||'GET').toUpperCase();
  if(method!=='GET')return new Response(JSON.stringify({detail:'This is a visual preview. Video processing, account connections and saving require the running application.'}),{status:409,headers:{'Content-Type':'application/json'}});
  return new Response(JSON.stringify(previewFixtures[p]||{}),{headers:{'Content-Type':'application/json'}});
 }
 return previewFetch(input,options);
};
for(const name of ['pushState','replaceState']){
 const original=history[name].bind(history);
 history[name]=(state,title,url)=>original(state,title,typeof url==='string'&&url.startsWith('/')&&!url.startsWith(previewBase)?previewBase+url:url);
}
</script>'''.replace('FIXTURES',json.dumps(fixture).replace('</','<\\/'))
banner='''<div style="position:fixed;bottom:10px;left:50%;transform:translateX(-50%);z-index:99999;max-width:95vw;background:#252525;color:#fff;border:1px solid #e9ff32;border-radius:99px;padding:9px 18px;font:12px/1.5 system-ui;text-align:center">Design preview · Processing disabled · <a style="color:#e9ff32" href="/Clipora/">Landing</a> · <a style="color:#e9ff32" href="/Clipora/app/">Studio</a></div>'''
pages={'':'landing.html','app':'index.html','login':'auth.html','signup':'auth.html','reset':'reset.html','license':'license.html'}
for target,source in pages.items():
    s=(ROOT/'web'/source).read_text(encoding='utf-8')
    if source=='index.html':s=s.replace('location.pathname','previewPath()')
    s=s.replace('src="/','src="'+BASE+'/').replace('poster="/','poster="'+BASE+'/').replace('href="/','href="'+BASE+'/')
    s=s.replace('{{SITE}}','https://oossspvt-stack.github.io/Clipora')
    s=s.replace('</head>',shim+'</head>').replace('</body>',banner+'</body>')
    dest=OUT/target; dest.mkdir(exist_ok=True)
    (dest/'index.html').write_text(s,encoding='utf-8')
(OUT/'.nojekyll').write_text('')
print('Built landing, studio, account and license preview pages from web/.')
