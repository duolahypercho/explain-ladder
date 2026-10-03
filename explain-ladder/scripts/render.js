// Renders WORKDIR/explainer.html (must expose window.ready, window.renderFrame(t), window.DUR) to frames.
//
//   NODE_PATH=~/.cache/explain-ladder/node_modules node render.js WORKDIR stills [3,10.5,22]
//       -> WORKDIR/stills/sNN.jpg + WORKDIR/sheet.jpg (contact sheet to review before the full render)
//   NODE_PATH=~/.cache/explain-ladder/node_modules node render.js WORKDIR video [fps=30]
//       -> WORKDIR/explainer.mp4 (1080p, with audio.wav if present) + explainer_720p.mp4 (sized for X / chat uploads)
const path = require('path'), fs = require('fs'), os = require('os'), { spawn, spawnSync } = require('child_process');
const { chromium } = require('playwright-core');
const [W, mode = 'stills', arg] = process.argv.slice(2);
if (!W) { console.error('usage: render.js WORKDIR stills|video [times|fps]'); process.exit(1); }
const dir = path.resolve(W);

function browserPath() {
  const roots = [path.join(os.homedir(), 'Library/Caches/ms-playwright'), path.join(os.homedir(), '.cache/ms-playwright')];
  const inner = ['chrome-mac-arm64/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing',
    'chrome-mac-x64/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing',
    'chrome-mac/Chromium.app/Contents/MacOS/Chromium', 'chrome-linux64/chrome', 'chrome-linux/chrome'];
  for (const r of roots) {
    if (!fs.existsSync(r)) continue;
    const dirs = fs.readdirSync(r).filter(d => /^chromium-\d+$/.test(d)).sort((a, b) => b.localeCompare(a, undefined, { numeric: true }));
    for (const d of dirs) for (const c of inner) { const p = path.join(r, d, c); if (fs.existsSync(p)) return p; }
  }
  const sys = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
  return fs.existsSync(sys) ? sys : undefined;
}

(async () => {
  const browser = await chromium.launch({ executablePath: browserPath(), args: ['--force-device-scale-factor=1'] });
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
  page.on('pageerror', e => console.log('PAGE ERROR:', e.message));
  await page.goto('file://' + path.join(dir, 'explainer.html') + '?render=1');
  await page.evaluate(() => window.ready);
  const DUR = await page.evaluate(() => window.DUR);
  const grab = async t => Buffer.from((await page.evaluate(t => {
    renderFrame(t); return document.querySelector('canvas').toDataURL('image/jpeg', 0.93);
  }, t)).split(',')[1], 'base64');

  if (mode === 'stills') {
    const ts = (arg || [.08, .2, .32, .44, .56, .68, .8, .95].map(f => (f * DUR).toFixed(1)).join(',')).split(',').map(Number);
    const sd = path.join(dir, 'stills'); fs.rmSync(sd, { recursive: true, force: true }); fs.mkdirSync(sd);
    for (const [i, t] of ts.entries()) fs.writeFileSync(path.join(sd, `s${String(i).padStart(2, '0')}.jpg`), await grab(t));
    const cols = Math.min(4, ts.length);
    spawnSync('ffmpeg', ['-y', '-loglevel', 'error', '-framerate', '1', '-i', path.join(sd, 's%02d.jpg'),
      '-vf', `scale=720:405,tile=${cols}x${Math.ceil(ts.length / cols)}`, '-frames:v', '1', path.join(dir, 'sheet.jpg')]);
    console.log(`stills at ${ts.join(', ')}s -> ${path.join(dir, 'sheet.jpg')}`);
  } else {
    const fps = Number(arg) || 30, n = Math.round(DUR * fps), out = path.join(dir, 'explainer.mp4');
    const audio = path.join(dir, 'audio.wav'), hasAudio = fs.existsSync(audio);
    const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(fps), '-i', '-',
      ...(hasAudio ? ['-i', audio] : []), '-c:v', 'libx264', '-preset', 'medium', '-b:v', '9M', '-maxrate', '14M', '-bufsize', '20M',
      '-pix_fmt', 'yuv420p', ...(hasAudio ? ['-c:a', 'aac', '-b:a', '192k', '-shortest'] : []), '-movflags', '+faststart', out],
      { stdio: ['pipe', 'inherit', 'inherit'] });
    for (let i = 0; i < n; i++) {
      const b = await grab(i / fps);
      if (!ff.stdin.write(b)) await new Promise(r => ff.stdin.once('drain', r));
      if (i % 300 === 0) console.log(`frame ${i}/${n}`);
    }
    ff.stdin.end(); await new Promise(r => ff.on('close', r));
    // share copy: target ~28 MB total
    const vk = Math.min(4000, Math.max(700, Math.floor(28 * 8192 / DUR) - 160));
    spawnSync('ffmpeg', ['-y', '-loglevel', 'error', '-i', out, '-vf', 'scale=1280:720,hqdn3d=2:2:3:3', '-c:v', 'libx264', '-preset', 'slow',
      '-b:v', `${vk}k`, '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '128k', '-movflags', '+faststart', out.replace('.mp4', '_720p.mp4')], { stdio: 'inherit' });
    console.log(`done: ${out} (${DUR.toFixed(1)}s) + explainer_720p.mp4`);
  }
  await browser.close();
})();
