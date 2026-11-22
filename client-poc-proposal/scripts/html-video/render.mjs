// video.html を1コマずつ描いて MP4 にする（1920x1080・30fps）。
//   node render.mjs                           → out/video.mp4（音なし版）
//   node render.mjs --stills [--times 3,10]   → out/stills/ に確認用の静止画（既定の秒は video.html の STILLS）
//   node render.mjs --timing out/timing.json --out out/video-voice-video.mp4 --credit "..."
//       → ナレーションに合わせた版。声が長い場面は、表示し終えた所（hold）で止めて待つ（アニメの速さは変えない）
//   --html <ファイル> で別のHTMLを描く。出力先は、そのHTMLと同じフォルダの out/。
//   Chrome の場所は環境変数 CHROME_PATH で変えられる（既定は /Applications/Google Chrome.app）。
import { chromium } from "playwright-core";
import { spawn } from "node:child_process";
import { mkdirSync, readFileSync } from "node:fs";
import { fileURLToPath, pathToFileURL } from "node:url";
import path from "node:path";

const here = path.dirname(fileURLToPath(import.meta.url));
const FPS = 30;
const arg = (name) => { const i = process.argv.indexOf(name); return i >= 0 ? process.argv[i + 1] : undefined; };
const stills = process.argv.includes("--stills");
const timingPath = arg("--timing");
const credit = arg("--credit") || "";
const htmlPath = path.resolve(arg("--html") || path.join(here, "video.html"));
const outDir = path.join(path.dirname(htmlPath), "out");
mkdirSync(path.join(outDir, "stills"), { recursive: true });

// 出力の時刻 T → 元の台本の時刻 t（声に合わせて、hold の所で止めている時間を差し引く）
function makeWarp(timing) {
  const segs = timing.segments;
  return (T) => {
    if (T < segs[0].newStart) return T;
    let s = segs[0];
    for (const x of segs) if (T >= x.newStart) s = x;
    const local = T - s.newStart;
    const L = s.next - s.at, extra = s.newLen - L, h = s.hold - s.at;
    if (local < h) return s.at + local;
    if (local < h + extra) return s.hold;
    return s.hold + (local - h - extra);
  };
}

const browser = await chromium.launch({
  executablePath: process.env.CHROME_PATH || "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
  headless: true,
});
const page = await browser.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 1 });
const url = pathToFileURL(htmlPath);
if (credit) url.searchParams.set("credit", credit);
await page.goto(url.href);
await page.evaluate(async () => {
  await document.fonts.ready;
  await Promise.all([...document.images].map((img) => img.decode().catch(() => {})));
});

let duration = await page.evaluate(() => window.DURATION);
let warp = (T) => T;
if (timingPath) {
  const timing = JSON.parse(readFileSync(timingPath, "utf8"));
  warp = makeWarp(timing);
  duration = timing.total;
}

if (stills) {
  const given = arg("--times");
  const preset = await page.evaluate(() => window.STILLS || null);
  const times = given
    ? given.split(",").map(Number)
    : preset || Array.from({ length: Math.floor(duration / 4) }, (_, i) => (i + 1) * 4);
  for (const T of times) {
    await page.evaluate(([t, T]) => window.renderAt(t, T), [warp(T), T]);
    await page.screenshot({ path: path.join(outDir, "stills", `t${T.toFixed(1).padStart(5, "0")}.png`) });
  }
  console.log(`stills: ${times.length} → ${path.join(outDir, "stills")}`);
} else {
  const out = arg("--out") ? path.resolve(arg("--out")) : path.join(outDir, "video.mp4");
  const ff = spawn("ffmpeg", [
    "-y", "-loglevel", "error", "-f", "image2pipe", "-framerate", String(FPS), "-c:v", "mjpeg", "-i", "-",
    "-vf", "scale=in_range=full:out_range=tv,format=yuv420p",
    "-c:v", "libx264", "-crf", "20", "-preset", "fast", "-tune", "animation", "-movflags", "+faststart", out,
  ], { stdio: ["pipe", "inherit", "inherit"] });
  const total = Math.round(duration * FPS);
  const started = Date.now();
  for (let i = 0; i < total; i++) {
    const T = i / FPS;
    await page.evaluate(([t, T]) => window.renderAt(t, T), [warp(T), T]);
    const buf = await page.screenshot({ type: "jpeg", quality: 92 });
    if (!ff.stdin.write(buf)) await new Promise((r) => ff.stdin.once("drain", r));
    if (i % (FPS * 10) === 0) console.log(`frame ${i}/${total} (${Math.round((Date.now() - started) / 1000)}s)`);
  }
  ff.stdin.end();
  await new Promise((r) => ff.on("close", r));
  console.log(`saved: ${out} (${Math.round((Date.now() - started) / 1000)}s)`);
}
await browser.close();
