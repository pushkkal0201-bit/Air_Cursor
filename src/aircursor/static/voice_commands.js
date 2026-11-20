/* Strict, allowlisted voice commands. Shared by the browser and Node.js tests. */
(function (root, factory) {
  const parser = factory();
  if (typeof module === "object" && module.exports) module.exports = parser;
  if (root) root.AirCursorVoiceCommands = parser;
})(typeof globalThis === "object" ? globalThis : null, function () {
  "use strict";
  const actions = Object.freeze({
    "next slide": "next_slide",
    "next page": "next_slide",
    "previous slide": "previous_slide",
    "previous page": "previous_slide",
    "play pause": "play_pause",
    "pause video": "play_pause",
    "resume video": "play_pause",
    "volume up": "volume_up",
    "increase volume": "volume_up",
    "volume down": "volume_down",
    "decrease volume": "volume_down",
    "mute": "mute",
    "unmute": "mute",
    "escape": "escape",
    "press escape": "escape",
    "enter": "enter",
    "press enter": "enter"
  });
  const clicks = Object.freeze({
    "left click": "left",
    "click": "left",
    "right click": "right",
    "double click": "double"
  });
  const scrolls = Object.freeze({
    "scroll up": 5,
    "scroll down": -5
  });
  function parse(input) {
    if (typeof input !== "string" || input.length > 160) return null;
    const phrase = input.toLowerCase().replace(/[^a-z\s]/g, " ").replace(/\s+/g, " ").trim();
    if (Object.prototype.hasOwnProperty.call(actions, phrase)) {
      return {kind: "action", value: actions[phrase]};
    }
    if (Object.prototype.hasOwnProperty.call(clicks, phrase)) {
      return {kind: "click", value: clicks[phrase]};
    }
    if (Object.prototype.hasOwnProperty.call(scrolls, phrase)) {
      return {kind: "scroll", value: scrolls[phrase]};
    }
    return null;
  }
  return Object.freeze({parse});
});
