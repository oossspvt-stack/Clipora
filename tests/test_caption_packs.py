"""Exercise imported timing, ASS rendering and end-to-end video export."""
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from studio import caption_packs, caption_presets, render, config


class CaptionPacksTest(unittest.TestCase):
    def test_catalog_is_selectable_without_replacing_originals(self):
        self.assertEqual(len(caption_packs.PRESETS), 120)
        self.assertTrue({'bounce','hype','clean'} <= render.STYLES.keys())
        self.assertTrue(caption_packs.PRESETS.keys() <= render.STYLES.keys())
        self.assertEqual({p:sum(s['pack']==p for s in caption_packs.PRESETS.values()) for p in caption_packs.PACKS},
                         {'Premium':6,'Normal':98,'Minimal':1,'Multiline':15})

    def test_words_crossing_trim_boundaries_are_kept_and_clamped(self):
        words=[{'w':'before','s':0,'e':1},{'w':'crossing','s':9.8,'e':10.4},
               {'w':'ending','s':10.8,'e':12},{'w':'after','s':12,'e':13}]
        actual=caption_packs.relative_words(words,10,11)
        self.assertEqual([w['word'] for w in actual],['crossing','ending'])
        self.assertEqual(actual[0]['start'],0)
        self.assertEqual(actual[-1]['end'],1)

    def test_all_ass_styles_keep_caption_and_hook_events(self):
        words=[{'w':'Make','s':10,'e':10.4},{'w':'moments','s':10.4,'e':11}]
        for key, style in caption_packs.PRESETS.items():
            if style['engine']!='ass':continue
            with self.subTest(style=key):
                ass=render.build_ass(words,10,12,'A hook',key,[],300,1380)
                self.assertIn('Style: Hook,',ass)
                self.assertIn('Dialogue:',ass)
                self.assertIn('MOMENTS' if style['uppercase'] else 'moments',ass)
                self.assertNotIn('0:00:10.',ass)

    @unittest.skipUnless(shutil.which('ffmpeg') and shutil.which('node'),'ffmpeg and Node.js required')
    def test_representative_exports_have_audio_and_video(self):
        with tempfile.TemporaryDirectory(prefix='clipora-pack-test-') as folder:
            root=Path(folder); src=root/'source.mp4'
            subprocess.run(['ffmpeg','-v','error','-y','-f','lavfi','-i','color=c=gray:s=360x640:r=30:d=1.4',
                '-f','lavfi','-i','sine=frequency=440:duration=1.4','-c:v','libx264','-pix_fmt','yuv420p','-c:a','aac',str(src)],check=True)
            config.FONTS_DIR=root/'fonts';config.FONTS_DIR.mkdir();render.install_fonts()
            words=[{'w':'Make','s':.1,'e':.4},{'w':'every','s':.4,'e':.8},{'w':'moment','s':.8,'e':1.2}]
            keys=['bounce']+[next(k for k,s in caption_packs.PRESETS.items() if s['pack']==p) for p in caption_packs.PACKS]
            render._qsv_ok=False
            for index,key in enumerate(keys):
                with self.subTest(style=key):
                    result=render.render_clip(src,root,f'pack{index}',{'start':0,'end':1.3,'style':key,'hook':'A hook','layout':'crop'},words,360,640)
                    probe=subprocess.run(['ffprobe','-v','error','-show_entries','stream=codec_type','-of','csv=p=0',str(root/result['file'])],capture_output=True,text=True,check=True).stdout
                    self.assertIn('video',probe);self.assertIn('audio',probe)
                    self.assertGreater((root/result['file']).stat().st_size,1000)

if __name__=='__main__':unittest.main()
