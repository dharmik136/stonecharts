const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const vm = require("node:vm");

class FakeClassList {
  constructor(node, initial) {
    this.node = node;
    this.set = new Set(initial || []);
  }
  contains(token) {
    return this.set.has(token);
  }
  add(...tokens) {
    for (const token of tokens) this.set.add(token);
    this._sync();
  }
  remove(...tokens) {
    for (const token of tokens) this.set.delete(token);
    this._sync();
  }
  toggle(token, force) {
    const has = this.set.has(token);
    const next = force === undefined ? !has : !!force;
    if (next) this.set.add(token);
    else this.set.delete(token);
    this._sync();
    return next;
  }
  _sync() {
    this.node.attributes.class = Array.from(this.set).join(" ");
  }
}

class FakeElement {
  constructor(tagName, classes) {
    this.tagName = tagName.toUpperCase();
    this.attributes = {};
    this.children = [];
    this.parentNode = null;
    this.listeners = {};
    this.style = {};
    this.classList = new FakeClassList(this, classes);
    this._innerHTML = "";
    this._rect = { left: 0, top: 0, width: 0, height: 0 };
  }
  appendChild(child) {
    child.parentNode = this;
    this.children.push(child);
    return child;
  }
  setRect(left, top, width, height) {
    this._rect = { left, top, width, height };
  }
  getBoundingClientRect() {
    return this._rect;
  }
  setAttribute(name, value) {
    this.attributes[name] = String(value);
    if (name === "class") {
      this.classList = new FakeClassList(this, String(value).split(/\s+/).filter(Boolean));
    }
  }
  getAttribute(name) {
    return Object.prototype.hasOwnProperty.call(this.attributes, name) ? this.attributes[name] : null;
  }
  removeAttribute(name) {
    delete this.attributes[name];
  }
  addEventListener(type, fn) {
    if (!this.listeners[type]) this.listeners[type] = [];
    this.listeners[type].push(fn);
  }
  dispatchEvent(event) {
    event = event || {};
    event.type = event.type || "";
    event.target = this;
    event.currentTarget = this;
    event.defaultPrevented = false;
    if (!event.preventDefault) {
      event.preventDefault = function () {
        this.defaultPrevented = true;
      };
    }
    const handlers = this.listeners[event.type] || [];
    for (const fn of handlers) fn.call(this, event);
    return !event.defaultPrevented;
  }
  closest(selector) {
    if (!selector || selector[0] !== ".") return null;
    const token = selector.slice(1);
    let node = this;
    while (node) {
      if (node.classList && node.classList.contains(token)) return node;
      node = node.parentNode;
    }
    return null;
  }
  querySelector(selector) {
    return this.querySelectorAll(selector)[0] || null;
  }
  querySelectorAll(selector) {
    const selectors = selector.split(",").map((s) => s.trim()).filter(Boolean);
    const out = [];
    const visit = (node) => {
      for (const child of node.children) {
        if (selectors.some((sel) => matches(child, sel))) out.push(child);
        visit(child);
      }
    };
    visit(this);
    return out;
  }
  set innerHTML(value) {
    this._innerHTML = String(value);
  }
  get innerHTML() {
    return this._innerHTML;
  }
  get offsetWidth() {
    return this._rect.width || 120;
  }
  get offsetHeight() {
    return this._rect.height || 50;
  }
}

function matches(node, selector) {
  if (selector === "*") return true;
  if (selector.startsWith(".")) return node.classList && node.classList.contains(selector.slice(1));
  const attr = selector.match(/^\[([^=\]]+)(?:="([^"]*)")?\]$/);
  if (attr) {
    const name = attr[1];
    const value = attr[2];
    const actual = node.getAttribute(name);
    return value === undefined ? actual !== null : actual === value;
  }
  return node.tagName && node.tagName.toLowerCase() === selector.toLowerCase();
}

function makePoint(series, index, x, y, cx, cy) {
  const pt = new FakeElement("circle", ["sc-point"]);
  pt.setAttribute("data-series", String(series));
  pt.setAttribute("data-series-name", "Series " + series);
  pt.setAttribute("data-x", x);
  pt.setAttribute("data-y", String(y));
  pt.setAttribute("data-color", series === 0 ? "#ff0000" : "#0000ff");
  pt.setAttribute("data-r", "3.5");
  pt.setAttribute("data-r-hover", "6");
  pt.setAttribute("cx", String(cx));
  pt.setAttribute("cy", String(cy));
  pt.setAttribute("r", "3.5");
  pt.setRect(cx - 3, cy - 3, 6, 6);
  return pt;
}

