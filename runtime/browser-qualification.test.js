const assert = require("node:assert/strict");
const fs = require("node:fs");
const http = require("node:http");
const os = require("node:os");
const path = require("node:path");
const { execFileSync } = require("node:child_process");
const test = require("node:test");

const { chromium } = require("playwright");

function makeTempDir() {
  return fs.mkdtempSync(path.join(os.tmpdir(), "stonecharts-browser-"));
}

function renderFixtureHtml(outPath) {
  const repoRoot = path.resolve(__dirname, "..");
  const script = String.raw`
from pathlib import Path
import sys
sys.path.insert(0, r"${path.join(repoRoot, "libs", "python")}")
from stonecharts import Axis, ChartSpec, Series, render_html

spec = ChartSpec(
    type="line",
    title="Browser Qualification",
    x_axis=Axis(categories=["Jan", "Feb"]),
    series=[
        Series(name="Alpha", data=[1, 2]),
        Series(name="Beta", data=[3, 4]),
    ],
)
Path(r"${outPath}").write_text(render_html(spec), encoding="utf-8")
`;

  execFileSync("python", ["-c", script], {
    cwd: repoRoot,
    stdio: "inherit",
    env: {
      ...process.env,
      PYTHONPATH: path.join(repoRoot, "libs", "python"),
    },
  });
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

test("local HTTP Chromium browser qualification covers runtime and a11y contracts", async () => {
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
    const series1 = page.locator('.sc-series[data-series="1"]');
    const point00 = page.locator('.sc-point[data-series="0"][data-x="Jan"]');
    const point01 = page.locator('.sc-point[data-series="0"][data-x="Feb"]');
    const point11 = page.locator('.sc-point[data-series="1"][data-x="Feb"]');

    await point00.hover();
    await waitForTooltip(page, "visible");
    const hoverText = (await tooltip.textContent()) || "";
    assert.match(hoverText, /Jan/);
    assert.match(hoverText, /Alpha/);
    assert.match(hoverText, /1/);

    await svg.focus();
    await page.keyboard.press("ArrowRight");
    assert.equal(await point00.getAttribute("r"), "3.5");
    assert.equal(await point01.getAttribute("r"), "6");
    assert.equal(await page.evaluate(() => document.activeElement && document.activeElement.matches("svg.sc-chart")), true);

    await page.keyboard.press("ArrowDown");
    assert.equal(await point01.getAttribute("r"), "3.5");
    assert.equal(await point11.getAttribute("r"), "6");

    await page.keyboard.press("Escape");
    await waitForTooltip(page, "hidden");
    assert.equal(await point11.getAttribute("r"), "3.5");
    assert.equal(await page.evaluate(() => document.activeElement && document.activeElement.matches("svg.sc-chart")), true);

    await legend0.click();
    assert.equal(await series0.evaluate((el) => el.style.display), "none");
    assert.equal(await legend0.getAttribute("aria-pressed"), "false");
    assert.equal(await series0.getAttribute("aria-hidden"), "true");
    assert.equal(await page.locator('.sc-point[data-series="0"][data-x="Jan"]').getAttribute("aria-hidden"), "true");

    await svg.focus();
    assert.equal(await page.locator('.sc-point[r="6"]').getAttribute("data-series"), "1");
    assert.equal(await page.locator('.sc-point[r="6"]').getAttribute("data-x"), "Jan");
    await page.keyboard.press("ArrowRight");
    assert.equal(await page.locator('.sc-point[r="6"]').getAttribute("data-series"), "1");
    assert.equal(await page.locator('.sc-point[r="6"]').getAttribute("data-x"), "Feb");

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
