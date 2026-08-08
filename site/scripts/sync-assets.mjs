import { readdir, readFile, copyFile, mkdir, cp } from 'node:fs/promises';
import { join, basename, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = join(__dirname, '..', '..');
const SITE = join(__dirname, '..');

const CHART_TYPES = ['line-basic', 'column', 'area', 'bar', 'scatter', 'bubble', 'combo'];

async function ensureDir(dir) {
  await mkdir(dir, { recursive: true });
}

async function syncGoldenSvgs() {
  for (const type of CHART_TYPES) {
    const srcDir = join(ROOT, 'charts', type, 'golden');
    const destDir = join(SITE, 'src', 'assets', 'charts', type);
    await ensureDir(destDir);
    const files = await readdir(srcDir);
    for (const f of files) {
      if (f.endsWith('.svg')) {
        await copyFile(join(srcDir, f), join(destDir, f));
      }
    }
  }
  console.log('  synced golden SVGs');
}

async function syncExampleSpecs() {
  for (const type of CHART_TYPES) {
    const srcDir = join(ROOT, 'charts', type, 'examples');
    const destDir = join(SITE, 'src', 'assets', 'specs', type);
    await ensureDir(destDir);
    const files = await readdir(srcDir);
    for (const f of files) {
      if (f.endsWith('.json')) {
        await copyFile(join(srcDir, f), join(destDir, f));
      }
    }
  }
  console.log('  synced example specs');
}

async function syncRuntime() {
  const dest = join(SITE, 'public', 'chart-interactions.js');
  await copyFile(join(ROOT, 'runtime', 'chart-interactions.js'), dest);
  console.log('  synced chart-interactions.js');
}

async function syncEvidence() {
  const srcDir = join(ROOT, 'docs', 'quality', 'stoneverify-sample-evidence');
  const destDir = join(SITE, 'src', 'assets', 'stoneverify');
  await ensureDir(destDir);
  for (const f of ['report.html', 'manifest.json', 'python-output.svg', 'go-output.svg']) {
    await copyFile(join(srcDir, f), join(destDir, f));
  }
  console.log('  synced StoneVerify evidence');
}

async function syncPreviewChart() {
  await copyFile(
    join(ROOT, 'charts', 'line-basic', 'golden', 'basic.svg'),
    join(SITE, 'public', 'preview-chart.svg'),
  );
  console.log('  synced preview chart');
}

console.log('sync-assets: copying from stonecharts project...');
await Promise.all([
  syncGoldenSvgs(),
  syncExampleSpecs(),
  syncRuntime(),
  syncEvidence(),
  syncPreviewChart(),
]);
console.log('sync-assets: done.');
