(function () {
  var S = globalThis.SkipHtpcSpatial;
  if (!S) return;

  var SELECTOR = [
    "a[href]",
    "button",
    "input",
    "select",
    "textarea",
    "summary",
    "[role='button']",
    "[role='link']",
    "[role='tab']",
    "[role='menuitem']",
    "[role='option']",
    "[role='slider']",
    "[tabindex]:not([tabindex='-1'])",
    "[data-uia='title-card']",
    "[data-uia='title-card-container']",
    "a.slider-refocus",
    "a[href*='/1-']",
  ].join(",");

  var PLAY_IN_CARD = [
    "[data-uia*='play']",
    "a[href*='/watch/']",
    "button[aria-label*='Play']",
    "button[aria-label*='Toista']",
    "button[aria-label*='Katso']",
    "a[aria-label*='Katso']",
    "a[aria-label*='Toista']",
  ].join(",");

  var BACK_SELECTOR = [
    "[data-uia='player-back']",
    "button[aria-label='Back']",
    "button[aria-label*='Takaisin']",
    "a[aria-label*='Takaisin']",
  ].join(",");

  var DIRS = {
    ArrowLeft: "left",
    ArrowRight: "right",
    ArrowUp: "up",
    ArrowDown: "down",
  };

  var current = null;

  function videoRects() {
    return Array.prototype.map.call(
      document.querySelectorAll("video"),
      function (video) {
        var rect = video.getBoundingClientRect();
        return { x: rect.left, y: rect.top, w: rect.width, h: rect.height };
      }
    );
  }

  function playerOwnsKeys() {
    return S.largeVideo(videoRects(), {
      w: window.innerWidth,
      h: window.innerHeight,
    });
  }

  function collect() {
    var view = { w: window.innerWidth, h: window.innerHeight };
    var nodes = document.querySelectorAll(SELECTOR);
    var items = [];
    for (var i = 0; i < nodes.length; i++) {
      var el = nodes[i];
      if (el.id === "skip-htpc-ring") continue;
      if (el.getAttribute("aria-hidden") === "true") continue;
      if (el.closest("[aria-hidden='true']")) continue;
      if (el.hasAttribute("disabled") || el.getAttribute("aria-disabled") === "true") {
        continue;
      }
      var rect = el.getBoundingClientRect();
      var box = { el: el, x: rect.left, y: rect.top, w: rect.width, h: rect.height };
      if (!S.isUsableRect(box, view, 0.5)) continue;
      var style = window.getComputedStyle(el);
      if (style.visibility === "hidden" || style.display === "none") continue;
      if (Number(style.opacity) === 0) continue;
      items.push(box);
    }
    return S.preferTiles(items);
  }

  function playTarget(el) {
    if (!el) return null;
    var uia = (el.getAttribute && el.getAttribute("data-uia")) || "";
    var label = (el.getAttribute && el.getAttribute("aria-label")) || "";
    var href = (el.getAttribute && el.getAttribute("href")) || "";
    if (/play|toista|katso/i.test(uia + " " + label) || href.indexOf("/watch/") !== -1) {
      return el;
    }
    if (!el.querySelector) return null;
    return el.querySelector(PLAY_IN_CARD);
  }

  function visibleBack() {
    var nodes = document.querySelectorAll(BACK_SELECTOR);
    var view = { w: window.innerWidth, h: window.innerHeight };
    for (var i = 0; i < nodes.length; i++) {
      var el = nodes[i];
      var rect = el.getBoundingClientRect();
      var box = { x: rect.left, y: rect.top, w: rect.width, h: rect.height };
      if (!S.isUsableRect(box, view, 0)) continue;
      var style = window.getComputedStyle(el);
      if (style.visibility === "hidden" || style.display === "none") continue;
      if (Number(style.opacity) === 0) continue;
      return el;
    }
    return null;
  }

  function rowHandle(direction) {
    var sel = direction === "right"
      ? "button.handleNext, [data-uia='handleNext'], [data-uia='pagination-next'], button[aria-label='Next'], button[aria-label*='Seuraava']"
      : "button.handlePrev, [data-uia='handlePrev'], [data-uia='pagination-previous'], button[aria-label='Previous'], button[aria-label*='Edellinen']";
    var view = { w: window.innerWidth, h: window.innerHeight };
    var nodes = document.querySelectorAll(sel);
    var items = [];
    for (var i = 0; i < nodes.length; i++) {
      var el = nodes[i];
      if (el.getAttribute("aria-hidden") === "true") continue;
      var rect = el.getBoundingClientRect();
      var box = { el: el, x: rect.left, y: rect.top, w: rect.width, h: rect.height };
      // Row chevrons are often opacity 0 until the pointer is over the row.
      if (!S.isUsableRect(box, view, 0)) continue;
      items.push(box);
    }
    if (!items.length) return null;
    var originY = window.innerHeight / 2;
    if (current && current.getBoundingClientRect) {
      var live = current.getBoundingClientRect();
      originY = live.top + live.height / 2;
    }
    var best = S.closestVertically(originY, items);
    if (!best) return null;
    if (Math.abs(best.y + best.h / 2 - originY) > 160) return null;
    return best.el;
  }

  function ring() {
    var el = document.getElementById("skip-htpc-ring");
    if (el) return el;
    el = document.createElement("div");
    el.id = "skip-htpc-ring";
    el.setAttribute("aria-hidden", "true");
    el.style.position = "fixed";
    el.style.zIndex = "2147483647";
    el.style.pointerEvents = "none";
    el.style.boxSizing = "border-box";
    el.style.border = "3px solid #ff6a00";
    el.style.outline = "3px solid #ff6a00";
    el.style.outlineOffset = "1px";
    el.style.borderRadius = "6px";
    el.style.boxShadow = "0 0 0 2px #000";
    el.style.display = "none";
    (document.documentElement || document.body).appendChild(el);
    return el;
  }

  function placeRing(rect) {
    var el = ring();
    el.style.display = "block";
    el.style.left = Math.max(0, rect.x) + "px";
    el.style.top = Math.max(0, rect.y) + "px";
    el.style.width = Math.max(0, rect.w) + "px";
    el.style.height = Math.max(0, rect.h) + "px";
  }

  function hideRing() {
    current = null;
    var el = document.getElementById("skip-htpc-ring");
    if (el) el.style.display = "none";
  }

  function show(item) {
    current = item.el;
    placeRing(item);
    if (item.el.scrollIntoView) {
      item.el.scrollIntoView({ block: "nearest", inline: "nearest" });
    }
  }

  function canScroll(el, axis) {
    var style = window.getComputedStyle(el);
    if (axis === "x") {
      var ox = style.overflowX;
      return (
        (ox === "auto" || ox === "scroll" || ox === "overlay") &&
        el.scrollWidth > el.clientWidth + 8
      );
    }
    var oy = style.overflowY;
    return (
      (oy === "auto" || oy === "scroll" || oy === "overlay") &&
      el.scrollHeight > el.clientHeight + 8
    );
  }

  function scrollableAncestor(el, direction) {
    var axis = direction === "left" || direction === "right" ? "x" : "y";
    var node = el ? el.parentElement : null;
    while (node && node !== document.documentElement) {
      if (canScroll(node, axis)) return node;
      node = node.parentElement;
    }
    return null;
  }

  function nudge(direction) {
    if (direction === "left" || direction === "right") {
      var handle = rowHandle(direction);
      if (handle) {
        handle.click();
        return;
      }
    }
    var scroller = scrollableAncestor(current, direction);
    var dx = direction === "right" ? 0.8 : direction === "left" ? -0.8 : 0;
    var dy = direction === "down" ? 0.8 : direction === "up" ? -0.8 : 0;
    if (scroller) {
      scroller.scrollBy({
        left: dx * scroller.clientWidth,
        top: dy * scroller.clientHeight,
        behavior: "auto",
      });
      return;
    }
    window.scrollBy({
      left: dx * window.innerWidth,
      top: dy * window.innerHeight,
      behavior: "auto",
    });
  }

  function onKey(event) {
    if (event.altKey || event.ctrlKey || event.metaKey || event.shiftKey) return;
    var direction = DIRS[event.key];
    var enter = event.key === "Enter";
    var back = event.key === "Escape";
    if (!direction && !enter && !back) return;
    if (playerOwnsKeys() || (event.target && event.target.tagName === "VIDEO")) {
      hideRing();
      return;
    }
    if (S.isTypingElement(document.activeElement)) {
      hideRing();
      return;
    }

    if (back) {
      var backEl = visibleBack();
      hideRing();
      event.preventDefault();
      event.stopPropagation();
      if (backEl) backEl.click();
      else window.history.back();
      return;
    }

    var items = collect();
    if (enter) {
      if (!current || !current.isConnected) {
        var first = S.initialTarget(items);
        if (!first) return;
        show(first);
        event.preventDefault();
        event.stopPropagation();
        return;
      }
      event.preventDefault();
      event.stopPropagation();
      (playTarget(current) || current).click();
      return;
    }

    var currentRect = null;
    if (current && current.isConnected) {
      var live = current.getBoundingClientRect();
      currentRect = {
        el: current,
        x: live.left,
        y: live.top,
        w: live.width,
        h: live.height,
      };
    }
    var next = currentRect
      ? S.navigate(currentRect, items, direction)
      : S.initialTarget(items);
    event.preventDefault();
    event.stopPropagation();
    if (next) {
      show(next);
      return;
    }
    nudge(direction);
  }

  window.addEventListener("keydown", onKey, true);
  window.addEventListener("resize", function () {
    if (!current || !current.isConnected) return;
    var rect = current.getBoundingClientRect();
    placeRing({ x: rect.left, y: rect.top, w: rect.width, h: rect.height });
  });
})();