function loadRuntimeFixture() {
  const document = new FakeElement("document");
  document.readyState = "complete";
  document.addEventListener = function () {};
  document.createElement = function (tag) {
    return new FakeElement(tag);
  };

  const wrap = new FakeElement("div", ["sc-chart-wrap"]);
  wrap.setRect(0, 0, 260, 180);
  const svg = new FakeElement("svg", ["sc-chart"]);
  svg.setRect(0, 0, 260, 180);
  const tooltip = new FakeElement("div", ["sc-tooltip"]);
  tooltip.style.display = "none";
  tooltip.setRect(0, 0, 120, 50);
  const crosshair = new FakeElement("line", ["sc-crosshair"]);
  crosshair.style.display = "none";
  const series0 = new FakeElement("g", ["sc-series"]);
  series0.setAttribute("data-series", "0");
  const series1 = new FakeElement("g", ["sc-series"]);
  series1.setAttribute("data-series", "1");
  const legend = new FakeElement("g", ["sc-legend"]);
  const item0 = new FakeElement("g", ["sc-legend-item"]);
  item0.setAttribute("data-series", "0");
  const item1 = new FakeElement("g", ["sc-legend-item"]);
  item1.setAttribute("data-series", "1");

  const points = [
    makePoint(0, 0, "Jan", 7, 40, 40),
    makePoint(0, 1, "Feb", 9, 70, 40),
    makePoint(1, 0, "Jan", 4, 40, 110),
    makePoint(1, 1, "Feb", 5, 70, 110),
  ];

  series0.appendChild(points[0]);
  series0.appendChild(points[1]);
  series1.appendChild(points[2]);
  series1.appendChild(points[3]);
  legend.appendChild(item0);
  legend.appendChild(item1);
  svg.appendChild(crosshair);
  svg.appendChild(series0);
  svg.appendChild(series1);
  svg.appendChild(legend);
  wrap.appendChild(svg);
  wrap.appendChild(tooltip);

  document.children = [wrap];
  document.querySelectorAll = function (selector) {
    return selector === ".sc-chart" ? [svg] : [];
  };

  const window = {};
  const runtimePath = path.join(__dirname, "chart-interactions.js");
  const source = fs.readFileSync(runtimePath, "utf8");
  vm.runInNewContext(source, { document, window, console });

  return { document, window, wrap, svg, tooltip, crosshair, series0, series1, item0, item1, points };
}

test("runtime keyboard and legend semantics stay aligned with the contract", () => {
  const f = loadRuntimeFixture();

  assert.equal(f.svg.getAttribute("tabindex"), "0");
  assert.equal(f.item0.getAttribute("tabindex"), "0");
  assert.equal(f.item0.getAttribute("role"), "button");
  assert.equal(f.item0.getAttribute("aria-pressed"), "true");

  f.item0.dispatchEvent({ type: "keydown", key: "Enter" });
  assert.equal(f.series0.style.display, "none");
  assert.equal(f.item0.getAttribute("aria-pressed"), "false");
  assert.equal(f.series0.getAttribute("aria-hidden"), "true");
  assert.equal(f.points[0].getAttribute("aria-hidden"), "true");

  f.item0.dispatchEvent({ type: "click" });
  assert.equal(f.series0.style.display, "");
  assert.equal(f.item0.getAttribute("aria-pressed"), "true");
  assert.equal(f.series0.getAttribute("aria-hidden"), null);
  assert.equal(f.points[0].getAttribute("aria-hidden"), null);

  f.item0.dispatchEvent({ type: "keydown", key: " " });
  assert.equal(f.series0.style.display, "none");
  assert.equal(f.item0.getAttribute("aria-pressed"), "false");

  f.svg.dispatchEvent({ type: "focus" });
  assert.equal(f.points[2].getAttribute("r"), "6");
  assert.equal(f.points[3].getAttribute("r"), "3.5");
  assert.equal(f.tooltip.style.display, "block");

  f.svg.dispatchEvent({ type: "keydown", key: "ArrowRight" });
  assert.equal(f.points[2].getAttribute("r"), "3.5");
  assert.equal(f.points[3].getAttribute("r"), "6");

  f.svg.dispatchEvent({ type: "keydown", key: "Escape" });
  assert.equal(f.points[3].getAttribute("r"), "3.5");
});
