import assert from "node:assert/strict";
import test from "node:test";

import {
  createRecognition,
  speak,
  stopSpeaking,
  voiceInputSupported,
} from "../src/lib/voice.js";


class FakeRecognition {
  continuous = true;
  interimResults = false;
  lang = "";
  onresult: ((event: never) => void) | null = null;
  onerror: ((event: never) => void) | null = null;
  onend: (() => void) | null = null;
  started = false;
  start() { this.started = true; }
  stop() { this.started = false; }
}


test("voice input support detects standard and prefixed constructors", () => {
  assert.equal(voiceInputSupported({ SpeechRecognition: FakeRecognition } as never), true);
  assert.equal(voiceInputSupported({ webkitSpeechRecognition: FakeRecognition } as never), true);
  assert.equal(voiceInputSupported({} as never), false);
});


test("recognition uses push-to-talk settings and transcript callback", () => {
  let transcript = "";
  const recognition = createRecognition(
    { SpeechRecognition: FakeRecognition } as never,
    { onTranscript: (value) => { transcript = value; }, onError: () => {}, onEnd: () => {} },
  );
  assert.ok(recognition);
  assert.equal(recognition.continuous, false);
  assert.equal(recognition.interimResults, true);
  assert.equal(recognition.lang, "en-US");
  recognition.onresult?.({ results: [{ 0: { transcript: "walkable options" }, isFinal: true }] } as never);
  assert.equal(transcript, "walkable options");
});


test("recognition normalizes unknown errors", () => {
  let error = "";
  const recognition = createRecognition(
    { SpeechRecognition: FakeRecognition } as never,
    { onTranscript: () => {}, onError: (value) => { error = value; }, onEnd: () => {} },
  );
  recognition?.onerror?.({ error: "vendor-specific" } as never);
  assert.equal(error, "unknown");
});


test("speech output cancels old speech and can be stopped", () => {
  const calls: string[] = [];
  class Utterance { rate = 0; lang = ""; constructor(public text = "") {} }
  const environment = {
    SpeechSynthesisUtterance: Utterance,
    speechSynthesis: {
      cancel: () => calls.push("cancel"),
      speak: (utterance: Utterance) => calls.push(`speak:${utterance.text}`),
    },
  } as never;
  assert.equal(speak(environment, "Top result"), true);
  stopSpeaking(environment);
  assert.deepEqual(calls, ["cancel", "speak:Top result", "cancel"]);
});
