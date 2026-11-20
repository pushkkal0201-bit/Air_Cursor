"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const {tiltToMovement} = require("../src/aircursor/static/motion_math.js");

test("motion calibration produces zero movement at neutral and inside deadzone", () => {
  const neutral={gamma:5,beta:12};
  assert.deepEqual(tiltToMovement(neutral,neutral,2),{dx:0,dy:0});
  assert.deepEqual(tiltToMovement({gamma:6,beta:11},neutral,2),{dx:0,dy:0});
});
test("tilting phone provides proportional continuous movement", () => {
  const neutral={gamma:0,beta:0};
  const fast=tiltToMovement({gamma:22,beta:-18},neutral,2);
  assert.ok(fast.dx>0);
  assert.ok(fast.dy<0);
  const more=tiltToMovement({gamma:22,beta:-18},neutral,4);
  assert.ok(more.dx>fast.dx);
  assert.ok(Math.abs(more.dy)>Math.abs(fast.dy));
});
test("invalid sensor readings are ignored and large tilts are clamped", () => {
  const neutral={gamma:0,beta:0};
  assert.deepEqual(tiltToMovement({gamma:null,beta:0},neutral,2),{dx:0,dy:0});
  assert.deepEqual(tiltToMovement({gamma:NaN,beta:0},neutral,2),{dx:0,dy:0});
  assert.deepEqual(tiltToMovement({gamma:10,beta:10},neutral,50),{dx:0,dy:0});
  const big=tiltToMovement({gamma:150,beta:-300},neutral,5);
  assert.deepEqual(big,{dx:28,dy:-28});
});
