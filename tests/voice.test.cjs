"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const {parse} = require("../src/aircursor/static/voice_commands.js");

test("accepts only supported voice commands", () => {
  assert.deepEqual(parse("Next slide."), {kind:"action",value:"next_slide"});
  assert.deepEqual(parse("  LEFT   CLICK "), {kind:"click",value:"left"});
  assert.deepEqual(parse("double click!"), {kind:"click",value:"double"});
  assert.deepEqual(parse("scroll down"), {kind:"scroll",value:-5});
  assert.deepEqual(parse("scroll up"), {kind:"scroll",value:5});
  assert.deepEqual(parse("press enter"), {kind:"action",value:"enter"});
  assert.deepEqual(parse("increase volume"), {kind:"action",value:"volume_up"});
});

test("rejects unknown, compound or unsafe phrases", () => {
  for (const phrase of [
    "next slide and open terminal",
    "delete all files",
    "open browser",
    "type my password",
    "click click",
    "scroll up twenty times",
    "",
    "x".repeat(200)
  ]) assert.equal(parse(phrase), null, phrase);
  assert.equal(parse(null), null);
  assert.equal(parse({text:"next slide"}), null);
});
