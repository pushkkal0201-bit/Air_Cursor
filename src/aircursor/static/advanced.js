/* Optional intelligent controls: push-to-talk voice and local accessibility preferences. */
(function () {
  "use strict";
  const byId = id => document.getElementById(id);
  const voiceStatus = byId("voice-status");
  const startButton = byId("voice-start");
  const stopButton = byId("voice-stop");
  const voiceText = byId("voice-last");
  const VoiceEngine = window.SpeechRecognition || window.webkitSpeechRecognition;
  let recognition = null;
  let active = false;

  function note(text, error) {
    voiceStatus.textContent = text;
    voiceStatus.classList.toggle("error", Boolean(error));
  }
  function resetVoice() {
    active = false;
    startButton.disabled = false;
    stopButton.disabled = true;
  }
  function paired() {
    return !byId("dashboard").classList.contains("hidden");
  }
  async function perform(command) {
    if (!paired()) {
      note("Pair this device before using voice commands.", true);
      return;
    }
    if (!command) {
      note("Command not recognized. Try one of the listed phrases.", true);
      return;
    }
    try {
      if (command.kind === "action") {
        await window.fetch("/api/v1/action", {
          method: "POST", credentials: "same-origin",
          headers: {"Content-Type": "application/json", "X-AirCursor-Client": "1"},
          body: JSON.stringify({action: command.value})
        }).then(assertOk);
      } else if (command.kind === "click") {
        await window.fetch("/api/v1/click", {
          method: "POST", credentials: "same-origin",
          headers: {"Content-Type": "application/json", "X-AirCursor-Client": "1"},
          body: JSON.stringify({button: command.value === "double" ? "left" : command.value,
                                count: command.value === "double" ? 2 : 1})
        }).then(assertOk);
      } else if (command.kind === "scroll") {
        await window.fetch("/api/v1/scroll", {
          method: "POST", credentials: "same-origin",
          headers: {"Content-Type": "application/json", "X-AirCursor-Client": "1"},
          body: JSON.stringify({dy: command.value})
        }).then(assertOk);
      }
      note("Executed: " + command.kind + " (" + command.value + ")");
    } catch (error) {
      note("Command failed: " + error.message, true);
    }
  }
  async function assertOk(response) {
    if (!response.ok) throw new Error(response.status === 401 ? "Pairing expired" : "Server rejected command (" + response.status + ")");
    return response;
  }
  if (!VoiceEngine) {
    startButton.disabled = true;
    note("Speech recognition is not supported by this browser. Touch controls remain available.", true);
  }
  startButton.addEventListener("click", () => {
    if (!paired()) {
      note("Pair this device first.", true);
      return;
    }
    if (!window.isSecureContext) {
      note("Voice input requires HTTPS or localhost. Phone access over ordinary LAN HTTP is not supported.", true);
      return;
    }
    if (!VoiceEngine || active) return;
    try {
      recognition = new VoiceEngine();
      recognition.lang = byId("voice-language").value;
      recognition.continuous = false;
      recognition.interimResults = false;
      recognition.maxAlternatives = 1;
      recognition.onresult = event => {
        const transcript = String(event.results[event.resultIndex][0].transcript || "");
        voiceText.textContent = "Heard: " + transcript;
        const command = window.AirCursorVoiceCommands.parse(transcript);
        void perform(command);
      };
      recognition.onerror = event => {
        note("Microphone or recognition error: " + event.error, true);
      };
      recognition.onend = () => {
        resetVoice();
      };
      recognition.start();
      active = true;
      startButton.disabled = true;
      stopButton.disabled = false;
      note("Listening once. Say a supported command.");
    } catch (error) {
      resetVoice();
      note("Cannot start voice input: " + error.message, true);
    }
  });
  stopButton.addEventListener("click", () => {
    if (recognition) recognition.abort();
    resetVoice();
    note("Voice input stopped.");
  });
  document.getElementById("logout").addEventListener("click", () => {
    if (recognition) recognition.abort();
    resetVoice();
    note("Voice input stopped.");
  });
  // A changing paired/unpaired state must never keep a microphone session running.
  new MutationObserver(() => {
    if (!paired() && active) {
      if (recognition) recognition.abort();
      resetVoice();
    }
  }).observe(byId("dashboard"), {attributes: true, attributeFilter: ["class"]});

  const defaults = {profile:"standard", large:false, contrast:false, reduced:false};
  let preferences = {...defaults};
  try {
    const previous = JSON.parse(localStorage.getItem("aircursor-a11y") || "{}");
    if (previous && typeof previous === "object") {
      preferences = {...defaults, ...previous};
    }
  } catch (_) {}

  function applyPreferences() {
    document.documentElement.classList.toggle("large-controls", Boolean(preferences.large));
    document.documentElement.classList.toggle("high-contrast", Boolean(preferences.contrast));
    document.documentElement.classList.toggle("reduced-motion", Boolean(preferences.reduced));
    byId("access-profile").value = ["standard","comfort","precision","presentation"].includes(preferences.profile) ? preferences.profile : "standard";
    for (const [id, prop] of [["large-controls", "large"],["high-contrast","contrast"],["reduced-motion","reduced"]]) {
      const button = byId(id);
      button.setAttribute("aria-pressed", preferences[prop] ? "true" : "false");
      button.textContent = (preferences[prop] ? "✓ " : "") + button.dataset.label;
    }
    try {localStorage.setItem("aircursor-a11y", JSON.stringify(preferences));} catch (_) {}
  }
  byId("access-profile").addEventListener("change", event => {
    const choice = event.target.value;
    preferences.profile = choice;
    preferences.large = ["comfort","presentation"].includes(choice);
    preferences.contrast = choice === "comfort";
    preferences.reduced = choice === "precision";
    const sensitivity = {standard:1.5, comfort:1, precision:0.6, presentation:2.2}[choice];
    if (sensitivity !== undefined) {
      byId("sensitivity").value = String(sensitivity);
      byId("sensitivity").dispatchEvent(new Event("input",{bubbles:true}));
    }
    applyPreferences();
  });
  for (const [id, prop] of [["large-controls","large"],["high-contrast","contrast"],["reduced-motion","reduced"]]) {
    byId(id).addEventListener("click", () => {
      preferences[prop] = !preferences[prop];
      applyPreferences();
    });
  }
  applyPreferences();
})();
