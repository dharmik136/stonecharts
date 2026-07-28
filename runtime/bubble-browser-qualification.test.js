// Browser qualification for bubble specifically. bubble.py/bubble.go emit
// the same .sc-point/.sc-series/data-* DOM contract as scatter, with two
// deliberate differences the design calls out: bubble carries a `data-z`
// attribute (the size-scale input, alongside data-x/data-y), and its radius
// does NOT grow on hover/keyboard-focus the way line/scatter's markers do
// (data-r-hover == data-r for every bubble - the radius already encodes z,
// so a bubble growing on hover would misrepresent its own magnitude). That
// full contract was never directly verified in a live browser before this
// file existed (chart-admission-checklist.md Phase 6). This mirrors
// browser-qualification.test.js's exact interaction assertions against a
// live bubble chart built on explicit point-model ([x,y,z] positional) data,
// rather than inferring bubble works because scatter's test passes.
const assert = require("node:assert/strict");
const fs = require("node:fs");
const http = require("node:http");
const os = require("node:os");
const path = require("node:path");
const { execFileSync } = require("node:child_process");
const test = require("node:test");

const { chromium } = require("playwright");

function makeTempDir() {
  return fs.mkdtempSync(path.join(os.tmpdir(), "stonecharts-bubble-browser-"));
}

function renderFixtureHtml(outPath) {
  const repoRoot = path.resolve(__dirname, "..");
  const script = String.raw`
from pathlib import Path
import sys
sys.path.insert(0, r"${path.join(repoRoot, "libs", "python")}")
from stonecharts import Axis, ChartSpec, Series, render_html

spec = ChartSpec(
    type="bubble",
    title="Bubble Browser Qualification",
    x_axis=Axis(title="X"),
    series=[
        Series(name="Alpha", data=[[10, 1, 100], [20, 2, 5000]]),
        Series(name="Beta", data=[[10, 3, 2500], [20, 4, 100]]),
    ],
)
Path(r"${outPath}").write_text(render_html(spec), encoding="utf-8")
`;
  const tmpDir = makeTempDir();
  const scriptPath = path.join(tmpDir, "gen.py");
  fs.writeFileSync(scriptPath, script, "utf-8");
  try {
    execFileSync("python", [scriptPath], {
      cwd: repoRoot,
      stdio: "inherit",
      env: {
        ...process.env,
        PYTHONPATH: path.join(repoRoot, "libs", "python"),
      },
    });
  } finally {
    fs.rmSync(tmpDir, { recursive: true, force: true });
  }
}

function serveDirectory(rootDir) {
  const server = http.createServer((req, res) => {
    const rawPath = new URL(req.url, "http://127.0.0.1").pathname;
    const relPath = rawPath === "/" ? "/chart.html" : rawPath;
    const filePath = path.normalize(path.join(rootDir, relPath));
    const rootPrefix = path.normalize(rootDir + path.sep);
    if (!filePath.startsWith(rootPrefix)) {
      res.writeHead(403, { "Content-Type": "text/plain; charset=utf-8" });
      res.end("forbidden");
      return;
    }
    fs.readFile(filePath, (err, data) => {
      if (err) {
        res.writeHead(404, { "Content-Type": "text/plain; charset=utf-8" });
        res.end("not found");
        return;
      }
      res.writeHead(200, { "Content-Type": "text/html; charset=utf-8" });
      res.end(data);
    });
  });

  return new Promise((resolve, reject) => {
    server.once("error", reject);
    server.listen(0, "127.0.0.1", () => {
      const addr = server.address();
      resolve({
        server,
        baseUrl: `http://127.0.0.1:${addr.port}`,
      });
    });
  });
}

async function waitForTooltip(page, expectedState) {
  await page.waitForFunction(
    (state) => {
      const tip = document.querySelector(".sc-tooltip");
      if (!tip) return false;
      const visible = getComputedStyle(tip).display !== "none";
      return state === "visible" ? visible : !visible;
    },
    expectedState
  );
}

