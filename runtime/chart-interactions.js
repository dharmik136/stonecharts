/*!
 * PeakCharts interaction runtime — shared across all language libraries.
 * Vanilla JS, zero dependencies. Operates on any SVG that follows
 * spec/svg-contract.md (classes: pk-chart, pk-series, pk-point, pk-legend-item;
 * data-* attributes on points/series). Server-rendered SVG stays fully visible
 * without JS; this only *enhances* it (tooltip, point highlight, legend toggle,
 * crosshair). See spec/svg-contract.md for the contract this depends on.
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

  function setupChart(svg) {
    if (svg.__pkInit) return;
    svg.__pkInit = true;

    var wrap = svg.closest(".pk-chart-wrap") || svg.parentNode;
    var tip = wrap.querySelector(".pk-tooltip");
    if (!tip) {
      tip = document.createElement("div");
      tip.className = "pk-tooltip";
      tip.style.display = "none";
      wrap.appendChild(tip);
    }
    var crosshair = svg.querySelector(".pk-crosshair");

    function moveTip(e) {
      var r = wrap.getBoundingClientRect();
      var tw = tip.offsetWidth, th = tip.offsetHeight;
      var x = e.clientX - r.left + 14;
      var y = e.clientY - r.top + 14;
      if (x + tw > r.width) x = e.clientX - r.left - tw - 14;
      if (y + th > r.height) y = e.clientY - r.top - th - 14;
      tip.style.left = x + "px";
      tip.style.top = y + "px";
    }

    // Tooltip + highlight on data points.
    var points = svg.querySelectorAll(".pk-point");
    for (var i = 0; i < points.length; i++) {
      (function (pt) {
        var rBase = pt.getAttribute("data-r") || "3.5";
        var rHover = pt.getAttribute("data-r-hover") || "6";
        pt.addEventListener("mouseenter", function () {
          pt.setAttribute("r", rHover);
          var name = pt.getAttribute("data-series-name") || "";
          var color = pt.getAttribute("data-color") || "#333";
          var xl = pt.getAttribute("data-x");
          var yl = pt.getAttribute("data-y");
          tip.innerHTML =
            '<div class="pk-tt-title">' + escapeHtml(xl) + "</div>" +
            '<div class="pk-tt-row"><span class="pk-tt-dot" style="background:' + color + '"></span>' +
            escapeHtml(name) + ": <b>" + escapeHtml(yl) + "</b></div>";
          tip.style.display = "block";
          if (crosshair) {
            crosshair.setAttribute("x1", pt.getAttribute("cx"));
            crosshair.setAttribute("x2", pt.getAttribute("cx"));
            crosshair.style.display = "";
          }
        });
        pt.addEventListener("mousemove", moveTip);
        pt.addEventListener("mouseleave", function () {
          pt.setAttribute("r", rBase);
          tip.style.display = "none";
          if (crosshair) crosshair.style.display = "none";
        });
      })(points[i]);
    }

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

  function escapeHtml(s) {
    return String(s == null ? "" : s)
      .replace(/&/g, "&amp;").replace(/</g, "&lt;")
      .replace(/>/g, "&gt;").replace(/"/g, "&quot;");
  }

  if (document.readyState !== "loading") init();
  else document.addEventListener("DOMContentLoaded", function () { init(); });

  if (typeof window !== "undefined") window.PeakCharts = { init: init };
})();
