import { readdir, readFile, copyFile, mkdir, rm } from 'node:fs/promises';
import { join, basename, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = join(__dirname, '..', '..');
const SITE = join(__dirname, '..');

const capabilityRegistry = JSON.parse(
  await readFile(join(ROOT, 'spec', 'capabilities.json'), 'utf-8'),
);
const CHART_TYPES = capabilityRegistry.chartTypes
  .filter((chart) => chart.tier === 'certified')
  .map((chart) => (chart.id === 'line' ? 'line-basic' : chart.id));

if (CHART_TYPES.length !== 36 || new Set(CHART_TYPES).size !== CHART_TYPES.length) {
  throw new Error(`Expected 36 unique certified chart directories, found ${CHART_TYPES.length}`);
}

async function ensureDir(dir) {
  await mkdir(dir, { recursive: true });
}

async function resetGeneratedDirectory(dir) {
  await rm(dir, { recursive: true, force: true });
  await ensureDir(dir);
}

async function syncGoldenSvgs() {
  const destRoot = join(SITE, 'src', 'assets', 'charts');
  await resetGeneratedDirectory(destRoot);
  for (const type of CHART_TYPES) {
    const srcDir = join(ROOT, 'charts', type, 'golden');
    const destDir = join(destRoot, type);
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
  const destRoot = join(SITE, 'src', 'assets', 'specs');
  await resetGeneratedDirectory(destRoot);
  for (const type of CHART_TYPES) {
    const srcDir = join(ROOT, 'charts', type, 'examples');
    const destDir = join(destRoot, type);
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
