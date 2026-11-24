// Pure spatial-navigation helpers. The content script supplies rects from
// the page; this file does not touch the DOM so the same functions run
// under Node's test runner.
(function (root) {
  function center(rect) {
    return { x: rect.x + rect.w / 2, y: rect.y + rect.h / 2 };
  }

  function inDirection(from, to, direction) {
    var a = center(from);
    var b = center(to);
    var dx = b.x - a.x;
    var dy = b.y - a.y;
    var horizontal = direction === "left" || direction === "right";
    var primary = horizontal ? Math.abs(dx) : Math.abs(dy);
    var secondary = horizontal ? Math.abs(dy) : Math.abs(dx);
    if (primary < 4) return false;
    if (secondary > primary * 4) return false;
    if (direction === "left") return dx < 0;
    if (direction === "right") return dx > 0;
    if (direction === "up") return dy < 0;
    if (direction === "down") return dy > 0;
    return false;
  }

  function score(from, to, direction) {
    if (!inDirection(from, to, direction)) return null;
    var a = center(from);
    var b = center(to);
    var dx = Math.abs(b.x - a.x);
    var dy = Math.abs(b.y - a.y);
    var horizontal = direction === "left" || direction === "right";
    var primary = horizontal ? dx : dy;
    var secondary = horizontal ? dy : dx;
    return primary + secondary * 2;
  }

  function navigate(current, candidates, direction) {
    var best = null;
    var bestScore = Infinity;
    for (var i = 0; i < candidates.length; i++) {
      var candidate = candidates[i];
      if (candidate === current) continue;
      if (
        current &&
        candidate.el &&
        current.el &&
        candidate.el === current.el
      ) {
        continue;
      }
      var value = score(current, candidate, direction);
      if (value === null || value >= bestScore) continue;
      bestScore = value;
      best = candidate;
    }
    return best;
  }

  function initialTarget(candidates) {
    if (!candidates.length) return null;
    var sorted = candidates.slice().sort(function (a, b) {
      return a.y - b.y || a.x - b.x;
    });
    return sorted[0];
  }

  function contains(outer, inner) {
    return (
      inner.x >= outer.x - 1 &&
      inner.y >= outer.y - 1 &&
      inner.x + inner.w <= outer.x + outer.w + 1 &&
      inner.y + inner.h <= outer.y + outer.h + 1
    );
  }

  function area(rect) {
    return rect.w * rect.h;
  }

  function preferTiles(items) {
    return items.filter(function (item) {
      var itemArea = area(item);
      return !items.some(function (other) {
        if (other === item) return false;
        if (!contains(other, item)) return false;
        return itemArea < area(other) * 0.3;
      });
    });
  }

  function isUsableRect(rect, view, marginFraction) {
    var margin = marginFraction === undefined ? 0.5 : marginFraction;
    if (rect.w < 8 || rect.h < 8) return false;
    var mx = view.w * margin;
    var my = view.h * margin;
    return (
      rect.x < view.w + mx &&
      rect.x + rect.w > -mx &&
      rect.y < view.h + my &&
      rect.y + rect.h > -my
    );
  }

  function largeVideo(rects, view) {
    return rects.some(function (rect) {
      return rect.w >= view.w * 0.7 && rect.h >= view.h * 0.7;
    });
  }

  function closestVertically(originY, items) {
    var best = null;
    var bestDy = Infinity;
    items.forEach(function (item) {
      var dy = Math.abs(item.y + item.h / 2 - originY);
      if (dy < bestDy) {
        bestDy = dy;
        best = item;
      }
    });
    return best;
  }

  function isTypingElement(el) {
    if (!el || !el.tagName) return false;
    var tag = String(el.tagName).toUpperCase();
    if (tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT") return true;
    return Boolean(el.isContentEditable);
  }

  root.SkipHtpcSpatial = {
    center: center,
    inDirection: inDirection,
    score: score,
    navigate: navigate,
    initialTarget: initialTarget,
    contains: contains,
    preferTiles: preferTiles,
    isUsableRect: isUsableRect,
    largeVideo: largeVideo,
    closestVertically: closestVertically,
    isTypingElement: isTypingElement,
  };
})(globalThis);
