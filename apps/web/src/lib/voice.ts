export type VoiceRecognitionError =
  | "not-allowed"
  | "audio-capture"
  | "no-speech"
  | "network"
  | "aborted"
  | "unknown";

type RecognitionResultEvent = Event & {
  results: ArrayLike<{ 0: { transcript: string }; isFinal: boolean }>;
};

type RecognitionErrorEvent = Event & { error: string };

export interface SpeechRecognitionAdapter {
  continuous: boolean;
  interimResults: boolean;
  lang: string;
  onresult: ((event: RecognitionResultEvent) => void) | null;
  onerror: ((event: RecognitionErrorEvent) => void) | null;
  onend: (() => void) | null;
  start(): void;
  stop(): void;
}

type SpeechRecognitionConstructor = new () => SpeechRecognitionAdapter;
type SpeechUtteranceConstructor = new (text?: string) => SpeechSynthesisUtterance;

type VoiceWindow = Window & {
  SpeechRecognition?: SpeechRecognitionConstructor;
  webkitSpeechRecognition?: SpeechRecognitionConstructor;
  SpeechSynthesisUtterance?: SpeechUtteranceConstructor;
};

export type RecognitionCallbacks = {
  onTranscript: (transcript: string) => void;
  onError: (error: VoiceRecognitionError) => void;
  onEnd: () => void;
};

export function voiceInputSupported(environment: VoiceWindow): boolean {
  return Boolean(
    environment.SpeechRecognition ?? environment.webkitSpeechRecognition,
  );
}

export function createRecognition(
  environment: VoiceWindow,
  callbacks: RecognitionCallbacks,
): SpeechRecognitionAdapter | null {
  const Constructor =
    environment.SpeechRecognition ?? environment.webkitSpeechRecognition;
  if (!Constructor) return null;
  const recognition = new Constructor();
  recognition.continuous = false;
  recognition.interimResults = true;
  recognition.lang = "en-US";
  recognition.onresult = (event) => {
    const transcripts = Array.from(event.results, (result) => result[0].transcript);
    callbacks.onTranscript(transcripts.join(" ").trim());
  };
  recognition.onerror = (event) => {
    const known = ["not-allowed", "audio-capture", "no-speech", "network", "aborted"];
    callbacks.onError(
      known.includes(event.error)
        ? (event.error as VoiceRecognitionError)
        : "unknown",
    );
  };
  recognition.onend = callbacks.onEnd;
  return recognition;
}

export function speak(environment: VoiceWindow, text: string): boolean {
  const Constructor = environment.SpeechSynthesisUtterance;
  if (!("speechSynthesis" in environment) || !Constructor) {
    return false;
  }
  environment.speechSynthesis.cancel();
  const utterance = new Constructor(text);
  utterance.rate = 1;
  utterance.lang = "en-US";
  environment.speechSynthesis.speak(utterance);
  return true;
}

export function stopSpeaking(environment: Window): void {
  environment.speechSynthesis?.cancel();
}
