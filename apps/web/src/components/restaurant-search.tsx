"use client";

import { FormEvent, useEffect, useRef, useState } from "react";

import {
  CUISINE_OPTIONS,
  STARTING_AREA_OPTIONS,
} from "@/lib/api/restaurants";
import {
  recommendRestaurants,
  RestaurantRecommendation,
  RestaurantRecommendationResponse,
} from "@/lib/api/recommendations";
import {
  ConversationState,
  ConversationResponse,
  followUpConversationSequence,
  initialConversationState,
} from "@/lib/api/conversation";
import {
  Coordinates,
  formatDistance,
  openStreetMapUrl,
  straightLineDistanceKm,
} from "@/lib/location";
import {
  createRecognition,
  speak,
  SpeechRecognitionAdapter,
  stopSpeaking,
  voiceInputSupported,
} from "@/lib/voice";

type SearchFormValues = {
  cuisine: string;
  maximumBudget: string;
  vegetarianRequired: boolean;
  startingArea: string;
  maximumTravelTime: string;
};

type SearchState =
  | { kind: "idle" }
  | { kind: "loading" }
  | { kind: "success"; response: RestaurantRecommendationResponse }
  | { kind: "error"; message: string };

type LocationState =
  | { kind: "idle" }
  | { kind: "loading" }
  | { kind: "success" }
  | { kind: "error"; message: string };

const FOLLOW_UP_SUGGESTIONS = [
  "Only show walkable options",
  "Show me the cheapest one",
  "Most reliable reviews",
  "What are the common complaints?",
] as const;

const SUGGESTED_VALUES: SearchFormValues = {
  cuisine: "",
  maximumBudget: "25",
  vegetarianRequired: true,
  startingArea: "Illinois Tech",
  maximumTravelTime: "30",
};

const EMPTY_VALUES: SearchFormValues = {
  cuisine: "",
  maximumBudget: "",
  vegetarianRequired: false,
  startingArea: "",
  maximumTravelTime: "",
};

function SearchIcon() {
  return (
    <svg
      aria-hidden="true"
      className="size-5"
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
      strokeWidth="2"
    >
      <circle cx="11" cy="11" r="7" />
      <path d="m20 20-3.2-3.2" />
    </svg>
  );
}

function LocationIcon() {
  return (
    <svg
      aria-hidden="true"
      className="size-5"
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
      strokeWidth="2"
    >
      <path d="M12 21s6-5.1 6-12a6 6 0 1 0-12 0c0 6.9 6 12 6 12Z" />
      <circle cx="12" cy="9" r="2" />
    </svg>
  );
}

