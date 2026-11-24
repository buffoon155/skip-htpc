import assert from "node:assert/strict";
import fs from "node:fs";
import test from "node:test";
import vm from "node:vm";

const code = fs.readFileSync(new URL("./spatial.js", import.meta.url), "utf8");
const sandbox = {};
vm.createContext(sandbox);
vm.runInContext(code, sandbox);
const S = sandbox.SkipHtpcSpatial;

const left = { x: 0, y: 0, w: 100, h: 80 };
const right = { x: 140, y: 0, w: 100, h: 80 };
const below = { x: 0, y: 120, w: 100, h: 80 };

test("right arrow moves to the tile on the same row", () => {
  assert.equal(S.navigate(left, [left, right, below], "right"), right);
});

test("down arrow moves to the tile below", () => {
  assert.equal(S.navigate(left, [left, right, below], "down"), below);
});

test("a diagonal tile does not beat the straight neighbour", () => {
  const diagonal = { x: 140, y: 120, w: 100, h: 80 };
  assert.equal(S.navigate(left, [right, diagonal], "right"), right);
});

test("no candidate in that direction returns null", () => {
  assert.equal(S.navigate(left, [below], "right"), null);
});

test("the row handle on the same row wins", () => {
  const far = { y: 400, h: 40 };
  const near = { y: 80, h: 40 };
  assert.equal(S.closestVertically(100, [far, near]), near);
});

test("the first target is the top-left tile", () => {
  assert.equal(S.initialTarget([right, below, left]), left);
});

test("a tiny control inside a card is dropped", () => {
  const card = { x: 0, y: 0, w: 200, h: 100 };
  const icon = { x: 8, y: 8, w: 20, h: 20 };
  assert.deepEqual(S.preferTiles([card, icon]), [card]);
});

test("tiles that only overlap stay in the list", () => {
  assert.deepEqual(S.preferTiles([left, right]), [left, right]);
});

test("a large video owns the arrow keys", () => {
  const view = { w: 1920, h: 1080 };
  assert.equal(
    S.largeVideo([{ x: 0, y: 0, w: 1800, h: 1000 }], view),
    true
  );
  assert.equal(
    S.largeVideo([{ x: 0, y: 0, w: 320, h: 180 }], view),
    false
  );
});

test("off-screen and tiny rects are not candidates", () => {
  const view = { w: 1000, h: 800 };
  assert.equal(S.isUsableRect({ x: 10, y: 10, w: 4, h: 40 }, view), false);
  assert.equal(S.isUsableRect({ x: 4000, y: 10, w: 100, h: 40 }, view), false);
  assert.equal(S.isUsableRect({ x: 10, y: 10, w: 100, h: 40 }, view), true);
});

test("text fields keep the keys", () => {
  assert.equal(S.isTypingElement({ tagName: "INPUT" }), true);
  assert.equal(
    S.isTypingElement({ tagName: "DIV", isContentEditable: true }),
    true
  );
  assert.equal(S.isTypingElement({ tagName: "A" }), false);
  assert.equal(S.isTypingElement(null), false);
});
