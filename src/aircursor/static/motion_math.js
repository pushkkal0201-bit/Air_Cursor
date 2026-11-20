/* Pure tilt-to-cursor movement helper; usable by browsers and Node tests. */
(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  if (root) root.AirCursorMotion = api;
})(typeof globalThis === "object" ? globalThis : null, function () {
  "use strict";
  function tiltToMovement(current, neutral, sensitivity) {
    if (!current || !neutral) return {dx: 0, dy: 0};
    const values = [current.gamma, current.beta, neutral.gamma, neutral.beta, sensitivity];
    if (!values.every(Number.isFinite) || sensitivity < 0.5 || sensitivity > 5) {
      return {dx: 0, dy: 0};
    }
    function axis(angle) {
      const cutoff = 2.0; // degrees of dead zone; filters hand tremor.
      const amount = Math.max(0, Math.abs(angle) - cutoff);
      const speed = Math.sign(angle) * amount * sensitivity * 0.25;
      return Math.round(Math.max(-28, Math.min(28, speed)));
    }
    return {dx: axis(current.gamma - neutral.gamma),
            dy: axis(current.beta - neutral.beta)};
  }
  return Object.freeze({tiltToMovement});
});
