/*!
 * StoneCharts interaction runtime — shared across all language libraries.
 * Vanilla JS, zero dependencies. Operates on any SVG that follows
 * spec/svg-contract.md (classes: sc-chart, sc-series, sc-point, sc-legend-item;
 * data-* attributes on points/series). Server-rendered SVG stays fully visible
 * without JS; this only *enhances* it (tooltip, point highlight, legend toggle,
 * crosshair, keyboard navigation). See spec/svg-contract.md for the contract this
 * depends on.
 *
 * Proprietary. Copyright (c) 2026 Dharmik Shingala. All rights reserved.
 * No use, copying, or distribution without written permission. See LICENSE.
 */
(function () {
  "use strict";

  function init(root) {
    root = root || document;
    var charts = root.querySelectorAll(".sc-chart");
    for (var i = 0; i < charts.length; i++) setupChart(charts[i]);
  }

  var uidCounter = 0;

  // Uniquify this chart's <defs> ids (gradients/patterns) and rewrite its own
  // url(#id) references, so multiple charts on one page can't collide on shared
  // ids like "sc-grad-0". Runs at load, so the static SVG bytes stay unchanged.
  function scopeDefs(svg) {
    var defs = svg.querySelector("defs");
    if (!defs) return;
    var idNodes = defs.querySelectorAll("[id]");
    if (!idNodes.length) return;
    var uid = "scc" + (uidCounter++), map = {};
    for (var i = 0; i < idNodes.length; i++) {
      var oldId = idNodes[i].getAttribute("id");
      map[oldId] = uid + "-" + oldId;
      idNodes[i].setAttribute("id", map[oldId]);
    }
    var refs = svg.querySelectorAll("[fill],[stroke]");
    for (var j = 0; j < refs.length; j++) {
      var attrs = ["fill", "stroke"];
      for (var a = 0; a < attrs.length; a++) {
        var v = refs[j].getAttribute(attrs[a]);
        if (v && v.indexOf("url(#") === 0) {
          var id = v.slice(5, -1);
          if (map[id]) refs[j].setAttribute(attrs[a], "url(#" + map[id] + ")");
        }
      }
    }
  }

  function setupChart(svg) {
    if (svg.__scInit) return;
    svg.__scInit = true;
    scopeDefs(svg);

    var wrap = svg.closest(".sc-chart-wrap") || svg.parentNode;
    var tip = wrap.querySelector(".sc-tooltip");
    if (!tip) {
      tip = document.createElement("div");
      tip.className = "sc-tooltip";
      tip.style.display = "none";
      wrap.appendChild(tip);
    }
    var crosshair = svg.querySelector(".sc-crosshair");
    var activePoint = null;
    var clearActive = function () {};

    function seriesGroupFor(pt) {
      var node = pt;
      while (node && node !== svg) {
        if (node.classList && node.classList.contains("sc-series")) return node;
        node = node.parentNode;
      }
      return null;
    }
    function isVisiblePoint(pt) {
      var group = seriesGroupFor(pt);
      return !!group && group.style.display !== "none";
    }

    function positionTip(clientX, clientY) {
      var r = wrap.getBoundingClientRect();
      var tw = tip.offsetWidth, th = tip.offsetHeight;
      var x = clientX - r.left + 14;
      var y = clientY - r.top + 14;
      if (x + tw > r.width) x = clientX - r.left - tw - 14;
      if (y + th > r.height) y = clientY - r.top - th - 14;
      tip.style.left = x + "px";
      tip.style.top = y + "px";
    }
    function moveTip(e) { positionTip(e.clientX, e.clientY); }

    // Show/hide tooltip + highlight + crosshair for one point. Shared by mouse
    // (hover) and keyboard (focus/arrows). atPoint=true anchors the tooltip to the
    // point's own position (keyboard) instead of the cursor (mouse).
    function showPoint(pt, atPoint) {
      pt.setAttribute("r", pt.getAttribute("data-r-hover") || "6");
      var name = pt.getAttribute("data-series-name") || "";
      var color = pt.getAttribute("data-color") || "#333";
      tip.innerHTML =
        '<div class="sc-tt-title">' + escapeHtml(pt.getAttribute("data-x")) + "</div>" +
        '<div class="sc-tt-row"><span class="sc-tt-dot" style="background:' + color + '"></span>' +
        escapeHtml(name) + ": <b>" + escapeHtml(pt.getAttribute("data-y")) + "</b></div>";
      tip.style.display = "block";
      if (crosshair) {
        crosshair.setAttribute("x1", pt.getAttribute("cx"));
        crosshair.setAttribute("x2", pt.getAttribute("cx"));
        crosshair.style.display = "";
      }
      if (atPoint) {
        var pr = pt.getBoundingClientRect();
        positionTip(pr.left + pr.width / 2, pr.top + pr.height / 2);
      }
    }
    function hidePoint(pt) {
      pt.setAttribute("r", pt.getAttribute("data-r") || "3.5");
      tip.style.display = "none";
      if (crosshair) crosshair.style.display = "none";
    }

    function setLegendState(item, hidden) {
      var s = item.getAttribute("data-series");
      item.classList.toggle("sc-hidden", hidden);
      item.setAttribute("aria-pressed", hidden ? "false" : "true");
      var members = svg.querySelectorAll('[data-series="' + s + '"]');
      for (var k = 0; k < members.length; k++) {
        if (members[k] === item) continue;
        members[k].style.display = hidden ? "none" : "";
        if (hidden) members[k].setAttribute("aria-hidden", "true");
        else members[k].removeAttribute("aria-hidden");
      }
      if (activePoint && !isVisiblePoint(activePoint)) clearActive();
    }

    // Tooltip + highlight on data points (mouse).
    var points = svg.querySelectorAll(".sc-point");
    for (var i = 0; i < points.length; i++) {
      (function (pt) {
        pt.addEventListener("mouseenter", function () { showPoint(pt, false); });
        pt.addEventListener("mousemove", moveTip);
        pt.addEventListener("mouseleave", function () { hidePoint(pt); });
      })(points[i]);
    }

    // Keyboard navigation: the chart is a single focus stop; arrow keys walk the
    // points (Left/Right within a series, Up/Down across series, Home/End, Esc).
    // Sighted keyboard users get the visual tooltip; screen-reader users have the
    // data table. tabindex is set here at runtime so the static SVG stays unchanged.
    setupKeyboard(
      svg,
      points,
      showPoint,
      hidePoint,
      function (pt) { activePoint = pt; },
      function (fn) { clearActive = fn; }
    );

    // Legend click/keyboard toggles the whole series on/off.
    var items = svg.querySelectorAll(".sc-legend-item");
    for (var j = 0; j < items.length; j++) {
      (function (item) {
        item.style.cursor = "pointer";
        item.setAttribute("tabindex", "0");
        item.setAttribute("role", "button");
        item.setAttribute("aria-pressed", "true");
        item.addEventListener("click", function () {
          setLegendState(item, !item.classList.contains("sc-hidden"));
        });
        item.addEventListener("keydown", function (e) {
          var k = e.key;
          if (k === "Enter" || k === " " || k === "Space" || k === "Spacebar") {
            e.preventDefault();
            setLegendState(item, !item.classList.contains("sc-hidden"));
          }
        });
      })(items[j]);
    }
  }

  function setupKeyboard(svg, points, showPoint, hidePoint, setActivePoint, setClearActive) {
    if (!points.length) return;
    function series() {
      var visible = [], byKey = {};
      for (var i = 0; i < points.length; i++) {
        var pt = points[i];
        var group = pt.parentNode;
        while (group && (!group.classList || !group.classList.contains("sc-series"))) group = group.parentNode;
        if (!group || group.style.display === "none") continue;
        var k = pt.getAttribute("data-series") || "0";
        if (!byKey[k]) { byKey[k] = []; visible.push(byKey[k]); }
        byKey[k].push(pt);
      }
      return visible;
    }
    function pointPosition(series, pt) {
      for (var si = 0; si < series.length; si++) {
        for (var pi = 0; pi < series[si].length; pi++) {
          if (series[si][pi] === pt) return { si: si, pi: pi };
        }
      }
      return null;
    }
    var si = 0, pi = 0, active = null;
    function go(series, ns, np) {
      var col = series[ns];
      if (!col) return;
      np = Math.max(0, Math.min(np, col.length - 1));
      if (active) hidePoint(active);
      si = ns; pi = np; active = col[pi];
      setActivePoint(active);
      showPoint(active, true);
    }
    function clear() {
      if (active) { hidePoint(active); active = null; }
      setActivePoint(null);
    }
    setClearActive(clear);
    svg.setAttribute("tabindex", "0");
    svg.addEventListener("focus", function () {
      var s = series();
      if (!active && s.length) go(s, 0, 0);
    });
    svg.addEventListener("blur", clear);
    svg.addEventListener("keydown", function (e) {
      var k = e.key;
      var s = series();
      var pos = active ? pointPosition(s, active) : null;
      if (k === "ArrowRight") {
        if (!pos) go(s, 0, 0);
        else go(s, pos.si, pos.pi + 1);
      } else if (k === "ArrowLeft") {
        if (!pos) go(s, 0, 0);
        else go(s, pos.si, pos.pi - 1);
      } else if (k === "ArrowDown") {
        if (!pos) go(s, 0, 0);
        else go(s, Math.min(pos.si + 1, s.length - 1), pos.pi);
      } else if (k === "ArrowUp") {
        if (!pos) go(s, 0, 0);
        else go(s, Math.max(pos.si - 1, 0), pos.pi);
      } else if (k === "Home") {
        if (!pos) go(s, 0, 0);
        else go(s, pos.si, 0);
      } else if (k === "End") {
        if (!pos) go(s, 0, 0);
        else go(s, pos.si, s[pos.si].length - 1);
      } else if (k === "Escape") {
        // Collapse the chart's active state but KEEP focus on the SVG (Tab still
        // moves on). If nothing is active, let Esc bubble (e.g. to close a modal).
        if (!active) return;
        clear();
      } else return;
      e.preventDefault();
    });
  }

  function escapeHtml(s) {
    return String(s == null ? "" : s)
      .replace(/&/g, "&amp;").replace(/</g, "&lt;")
      .replace(/>/g, "&gt;").replace(/"/g, "&quot;");
  }

  if (document.readyState !== "loading") init();
  else document.addEventListener("DOMContentLoaded", function () { init(); });

  if (typeof window !== "undefined") window.StoneCharts = { init: init };
})();