function RestaurantCard({
  restaurant,
  currentLocation,
  displayRank,
}: {
  restaurant: RestaurantRecommendation;
  currentLocation: Coordinates | null;
  displayRank: number;
}) {
  const travelMode = restaurant.travel?.selected_mode.replace("_", " ");
  const coordinates = {
    latitude: restaurant.latitude,
    longitude: restaurant.longitude,
  };
  const distance =
    currentLocation === null
      ? null
      : straightLineDistanceKm(currentLocation, coordinates);

  return (
    <article className="group flex h-full flex-col overflow-hidden rounded-[1.75rem] border border-stone-200 bg-white shadow-[0_14px_40px_rgba(66,45,32,0.07)] transition duration-200 hover:-translate-y-1 hover:border-orange-200 hover:shadow-[0_22px_50px_rgba(66,45,32,0.12)]">
      <div className="flex items-start justify-between gap-4 border-b border-stone-100 bg-gradient-to-br from-orange-50/80 to-white px-5 py-5">
        <div className="min-w-0">
          <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-[0.14em] text-orange-700">
            <span>#{displayRank}</span>
            <span aria-hidden="true">·</span>
            <span>Demo {restaurant.cuisine}</span>
          </div>
          <h3 className="mt-1 text-xl font-bold tracking-[-0.025em] text-stone-950">
            {restaurant.name}
          </h3>
          <p className="mt-1 text-sm font-medium text-stone-600">
            {restaurant.neighborhood}
          </p>
          <a
            href={openStreetMapUrl(coordinates)}
            target="_blank"
            rel="noreferrer"
            className="mt-2 inline-flex max-w-full items-start gap-1.5 text-left text-xs leading-5 text-stone-500 underline decoration-stone-300 underline-offset-4 transition hover:text-orange-800 hover:decoration-orange-400"
          >
            <LocationIcon />
            <span>{restaurant.address}</span>
          </a>
        </div>
        <div className="shrink-0 text-right">
          <p className="text-2xl font-black tracking-tight text-stone-950">
            {restaurant.total_score.toFixed(1)}
          </p>
          <p className="text-[0.65rem] font-bold uppercase tracking-wider text-stone-500">
            match score
          </p>
        </div>
      </div>

      <div className="flex flex-1 flex-col p-5">
        {restaurant.categories.length > 0 && (
          <ul className="flex flex-wrap gap-2" aria-label="Recommendation labels">
            {restaurant.categories.map((badge) => (
              <li
                key={badge.category}
                className={`rounded-full px-3 py-1.5 text-xs font-bold ${
                  badge.category === "mixed_reviews"
                    ? "bg-amber-100 text-amber-900"
                    : "bg-orange-100 text-orange-900"
                }`}
              >
                {badge.label}
              </li>
            ))}
          </ul>
        )}

        <dl className="mt-5 grid grid-cols-3 gap-2">
          <div className="rounded-xl bg-stone-50 p-3">
            <dt className="text-xs font-semibold text-orange-800">Demo cost</dt>
            <dd className="mt-1 font-bold text-stone-950">
              ${restaurant.estimated_cost_per_person} {restaurant.price_category}
            </dd>
          </div>
          <div className="rounded-xl bg-amber-50 p-3">
            <dt className="text-xs font-semibold text-amber-800">Demo rating</dt>
            <dd className="mt-1 font-bold text-stone-950">
              <span className="text-amber-500" aria-hidden="true">★</span>{" "}
              {restaurant.rating.toFixed(1)}
            </dd>
          </div>
          <div className="rounded-xl bg-emerald-50 p-3">
            <dt className="text-xs font-semibold text-emerald-800">Demo confidence</dt>
            <dd className="mt-1 font-bold text-stone-950">
              {restaurant.review_confidence_score.toFixed(0)}%
            </dd>
          </div>
        </dl>

        <div className="mt-4 flex flex-wrap gap-2 text-xs font-semibold">
          {restaurant.vegetarian_available && (
            <span className="rounded-full bg-emerald-50 px-3 py-1.5 text-emerald-800">
              Demo vegetarian options
            </span>
          )}
          {restaurant.vegan_available && (
            <span className="rounded-full bg-teal-50 px-3 py-1.5 text-teal-800">
              Demo vegan options
            </span>
          )}
        </div>

        {distance !== null && (
          <div className="mt-5 flex items-center justify-between rounded-xl border border-violet-100 bg-violet-50/80 p-4">
            <div>
              <p className="text-xs font-bold uppercase tracking-wider text-violet-700">
                From your location
              </p>
              <p className="mt-1 text-xs text-violet-700">
                Straight-line distance · not travel time
              </p>
            </div>
            <p className="text-xl font-black text-violet-950">
              {formatDistance(distance)}
            </p>
          </div>
        )}

        <div className="mt-5 rounded-xl border border-emerald-100 bg-emerald-50/70 p-4 text-sm">
          <div className="flex items-center justify-between gap-3">
            <span className="font-semibold text-emerald-950">
              Latest City inspection
            </span>
            <span className="rounded-full bg-white px-2.5 py-1 text-xs font-bold text-emerald-800">
              {restaurant.latest_inspection.result}
            </span>
          </div>
          <p className="mt-2 text-xs text-emerald-800">
            {restaurant.latest_inspection.inspection_date} · Fixed public-data
            snapshot, not a current safety guarantee
          </p>
        </div>

        {restaurant.travel && (
          <div className="mt-5 rounded-xl border border-sky-100 bg-sky-50/70 p-4 text-sm">
            <div className="flex items-center justify-between gap-3">
              <span className="capitalize font-semibold text-sky-900">
                {travelMode} from {restaurant.travel.starting_area}
              </span>
              <span className="font-black text-sky-950">
                {restaurant.travel.selected_minutes} min
              </span>
            </div>
            <p className="mt-2 text-xs text-sky-800">
              Walk {restaurant.travel.walking_minutes} · Transit{" "}
              {restaurant.travel.public_transit_minutes} · Drive{" "}
              {restaurant.travel.driving_minutes} min
            </p>
          </div>
        )}

        <div className="mt-5 grid gap-4 border-t border-stone-100 pt-5 sm:grid-cols-2">
          <div>
            <h4 className="text-xs font-bold uppercase tracking-wider text-emerald-800">
              Review strengths
            </h4>
            <ul className="mt-2 space-y-1.5 text-sm text-stone-700">
              {restaurant.top_positive_themes.map((theme) => (
                <li key={theme.theme}>+ {theme.label} ({theme.mention_count})</li>
              ))}
            </ul>
          </div>
          <div>
            <h4 className="text-xs font-bold uppercase tracking-wider text-rose-800">
              Common concerns
            </h4>
            <ul className="mt-2 space-y-1.5 text-sm text-stone-700">
              {restaurant.top_negative_themes.map((theme) => (
                <li key={theme.theme}>− {theme.label} ({theme.mention_count})</li>
              ))}
            </ul>
          </div>
        </div>

        <div className="mt-5 rounded-xl bg-stone-950 p-4 text-sm text-stone-100">
          <p className="font-bold">Why it ranks here</p>
          <p className="mt-1 leading-6 text-stone-300">
            {restaurant.ranking_explanation}
          </p>
        </div>

        {restaurant.categories.length > 0 && (
          <details className="mt-4 text-sm">
            <summary className="cursor-pointer font-bold text-orange-800 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-orange-600">
              Why these labels?
            </summary>
            <ul className="mt-3 space-y-2 text-stone-600">
              {restaurant.categories.map((badge) => (
                <li key={badge.category}>
                  <span className="font-semibold text-stone-900">{badge.label}:</span>{" "}
                  {badge.reason}
                </li>
              ))}
            </ul>
          </details>
        )}

        <div className="mt-auto border-t border-stone-100 pt-4 text-xs text-stone-500">
          <p>{restaurant.data_freshness_label}</p>
          <p className="mt-1">Address and coordinates: City of Chicago data</p>
        </div>
      </div>
    </article>
  );
}

