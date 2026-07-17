/*!
 * PeakCharts interaction runtime — shared across all language libraries.
 * Vanilla JS, zero dependencies. Operates on any SVG that follows
 * spec/svg-contract.md (classes: pk-chart, pk-series, pk-point, pk-legend-item;
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
    var charts = root.querySelectorAll(".pk-chart");
    for (var i = 0; i < charts.length; i++) setupChart(charts[i]);
  }

  var uidCounter = 0;

  // Uniquify this chart's <defs> ids (gradients/patterns) and rewrite its own
  // url(#id) references, so multiple charts on one page can't collide on shared
  // ids like "pk-grad-0". Runs at load, so the static SVG bytes stay unchanged.
  function scopeDefs(svg) {
    var defs = svg.querySelector("defs");
    if (!defs) return;
    var idNodes = defs.querySelectorAll("[id]");
    if (!idNodes.length) return;
    var uid = "pkc" + (uidCounter++), map = {};
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
    if (svg.__pkInit) return;
    svg.__pkInit = true;
    scopeDefs(svg);

    var wrap = svg.closest(".pk-chart-wrap") || svg.parentNode;
    var tip = wrap.querySelector(".pk-tooltip");
    if (!tip) {
      tip = document.createElement("div");
      tip.className = "pk-tooltip";
      tip.style.display = "none";
      wrap.appendChild(tip);
    }
    var crosshair = svg.querySelector(".pk-crosshair");

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
        '<div class="pk-tt-title">' + escapeHtml(pt.getAttribute("data-x")) + "</div>" +
        '<div class="pk-tt-row"><span class="pk-tt-dot" style="background:' + color + '"></span>' +
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

    // Tooltip + highlight on data points (mouse).
    var points = svg.querySelectorAll(".pk-point");
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
    setupKeyboard(svg, points, showPoint, hidePoint);

    // Legend click toggles the whole series on/off.
    var items = svg.querySelectorAll(".pk-legend-item");
    for (var j = 0; j < items.length; j++) {
      (function (item) {
        item.style.cursor = "pointer";
        item.addEventListener("click", function () {
          var s = item.getAttribute("data-series");
          var hidden = item.classList.toggle("pk-hidden");
          var members = svg.querySelectorAll('[data-series="' + s + '"]');
          for (var k = 0; k < members.length; k++) {
            if (members[k] === item) continue;
            members[k].style.display = hidden ? "none" : "";
          }
        });
      })(items[j]);
    }
  }

  function setupKeyboard(svg, points, showPoint, hidePoint) {
    if (!points.length) return;
    // Group points by series in DOM order: series[] holds per-series point arrays.
    var series = [], byKey = {};
    for (var i = 0; i < points.length; i++) {
      var k = points[i].getAttribute("data-series") || "0";
      if (!byKey[k]) { byKey[k] = []; series.push(byKey[k]); }
      byKey[k].push(points[i]);
    }
    var si = 0, pi = 0, active = null;
    function go(ns, np) {
      var col = series[ns];
      if (!col) return;
      np = Math.max(0, Math.min(np, col.length - 1));
      if (active) hidePoint(active);
      si = ns; pi = np; active = col[pi];
      showPoint(active, true);
    }
    function clear() { if (active) { hidePoint(active); active = null; } }
    svg.setAttribute("tabindex", "0");
    svg.addEventListener("focus", function () { if (!active) go(si, pi); });
    svg.addEventListener("blur", clear);
    svg.addEventListener("keydown", function (e) {
      var k = e.key;
      if (k === "ArrowRight") go(si, pi + 1);
      else if (k === "ArrowLeft") go(si, pi - 1);
      else if (k === "ArrowDown") go(Math.min(si + 1, series.length - 1), pi);
      else if (k === "ArrowUp") go(Math.max(si - 1, 0), pi);
      else if (k === "Home") go(si, 0);
      else if (k === "End") go(si, series[si].length - 1);
      else if (k === "Escape") { clear(); svg.blur(); }
      else return;
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

  if (typeof window !== "undefined") window.PeakCharts = { init: init };
})();
