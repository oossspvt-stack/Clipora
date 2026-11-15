import fs from 'node:fs';
import path from 'node:path';
import {createCanvas, GlobalFonts} from '../web/captions/node_modules/@napi-rs/canvas/index.js';
import {createCaptionRenderer} from '../web/captions/adapter.mjs';
const root=path.resolve(import.meta.dirname,'..');
for(const font of fs.readdirSync(root+'/web/caption-fonts'))if(font.endsWith('.ttf'))GlobalFonts.registerFromPath(root+'/web/caption-fonts/'+font);
globalThis.document={createElement:()=>createCanvas(1,1),fonts:{load:async()=>[],ready:Promise.resolve()}};
const catalog=JSON.parse(fs.readFileSync(root+'/web/captions/catalog.json'));
const words=['Make','every','moment','worth','watching'].map((word,i)=>({word,start:i*.4,end:(i+1)*.4}));
let passed=0;
for(const style of catalog){
 const canvas=createCanvas(360,640),renderer=await createCaptionRenderer(canvas,{style:style.id,words,duration:2.5});
 let visible=false;
 for(const t of [.2,.7,1.2,1.8]){
  await renderer.draw(t);
  const pixels=canvas.getContext('2d').getImageData(0,0,360,640).data;
  for(let i=3;i<pixels.length;i+=4)if(pixels[i]){visible=true;break;}
 }
 if(!visible)throw Error('Caption style rendered no visible pixels: '+style.id);
 passed++;
}
console.log(`PASS: ${passed} Canvas styles produced visible frames.`);