test("bubble chart local HTTP Chromium browser qualification covers runtime and a11y contracts", async () => {
  const tmpDir = makeTempDir();
  const htmlPath = path.join(tmpDir, "chart.html");
  renderFixtureHtml(htmlPath);

  const { server, baseUrl } = await serveDirectory(tmpDir);
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 960, height: 720 } });

  try {
    await page.goto(`${baseUrl}/chart.html`, { waitUntil: "domcontentloaded" });
    await page.waitForFunction(() => {
      const svg = document.querySelector("svg.sc-chart");
      const legend = document.querySelector(".sc-legend-item");
      return svg && svg.getAttribute("tabindex") === "0" && legend && legend.getAttribute("role") === "button";
    });

    const svg = page.locator("svg.sc-chart");
    const tooltip = page.locator(".sc-tooltip");
    const legend0 = page.locator('.sc-legend-item[data-series="0"]');
    const series0 = page.locator('.sc-series[data-series="0"]');
    // data-x/data-y are numeric like scatter; data-z is the new bubble
    // attribute (the size-scale input).
    const point00 = page.locator('.sc-point[data-series="0"][data-x="10"]');
    const point01 = page.locator('.sc-point[data-series="0"][data-x="20"]');
    const point11 = page.locator('.sc-point[data-series="1"][data-x="20"]');

    // bubble emits no sc-series-line path (unconnected circles), and every
    // point is both .sc-point and .sc-bubble.
    assert.equal(await page.locator(".sc-series-line").count(), 0);
    assert.equal(await page.locator(".sc-bubble").count(), 4);

    // The size-scale is honored: min z (100) -> radius 4, max z (5000) -> 32.
    assert.equal(await point00.getAttribute("data-z"), "100");
    assert.equal(await point00.getAttribute("r"), "4");
    assert.equal(await point01.getAttribute("data-z"), "5000");
    assert.equal(await point01.getAttribute("r"), "32");

    // data-r-hover == data-r for every bubble (radius already encodes z; a
    // bubble growing on hover would misrepresent its own magnitude).
    for (const loc of [point00, point01, point11]) {
      assert.equal(await loc.getAttribute("data-r-hover"), await loc.getAttribute("data-r"));
    }

    await point00.hover();
    await waitForTooltip(page, "visible");
    const hoverText = (await tooltip.textContent()) || "";
    assert.match(hoverText, /10/);
    assert.match(hoverText, /Alpha/);
    assert.match(hoverText, /1/);

    await svg.focus();
    await page.keyboard.press("ArrowRight");
    // Keyboard nav moves the active point; bubble's own radius never
    // changes (unlike scatter's active-point growth from data-r-hover).
    assert.equal(await point00.getAttribute("r"), "4");
    assert.equal(await point01.getAttribute("r"), "32");
    assert.equal(await page.evaluate(() => document.activeElement && document.activeElement.matches("svg.sc-chart")), true);

    await page.keyboard.press("ArrowDown");
    assert.equal(await point01.getAttribute("r"), "32");
    assert.equal(await point11.getAttribute("r"), "4");

    await page.keyboard.press("Escape");
    await waitForTooltip(page, "hidden");
    assert.equal(await page.evaluate(() => document.activeElement && document.activeElement.matches("svg.sc-chart")), true);

    await legend0.click();
    assert.equal(await series0.evaluate((el) => el.style.display), "none");
    assert.equal(await legend0.getAttribute("aria-pressed"), "false");
    assert.equal(await series0.getAttribute("aria-hidden"), "true");
    assert.equal(await page.locator('.sc-point[data-series="0"][data-x="10"]').getAttribute("aria-hidden"), "true");

    await legend0.focus();
    await page.keyboard.press("Space");
    assert.equal(await series0.evaluate((el) => el.style.display), "");
    assert.equal(await legend0.getAttribute("aria-pressed"), "true");
    assert.equal(await series0.getAttribute("aria-hidden"), null);
  } finally {
    await page.close().catch(() => {});
    await browser.close().catch(() => {});
    await new Promise((resolve) => server.close(resolve));
    fs.rmSync(tmpDir, { recursive: true, force: true });
  }
});
