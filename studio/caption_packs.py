"""Clipxy4all caption catalogs and bounded Canvas export."""
import json
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

from . import config
from .media import NO_WINDOW

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / 'web' / 'captions'
PRESETS = {p['id']: p for p in json.loads((ASSETS / 'packs.json').read_text(encoding='utf-8'))}
PACKS = ('Premium', 'Normal', 'Minimal', 'Multiline')


def relative_words(words, start, end):
    """Clip source timings to the exported segment, including words crossing its start."""
    return [{'word': str(w['w']), 'start': max(0, w['s'] - start),
             'end': min(end - start, w['e'] - start)}
            for w in words if w.get('w') and w['e'] > start and w['s'] < end]


def render_layer(work, words, start, end, style, width, height, fps):
    node = shutil.which('node')
    if not node:
        raise RuntimeError('This caption pack needs Node.js 22 or newer. Install it and run npm ci --prefix web/captions.')
    request = work / 'captions.json'
    request.write_text(json.dumps({'style': style, 'words': relative_words(words, start, end),
        'duration': end - start, 'width': width, 'height': height, 'fps': fps,
        'fonts_dir': str((ROOT / 'web/caption-fonts').resolve())}), encoding='utf-8')
    output = work / 'captions.mov'
    processes = []
    try:
        with tempfile.TemporaryFile(dir=work) as node_log, tempfile.TemporaryFile(dir=work) as ffmpeg_log:
            producer = subprocess.Popen([node, '--expose-gc', str(ASSETS / 'driver.mjs'), str(request)],
                stdout=subprocess.PIPE, stderr=node_log, creationflags=NO_WINDOW)
            processes.append(producer)
            encoder = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgba',
                '-video_size', f'{width}x{height}', '-framerate', str(fps), '-i', 'pipe:0',
                '-an', '-c:v', 'qtrle', '-pix_fmt', 'argb', '-threads', '2', str(output)],
                stdin=producer.stdout, stdout=subprocess.DEVNULL, stderr=ffmpeg_log, creationflags=NO_WINDOW)
            processes.append(encoder)
            producer.stdout.close()
            deadline = time.monotonic() + 600
            while producer.poll() is None or encoder.poll() is None:
                if time.monotonic() > deadline:
                    raise RuntimeError('Caption export exceeded ten minutes. Try a shorter clip.')
                if encoder.poll() not in (None, 0):
                    break
                time.sleep(.05)
            for process in processes:
                if process.poll() is None:
                    process.terminate()
                process.wait(timeout=10)
            if any(p.returncode for p in processes) or not output.is_file():
                details = []
                for log in (node_log, ffmpeg_log):
                    log.seek(0, 2); log.seek(max(0, log.tell() - 1500))
                    details.append(log.read().decode('utf-8', 'replace'))
                raise RuntimeError('Caption pack export failed. Run npm ci --prefix web/captions.\n' + '\n'.join(details))
        return output
    finally:
        for process in processes:
            if process.poll() is None:
                process.kill()
            process.wait()
