const assert = require("node:assert/strict");
const fs = require("node:fs");
const http = require("node:http");
const os = require("node:os");
const path = require("node:path");
const { execFileSync } = require("node:child_process");
const test = require("node:test");

const { chromium } = require("playwright");

const repoRoot = path.resolve(__dirname, "..");

function makeTempDir() {
  return fs.mkdtempSync(path.join(os.tmpdir(), "stonecharts-all-browser-"));
}

function renderAllFixtureHtml(outDir) {
  const script = String.raw`
import json
import pathlib
import sys

repo = pathlib.Path(sys.argv[1])
out = pathlib.Path(sys.argv[2])
sys.path.insert(0, str(repo / "libs" / "python"))

from stonecharts import ChartSpec, render_html

registry = json.loads((repo / "spec" / "capabilities.json").read_text(encoding="utf-8"))
for item in registry["chartTypes"]:
    chart_id = item["id"]
    chart_dir = "line-basic" if chart_id == "line" else chart_id
    examples = sorted((repo / "charts" / chart_dir / "examples").glob("*.json"))
    preferred = repo / "charts" / chart_dir / "examples" / "basic.json"
    fixture = preferred if preferred.exists() else examples[0]
    spec = ChartSpec.from_dict(json.loads(fixture.read_text(encoding="utf-8")))
    (out / f"{chart_id}.html").write_text(render_html(spec), encoding="utf-8")
    print(f"{chart_id}|{fixture.stem}")
`;
  const scriptPath = path.join(outDir, "generate.py");
  fs.writeFileSync(scriptPath, script, "utf-8");
  const output = execFileSync("python", [scriptPath, repoRoot, outDir], {
    cwd: repoRoot,
    encoding: "utf-8",
    env: { ...process.env, PYTHONPATH: path.join(repoRoot, "libs", "python") },
  });
  fs.rmSync(scriptPath, { force: true });
  return output
    .trim()
    .split(/\r?\n/)
    .filter(Boolean)
    .map((line) => {
      const [chartId, fixture] = line.split("|");
      return { chartId, fixture };
    });
}

function serveDirectory(rootDir) {
  const server = http.createServer((req, res) => {
    const rawPath = new URL(req.url, "http://127.0.0.1").pathname;
    const filePath = path.normalize(path.join(rootDir, rawPath));
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
      resolve({ server, baseUrl: `http://127.0.0.1:${addr.port}` });
    });
  });
}

test("all 36 certified charts satisfy the browser and accessibility contract", { timeout: 120000 }, async (t) => {
  const tmpDir = makeTempDir();
  const fixtures = renderAllFixtureHtml(tmpDir);
  assert.equal(fixtures.length, 36, "capability registry must produce exactly 36 browser fixtures");

  const { server, baseUrl } = await serveDirectory(tmpDir);
  const browser = await chromium.launch({ headless: true });

  try {
    for (const { chartId, fixture } of fixtures) {
      await t.test(`${chartId}/${fixture}`, async () => {
        const page = await browser.newPage({ viewport: { width: 960, height: 720 } });
        const browserErrors = [];
        page.on("pageerror", (error) => browserErrors.push(`pageerror: ${error.message}`));
        page.on("console", (message) => {
          if (message.type() === "error") browserErrors.push(`console: ${message.text()}`);
        });

        try {
          const response = await page.goto(`${baseUrl}/${chartId}.html`, { waitUntil: "domcontentloaded" });
          assert.equal(response.status(), 200);
          await page.waitForFunction(() => document.querySelector("svg.sc-chart")?.getAttribute("tabindex") === "0");

          const svg = page.locator("svg.sc-chart");
          assert.equal(await svg.count(), 1);
          assert.equal(await svg.getAttribute("role"), "img");
          assert.ok((await svg.getAttribute("aria-label"))?.trim(), "chart needs an accessible name");

          const points = page.locator("svg.sc-chart .sc-point");
          assert.ok((await points.count()) > 0, "chart needs at least one interactive data mark");

          const table = page.locator("table.sc-visually-hidden");
          assert.equal(await table.count(), 1, "chart needs a screen-reader data table");
          assert.ok((await table.locator("caption").textContent())?.trim(), "data table needs a caption");
          assert.ok((await table.locator("tr").count()) >= 2, "data table needs headers and data");

          await points.first().dispatchEvent("mouseenter");
          await page.waitForFunction(() => {
            const tooltip = document.querySelector(".sc-tooltip");
            return tooltip && getComputedStyle(tooltip).display !== "none" && tooltip.textContent.trim().length > 0;
          }, null, { timeout: 2000 });

          await svg.focus();
          assert.equal(await page.evaluate(() => document.activeElement?.matches("svg.sc-chart")), true);
          await page.keyboard.press("ArrowRight");
          assert.equal(await page.evaluate(() => document.activeElement?.matches("svg.sc-chart")), true);
          await page.keyboard.press("Escape");

          const legend = page.locator(".sc-legend-item").first();
          if ((await legend.count()) > 0) {
            assert.equal(await legend.getAttribute("role"), "button");
            assert.ok(["true", "false"].includes(await legend.getAttribute("aria-pressed")));
          }

          assert.deepEqual(browserErrors, []);
        } finally {
          await page.close();
        }
      });
    }
  } finally {
    await browser.close().catch(() => {});
    await new Promise((resolve) => server.close(resolve));
    fs.rmSync(tmpDir, { recursive: true, force: true });
  }
});
