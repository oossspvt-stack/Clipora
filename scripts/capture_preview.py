"""Capture the actual Clipora frontend for the visual user guide."""
from pathlib import Path
import shutil, subprocess, sys, time, urllib.request
from playwright.sync_api import sync_playwright

root=Path(__file__).resolve().parents[1]
host=root/'preview-host'
shutil.copytree(root/'preview-dist',host/'Clipora',dirs_exist_ok=True)
out=root/'preview-dist/screenshots'; out.mkdir(exist_ok=True)
server=subprocess.Popen([sys.executable,'-m','http.server','8766','--bind','127.0.0.1','--directory',str(host)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
base='http://127.0.0.1:8766/Clipora/'
try:
 for _ in range(30):
  try: urllib.request.urlopen(base,timeout=1); break
  except Exception: time.sleep(.3)
 with sync_playwright() as p:
  browser=p.chromium.launch()
  page=browser.new_page(viewport={'width':1440,'height':1000},device_scale_factor=1)
  errors=[]
  page.on('pageerror',lambda e:errors.append(str(e)))
  def shot(name):
   page.screenshot(path=str(out/name),full_page=False)
  page.goto(base,wait_until='networkidle')
  page.locator('.hero h1').wait_for()
  shot('01-landing.png')
  page.goto(base+'app/',wait_until='networkidle')
  page.locator('#goBtn').wait_for()
  shot('02-studio.png')
  page.locator('#url').fill('https://www.youtube.com/watch?v=example')
  shot('03-import-video.png')
  opts=page.locator('[data-act="toggleopts"]')
  if opts.count():
   opts.click()
   shot('04-clip-options.png')
  page.locator('#nav [data-v="library"]').click()
  shot('05-all-videos.png')
  page.locator('#nav [data-act="newcreator"]').click()
  page.locator('#formdlg[open]').wait_for()
  shot('06-new-creator.png')
  page.goto(base+'login/',wait_until='networkidle')
  shot('07-account-page.png')
  page.goto(base+'license/',wait_until='networkidle')
  shot('08-license.png')
  browser.close()
  (out/'capture-report.txt').write_text('\n'.join(errors) if errors else 'No browser JavaScript errors during the captured workflow.',encoding='utf-8')
  if errors: raise RuntimeError('\n'.join(errors))
finally:
 server.terminate()