function ResultSummary({
  response,
}: {
  response: RestaurantRecommendationResponse;
}) {
  const filters = response.filters;
  const filterLabels = [
    filters.cuisine,
    filters.maximum_budget === null
      ? null
      : `Up to $${filters.maximum_budget}`,
    filters.vegetarian_required ? "Demo vegetarian flag" : null,
    filters.starting_area,
    filters.maximum_travel_time === null
      ? null
      : `Within ${filters.maximum_travel_time} min`,
  ].filter((label): label is string => label !== null);

  return (
    <div className="flex flex-col justify-between gap-5 sm:flex-row sm:items-end">
      <div>
        <p className="text-sm font-bold uppercase tracking-[0.18em] text-orange-700">
          Your matches
        </p>
        <h2 className="mt-2 text-3xl font-bold tracking-[-0.035em] text-stone-950 sm:text-4xl">
          {response.match_count === 0
            ? "No exact matches yet"
            : `${response.match_count} ${response.match_count === 1 ? "place" : "places"} fit your search`}
        </h2>
        <p className="mt-2 text-sm text-stone-500">
          Ranked with travel, review themes, and explainable evidence confidence.
        </p>
      </div>

      {filterLabels.length > 0 && (
        <ul className="flex max-w-xl flex-wrap gap-2" aria-label="Applied filters">
          {filterLabels.map((label) => (
            <li
              key={label}
              className="rounded-full border border-stone-200 bg-white px-3 py-1.5 text-xs font-semibold text-stone-700"
            >
              {label}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export function RestaurantSearch({
  backendConnected,
}: {
  backendConnected: boolean;
}) {
  const [values, setValues] = useState<SearchFormValues>(SUGGESTED_VALUES);
  const [state, setState] = useState<SearchState>({ kind: "idle" });
  const [conversationState, setConversationState] =
    useState<ConversationState | null>(null);
  const [followUpMessage, setFollowUpMessage] = useState("");
  const [selectedFollowUps, setSelectedFollowUps] = useState<string[]>([]);
  const [followUpStatus, setFollowUpStatus] = useState<
    | { kind: "idle" }
    | { kind: "loading" }
    | { kind: "success"; message: string }
    | { kind: "error"; message: string }
  >({ kind: "idle" });
  const resultsRef = useRef<HTMLElement>(null);
  const recognitionRef = useRef<SpeechRecognitionAdapter | null>(null);
  const [voiceInputAvailable, setVoiceInputAvailable] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [voiceOutputEnabled, setVoiceOutputEnabled] = useState(false);
  const [voiceMessage, setVoiceMessage] = useState<string | null>(null);
  const [currentLocation, setCurrentLocation] = useState<Coordinates | null>(
    null,
  );
  const [locationState, setLocationState] = useState<LocationState>({
    kind: "idle",
  });
  const [sortByDistance, setSortByDistance] = useState(false);

  useEffect(() => {
    const supportCheck = window.setTimeout(
      () => setVoiceInputAvailable(voiceInputSupported(window)),
      0,
    );
    return () => {
      window.clearTimeout(supportCheck);
      recognitionRef.current?.stop();
      stopSpeaking(window);
    };
  }, []);

  useEffect(() => {
    if (state.kind === "success" || state.kind === "error") {
      resultsRef.current?.focus();
    }
  }, [state]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setState({ kind: "loading" });

    try {
      const response = await recommendRestaurants({
        cuisine: values.cuisine || undefined,
        maximumBudget: values.maximumBudget
          ? Number(values.maximumBudget)
          : undefined,
        vegetarianRequired: values.vegetarianRequired,
        startingArea: values.startingArea || undefined,
        maximumTravelTime: values.maximumTravelTime
          ? Number(values.maximumTravelTime)
          : undefined,
      });
      setState({ kind: "success", response });
      setConversationState(initialConversationState(response.filters));
      setFollowUpStatus({ kind: "idle" });
      setSelectedFollowUps([]);
    } catch (error) {
      setState({
        kind: "error",
        message:
          error instanceof Error
            ? error.message
            : "BiteCheck could not complete this search.",
      });
    }
  }

  function clearFilters() {
    setValues(EMPTY_VALUES);
    setState({ kind: "idle" });
    setConversationState(null);
    setFollowUpMessage("");
    setSelectedFollowUps([]);
    setFollowUpStatus({ kind: "idle" });
    setCurrentLocation(null);
    setLocationState({ kind: "idle" });
    setSortByDistance(false);
  }

  function requestCurrentLocation() {
    if (!("geolocation" in navigator)) {
      setLocationState({
        kind: "error",
        message: "Location is unavailable in this browser.",
      });
      return;
    }

    setLocationState({ kind: "loading" });
    navigator.geolocation.getCurrentPosition(
      (position) => {
        setCurrentLocation({
          latitude: position.coords.latitude,
          longitude: position.coords.longitude,
        });
        setLocationState({ kind: "success" });
        setSortByDistance(true);
      },
      (error) => {
        const message =
          error.code === error.PERMISSION_DENIED
            ? "Location permission was not granted. Preset areas still work."
            : "Your location could not be read. Try again or use a preset area.";
        setLocationState({ kind: "error", message });
      },
      { enableHighAccuracy: false, timeout: 10_000, maximumAge: 300_000 },
    );
  }

  function applyConversationResponse(
    response: ConversationResponse,
    statusMessage: string,
  ) {
    setConversationState(response.state);
    setState({ kind: "success", response: response.results });
    setFollowUpStatus({ kind: "success", message: statusMessage });
    const filters = response.state.filters;
    setValues({
      cuisine: filters.cuisine ?? "",
      maximumBudget:
        filters.maximum_budget === null ? "" : String(filters.maximum_budget),
      vegetarianRequired: filters.vegetarian_required,
      startingArea: filters.starting_area ?? "",
      maximumTravelTime:
        filters.maximum_travel_time === null
          ? ""
          : String(filters.maximum_travel_time),
    });

    if (voiceOutputEnabled) {
      const top = response.results.recommendations[0];
      const summary =
        top === undefined
          ? "No restaurants match the updated request."
          : `${statusMessage} The top result is ${top.name} with a match score of ${top.total_score.toFixed(1)}.`;
      if (!speak(window, summary)) {
        setVoiceMessage("Speech output is unavailable in this browser.");
      }
    }
  }

  async function applyFollowUps(messages: string[]) {
    if (conversationState === null || messages.length === 0) return;
    setFollowUpStatus({ kind: "loading" });

    try {
      const sequence = await followUpConversationSequence(
        messages,
        conversationState,
      );
      applyConversationResponse(sequence.response, sequence.explanation);
      setFollowUpMessage("");
      setSelectedFollowUps([]);
    } catch (error) {
      setFollowUpStatus({
        kind: "error",
        message:
          error instanceof Error
            ? error.message
            : "BiteCheck could not apply those follow-ups.",
      });
    }
  }

  async function handleFollowUp(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const message = followUpMessage.trim();
    if (!message) return;
    await applyFollowUps([message]);
  }

  function toggleFollowUp(suggestion: string) {
    setSelectedFollowUps((current) =>
      current.includes(suggestion)
        ? current.filter((item) => item !== suggestion)
        : [...current, suggestion],
    );
  }

  function startListening() {
    setVoiceMessage(null);
    const recognition = createRecognition(window, {
      onTranscript: setFollowUpMessage,
      onError: (error) => {
        setIsListening(false);
        setVoiceMessage(
          error === "not-allowed"
            ? "Microphone access was not granted. You can keep typing instead."
            : error === "no-speech"
              ? "No speech was detected. Try again or type the request."
              : "Voice input stopped. You can retry or use text input.",
        );
      },
      onEnd: () => setIsListening(false),
    });
    if (recognition === null) {
      setVoiceMessage("Voice input is unsupported here. Text input still works.");
      return;
    }
    recognitionRef.current = recognition;
    setIsListening(true);
    try {
      recognition.start();
    } catch {
      setIsListening(false);
      setVoiceMessage("Voice input could not start. Text input still works.");
    }
  }

  const displayedRecommendations =
    state.kind === "success" && currentLocation !== null && sortByDistance
      ? [...state.response.recommendations].sort(
          (left, right) =>
            straightLineDistanceKm(currentLocation, {
              latitude: left.latitude,
              longitude: left.longitude,
            }) -
            straightLineDistanceKm(currentLocation, {
              latitude: right.latitude,
              longitude: right.longitude,
            }),
        )
      : state.kind === "success"
        ? state.response.recommendations
        : [];

  return (
    <>
      <section className="relative isolate overflow-hidden">
        <div
          aria-hidden="true"
          className="absolute -left-28 top-8 -z-10 size-80 rounded-full bg-orange-200/35 blur-3xl"
        />
        <div
          aria-hidden="true"
          className="absolute -right-24 bottom-0 -z-10 size-96 rounded-full bg-emerald-200/25 blur-3xl"
        />
        <div className="mx-auto grid max-w-7xl gap-8 px-5 pb-12 pt-8 sm:px-8 lg:grid-cols-[0.8fr_1.2fr] lg:items-center lg:px-10 lg:pb-16 lg:pt-12">
          <div className="py-3 lg:pr-8">
          <div className="flex items-center gap-3">
            <span className="rounded-full bg-orange-100 px-3 py-1.5 text-xs font-bold uppercase tracking-[0.16em] text-orange-800">
              Chicago preview
            </span>
            <span
              className={`flex items-center gap-2 text-xs font-semibold ${
                backendConnected ? "text-emerald-700" : "text-amber-700"
              }`}
            >
              <span
                aria-hidden="true"
                className={`size-2 rounded-full ${
                  backendConnected ? "bg-emerald-500" : "bg-amber-500"
                }`}
              />
              {backendConnected ? "Search service online" : "Service reconnecting"}
            </span>
          </div>

          <h1 className="mt-6 max-w-2xl text-5xl font-bold leading-[0.98] tracking-[-0.055em] text-stone-950 sm:text-6xl lg:text-7xl">
            Your next meal,
            <span className="block font-serif font-normal italic text-orange-700">
              minus the guesswork.
            </span>
          </h1>
          <p className="mt-6 max-w-xl text-lg leading-8 text-stone-600">
            Shape a search around your budget, dietary needs, and starting
            point. BiteCheck checks every selected preference together.
          </p>

          <div className="mt-8 flex flex-wrap gap-x-6 gap-y-3 text-sm font-semibold text-stone-600">
            <span>24 real Chicago establishments</span>
            <span>Your location stays in the browser</span>
            <span>No paid APIs</span>
          </div>
          </div>

          <form
            onSubmit={handleSubmit}
            className="rounded-[2rem] border border-white/80 bg-white/90 p-5 shadow-[0_25px_70px_rgba(66,45,32,0.14)] backdrop-blur sm:p-7"
          >
          <div className="flex items-start justify-between gap-4 border-b border-stone-100 pb-5">
            <div>
              <p className="text-xs font-bold uppercase tracking-[0.16em] text-orange-700">
                Personalize your search
              </p>
              <h2 className="mt-1 text-2xl font-bold tracking-tight text-stone-950">
                What sounds good today?
              </h2>
            </div>
            <button
              type="button"
              onClick={clearFilters}
              className="rounded-full px-3 py-2 text-sm font-semibold text-stone-500 transition hover:bg-stone-100 hover:text-stone-900 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-orange-600"
            >
              Clear
            </button>
          </div>

          <div className="mt-6 grid gap-5 sm:grid-cols-2">
            <label className="grid gap-2 text-sm font-bold text-stone-800">
              Demo cuisine category
              <select
                name="cuisine"
                value={values.cuisine}
                onChange={(event) =>
                  setValues((current) => ({
                    ...current,
                    cuisine: event.target.value,
                  }))
                }
                className="h-12 rounded-xl border border-stone-200 bg-stone-50 px-3 font-medium text-stone-900 outline-none transition focus:border-orange-500 focus:ring-3 focus:ring-orange-100"
              >
                <option value="">Any demo cuisine</option>
                {CUISINE_OPTIONS.map((cuisine) => (
                  <option key={cuisine} value={cuisine}>
                    {cuisine}
                  </option>
                ))}
              </select>
            </label>

            <label className="grid gap-2 text-sm font-bold text-stone-800">
              Maximum budget per person
              <div className="relative">
                <span className="pointer-events-none absolute inset-y-0 left-3 grid place-items-center font-semibold text-stone-500">
                  $
                </span>
                <input
                  name="maximum_budget"
                  type="number"
                  min="1"
                  inputMode="numeric"
                  value={values.maximumBudget}
                  onChange={(event) =>
                    setValues((current) => ({
                      ...current,
                      maximumBudget: event.target.value,
                    }))
                  }
                  placeholder="No limit"
                  className="h-12 w-full rounded-xl border border-stone-200 bg-stone-50 pl-8 pr-3 font-medium text-stone-900 outline-none transition placeholder:text-stone-400 focus:border-orange-500 focus:ring-3 focus:ring-orange-100"
                />
              </div>
            </label>

            <label className="grid gap-2 text-sm font-bold text-stone-800">
              Starting area
              <select
                name="starting_area"
                value={values.startingArea}
                onChange={(event) => {
                  const startingArea = event.target.value;
                  setValues((current) => ({
                    ...current,
                    startingArea,
                    maximumTravelTime: startingArea
                      ? current.maximumTravelTime
                      : "",
                  }));
                }}
                className="h-12 rounded-xl border border-stone-200 bg-stone-50 px-3 font-medium text-stone-900 outline-none transition focus:border-orange-500 focus:ring-3 focus:ring-orange-100"
              >
                <option value="">Anywhere in the dataset</option>
                {STARTING_AREA_OPTIONS.map((area) => (
                  <option key={area} value={area}>
                    {area}
                  </option>
                ))}
              </select>
            </label>

            <label className="grid gap-2 text-sm font-bold text-stone-800">
              Maximum travel time
              <div className="relative">
                <input
                  name="maximum_travel_time"
                  type="number"
                  min="1"
                  inputMode="numeric"
                  value={values.maximumTravelTime}
                  disabled={!values.startingArea}
                  onChange={(event) =>
                    setValues((current) => ({
                      ...current,
                      maximumTravelTime: event.target.value,
                    }))
                  }
                  placeholder={values.startingArea ? "No limit" : "Choose an area first"}
                  className="h-12 w-full rounded-xl border border-stone-200 bg-stone-50 px-3 pr-14 font-medium text-stone-900 outline-none transition placeholder:text-stone-400 focus:border-orange-500 focus:ring-3 focus:ring-orange-100 disabled:cursor-not-allowed disabled:bg-stone-100 disabled:text-stone-400"
                />
                <span className="pointer-events-none absolute inset-y-0 right-3 grid place-items-center text-sm font-medium text-stone-500">
                  min
                </span>
              </div>
            </label>
          </div>

          <label className="mt-5 flex cursor-pointer items-center gap-3 rounded-xl border border-emerald-100 bg-emerald-50/70 p-4 text-sm font-semibold text-emerald-950">
            <input
              name="vegetarian_required"
              type="checkbox"
              checked={values.vegetarianRequired}
              onChange={(event) =>
                setValues((current) => ({
                  ...current,
                  vegetarianRequired: event.target.checked,
                }))
              }
              className="size-5 accent-emerald-700"
            />
            Require the demo vegetarian flag
          </label>

          <div className="mt-5 rounded-2xl border border-violet-100 bg-gradient-to-r from-violet-50 to-sky-50 p-4">
            <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <p className="flex items-center gap-2 font-bold text-violet-950">
                  <LocationIcon />
                  Distance from where you are
                </p>
                <p className="mt-1 text-xs leading-5 text-violet-700">
                  Optional and browser-only. Shows straight-line distance to
                  these 24 Chicago records.
                </p>
              </div>
              <button
                type="button"
                onClick={requestCurrentLocation}
                disabled={locationState.kind === "loading"}
                className="shrink-0 rounded-xl border border-violet-200 bg-white px-4 py-2.5 text-sm font-bold text-violet-900 shadow-sm transition hover:-translate-y-0.5 hover:border-violet-400 hover:shadow disabled:cursor-wait disabled:text-violet-400"
              >
                {locationState.kind === "loading"
                  ? "Locating…"
                  : currentLocation === null
                    ? "Use my location"
                    : "Refresh location"}
              </button>
            </div>
            {locationState.kind === "success" && (
              <p className="mt-3 text-xs font-semibold text-emerald-700" role="status">
                Location ready. Results can now be ordered by nearest distance.
              </p>
            )}
            {locationState.kind === "error" && (
              <p className="mt-3 text-xs font-semibold text-red-700" role="alert">
                {locationState.message}
              </p>
            )}
          </div>

          <button
            type="submit"
            disabled={state.kind === "loading"}
            className="mt-6 flex h-13 w-full items-center justify-center gap-2 rounded-xl bg-stone-950 px-5 font-bold text-white shadow-lg shadow-stone-900/10 transition hover:bg-orange-700 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-orange-600 disabled:cursor-wait disabled:bg-stone-500"
          >
            {state.kind === "loading" ? (
              <>
                <span
                  aria-hidden="true"
                  className="size-4 animate-spin rounded-full border-2 border-white/40 border-t-white"
                />
                Building your recommendations…
              </>
            ) : (
              <>
                <SearchIcon />
                Build my recommendations
              </>
            )}
          </button>
          </form>
        </div>
      </section>

      <section
        id="search-results"
        ref={resultsRef}
        tabIndex={-1}
        aria-live="polite"
        aria-busy={state.kind === "loading"}
        className="border-t border-stone-200 bg-stone-100/80 outline-none"
      >
        <div className="mx-auto max-w-7xl px-5 py-12 sm:px-8 lg:px-10 lg:py-16">
          {state.kind === "idle" && (
            <div className="rounded-[1.75rem] border border-dashed border-stone-300 bg-white/60 px-6 py-12 text-center">
              <p className="text-lg font-bold text-stone-900">
                Your shortlist will appear here.
              </p>
              <p className="mx-auto mt-2 max-w-xl text-sm leading-6 text-stone-500">
                The suggested preferences are ready to search, or clear them to
                browse all 24 establishments in the City-data snapshot.
              </p>
            </div>
          )}

          {state.kind === "loading" && (
            <div>
              <div className="h-10 w-72 animate-pulse rounded-xl bg-stone-200" />
              <div className="mt-8 grid gap-5 md:grid-cols-2 xl:grid-cols-3">
                {[1, 2, 3].map((item) => (
                  <div
                    key={item}
                    className="h-80 animate-pulse rounded-[1.5rem] border border-stone-200 bg-white"
                  />
                ))}
              </div>
            </div>
          )}

          {state.kind === "error" && (
            <div className="rounded-[1.75rem] border border-red-200 bg-red-50 px-6 py-10 text-center">
              <p className="text-lg font-bold text-red-950">
                We couldn&apos;t finish that search.
              </p>
              <p className="mt-2 text-sm text-red-800">{state.message}</p>
            </div>
          )}

          {state.kind === "success" && (
            <div>
              <ResultSummary response={state.response} />
              <p className="mt-4 max-w-3xl text-xs leading-5 text-stone-500">
                {state.response.data_notice}
              </p>

              {currentLocation !== null && state.response.match_count > 0 && (
                <div className="mt-5 flex flex-col gap-3 rounded-2xl border border-violet-100 bg-white p-4 shadow-sm sm:flex-row sm:items-center sm:justify-between">
                  <div>
                    <p className="font-bold text-stone-950">Current-location view</p>
                    <p className="mt-1 text-xs text-stone-500">
                      Your coordinates stay in this browser and are used only
                      for straight-line distance.
                    </p>
                  </div>
                  <div
                    className="inline-flex rounded-xl bg-stone-100 p-1"
                    aria-label="Result ordering"
                  >
                    <button
                      type="button"
                      aria-pressed={!sortByDistance}
                      onClick={() => setSortByDistance(false)}
                      className={`rounded-lg px-3 py-2 text-xs font-bold transition ${
                        !sortByDistance
                          ? "bg-white text-stone-950 shadow-sm"
                          : "text-stone-500 hover:text-stone-900"
                      }`}
                    >
                      Match score
                    </button>
                    <button
                      type="button"
                      aria-pressed={sortByDistance}
                      onClick={() => setSortByDistance(true)}
                      className={`rounded-lg px-3 py-2 text-xs font-bold transition ${
                        sortByDistance
                          ? "bg-violet-700 text-white shadow-sm"
                          : "text-stone-500 hover:text-stone-900"
                      }`}
                    >
                      Nearest to me
                    </button>
                  </div>
                </div>
              )}

              {conversationState !== null && state.response.match_count > 0 && (
                <form
                  onSubmit={handleFollowUp}
                  className="mt-6 rounded-[1.5rem] border border-orange-200 bg-orange-50/70 p-5"
                >
                  <div className="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
                    <div>
                      <p className="text-xs font-bold uppercase tracking-[0.16em] text-orange-800">
                        Refine this result
                      </p>
                      <h3 className="mt-1 text-xl font-bold text-stone-950">
                        Stack follow-up actions
                      </h3>
                    </div>
                    <p className="text-xs text-stone-600">
                      Select several · applied in selection order
                    </p>
                  </div>
                  <div className="mt-4 flex flex-col gap-3 sm:flex-row">
                    <label className="sr-only" htmlFor="follow-up-message">
                      Follow-up request
                    </label>
                    <input
                      id="follow-up-message"
                      value={followUpMessage}
                      onChange={(event) => setFollowUpMessage(event.target.value)}
                      placeholder="Try: Only show walkable options"
                      className="h-12 min-w-0 flex-1 rounded-xl border border-orange-200 bg-white px-4 text-stone-950 outline-none focus:border-orange-500 focus:ring-3 focus:ring-orange-100"
                    />
                    <button
                      type="submit"
                      disabled={followUpStatus.kind === "loading"}
                      className="h-12 rounded-xl bg-orange-700 px-5 font-bold text-white transition hover:bg-orange-800 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-orange-600 disabled:cursor-wait disabled:bg-orange-400"
                    >
                      {followUpStatus.kind === "loading"
                        ? "Updating…"
                        : "Apply typed request"}
                    </button>
                  </div>
                  <fieldset className="mt-4">
                    <legend className="text-xs font-bold uppercase tracking-wider text-orange-900">
                      Quick actions
                    </legend>
                    <div className="mt-2 flex flex-wrap gap-2">
                      {FOLLOW_UP_SUGGESTIONS.map((suggestion) => {
                        const selected =
                          selectedFollowUps.includes(suggestion);
                        const unavailable =
                          suggestion === "Only show walkable options" &&
                          conversationState.filters.starting_area === null;
                        return (
                          <button
                            key={suggestion}
                            type="button"
                            aria-pressed={selected}
                            disabled={unavailable}
                            onClick={() => toggleFollowUp(suggestion)}
                            className={`rounded-full border px-3 py-2 text-xs font-semibold transition disabled:cursor-not-allowed disabled:opacity-45 ${
                              selected
                                ? "border-orange-700 bg-orange-700 text-white shadow-sm"
                                : "border-orange-200 bg-white text-orange-900 hover:-translate-y-0.5 hover:border-orange-400 hover:shadow-sm"
                            }`}
                          >
                            {selected ? "✓ " : "+ "}
                            {suggestion}
                          </button>
                        );
                      })}
                    </div>
                  </fieldset>

                  <div className="mt-4 flex flex-wrap items-center gap-3 border-t border-orange-200/70 pt-4">
                    <button
                      type="button"
                      disabled={
                        selectedFollowUps.length === 0 ||
                        followUpStatus.kind === "loading"
                      }
                      onClick={() => void applyFollowUps(selectedFollowUps)}
                      className="rounded-xl bg-stone-950 px-4 py-2.5 text-sm font-bold text-white shadow-sm transition hover:-translate-y-0.5 hover:bg-orange-800 hover:shadow disabled:cursor-not-allowed disabled:bg-stone-300"
                    >
                      {selectedFollowUps.length === 0
                        ? "Select quick actions"
                        : `Apply ${selectedFollowUps.length} selected`}
                    </button>
                    {selectedFollowUps.length > 0 && (
                      <button
                        type="button"
                        onClick={() => setSelectedFollowUps([])}
                        className="text-xs font-bold text-stone-500 underline underline-offset-4 hover:text-stone-900"
                      >
                        Clear selection
                      </button>
                    )}
                    <span className="hidden h-6 w-px bg-orange-200 sm:block" />
                    <button
                      type="button"
                      onClick={startListening}
                      disabled={!voiceInputAvailable || isListening}
                      className="rounded-full border border-orange-200 bg-white px-3 py-1.5 text-xs font-semibold text-orange-900 hover:border-orange-400 disabled:cursor-not-allowed disabled:text-stone-400"
                    >
                      {isListening ? "Listening…" : "Push to talk"}
                    </button>
                    <button
                      type="button"
                      aria-pressed={voiceOutputEnabled}
                      onClick={() => {
                        const next = !voiceOutputEnabled;
                        setVoiceOutputEnabled(next);
                        if (!next) stopSpeaking(window);
                      }}
                      className="rounded-full border border-orange-200 bg-white px-3 py-1.5 text-xs font-semibold text-orange-900 hover:border-orange-400"
                    >
                      Spoken replies: {voiceOutputEnabled ? "on" : "off"}
                    </button>
                    <button
                      type="button"
                      onClick={() => stopSpeaking(window)}
                      className="rounded-full border border-orange-200 bg-white px-3 py-1.5 text-xs font-semibold text-orange-900 hover:border-orange-400"
                    >
                      Stop speaking
                    </button>
                  </div>
                  {!voiceInputAvailable && (
                    <p className="mt-3 text-xs text-stone-600">
                      Voice input is not supported by this browser. The complete text fallback is available.
                    </p>
                  )}
                  {voiceMessage && (
                    <p className="mt-3 text-sm font-semibold text-amber-800" role="status">
                      {voiceMessage}
                    </p>
                  )}
                  {followUpStatus.kind === "success" && (
                    <p className="mt-3 text-sm font-semibold text-emerald-800" role="status">
                      {followUpStatus.message}
                    </p>
                  )}
                  {followUpStatus.kind === "error" && (
                    <p className="mt-3 text-sm font-semibold text-red-800" role="alert">
                      {followUpStatus.message}
                    </p>
                  )}
                </form>
              )}

              {state.response.match_count === 0 ? (
                <div className="mt-8 rounded-[1.75rem] border border-dashed border-stone-300 bg-white px-6 py-12 text-center">
                  <p className="text-lg font-bold text-stone-900">
                    Try widening one preference.
                  </p>
                  <p className="mx-auto mt-2 max-w-xl text-sm leading-6 text-stone-500">
                    A higher budget, longer travel time, or another cuisine may
                    reveal more options. Your request was valid—nothing in this
                    small dataset matched every filter together.
                  </p>
                </div>
              ) : (
                <div className="mt-8 grid gap-5 md:grid-cols-2 xl:grid-cols-3">
                  {displayedRecommendations.map((restaurant, index) => (
                    <RestaurantCard
                      key={restaurant.restaurant_id}
                      restaurant={restaurant}
                      currentLocation={currentLocation}
                      displayRank={index + 1}
                    />
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </section>
    </>
  );
}
