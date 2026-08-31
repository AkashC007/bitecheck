import {
  parseRestaurantRecommendationResponse,
  RestaurantRecommendationResponse,
} from "./recommendations";
import type { AppliedRestaurantSearchFilters } from "./restaurants.js";

export type ConversationState = {
  filters: AppliedRestaurantSearchFilters;
  sort_mode: "weighted" | "cheapest" | "preferred_theme" | "review_confidence";
  travel_preference: "any" | "walkable";
  theme_preference: "vegetarian_options" | "authenticity" | null;
  result_limit: number | null;
};

export type ConversationResponse = {
  intent: string;
  state: ConversationState;
  transition_explanation: string;
  candidate_count_before_limit: number;
  results: RestaurantRecommendationResponse;
};

const TIMEOUT_MS = 8_000;

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function isState(value: unknown): value is ConversationState {
  if (!isRecord(value) || !isRecord(value.filters)) return false;
  const filters = value.filters;
  return (
    (filters.cuisine === null || typeof filters.cuisine === "string") &&
    (filters.maximum_budget === null ||
      typeof filters.maximum_budget === "number") &&
    typeof filters.vegetarian_required === "boolean" &&
    (filters.starting_area === null || typeof filters.starting_area === "string") &&
    (filters.maximum_travel_time === null ||
      typeof filters.maximum_travel_time === "number") &&
    typeof value.sort_mode === "string" &&
    (value.travel_preference === "any" ||
      value.travel_preference === "walkable") &&
    (value.theme_preference === null ||
      value.theme_preference === "vegetarian_options" ||
      value.theme_preference === "authenticity") &&
    (value.result_limit === null || typeof value.result_limit === "number")
  );
}

export function parseConversationResponse(
  value: unknown,
): ConversationResponse | null {
  if (!isRecord(value)) return null;
  const results = parseRestaurantRecommendationResponse(value.results);
  if (
    typeof value.intent !== "string" ||
    !isState(value.state) ||
    typeof value.transition_explanation !== "string" ||
    typeof value.candidate_count_before_limit !== "number" ||
    results === null
  ) {
    return null;
  }
  return { ...value, results } as ConversationResponse;
}

export function initialConversationState(
  filters: AppliedRestaurantSearchFilters,
): ConversationState {
  return {
    filters,
    sort_mode: "weighted",
    travel_preference: "any",
    theme_preference: null,
    result_limit: null,
  };
}

export async function followUpConversation(
  message: string,
  state: ConversationState,
): Promise<ConversationResponse> {
  let response: Response;
  try {
    response = await fetch("/api/restaurants/conversation", {
      method: "POST",
      headers: { Accept: "application/json", "Content-Type": "application/json" },
      body: JSON.stringify({ message, state }),
      signal: AbortSignal.timeout(TIMEOUT_MS),
    });
  } catch {
    throw new Error("BiteCheck could not reach the conversation service.");
  }
  const payload: unknown = await response.json().catch(() => null);
  if (!response.ok) {
    const detail = isRecord(payload) ? payload.detail : null;
    const messageText = isRecord(detail) ? detail.message : detail;
    throw new Error(
      typeof messageText === "string"
        ? messageText
        : "BiteCheck could not understand that follow-up.",
    );
  }
  const parsed = parseConversationResponse(payload);
  if (parsed === null) {
    throw new Error("BiteCheck received an unexpected conversation response.");
  }
  return parsed;
}

type FollowUpRequester = (
  message: string,
  state: ConversationState,
) => Promise<ConversationResponse>;

export async function followUpConversationSequence(
  messages: string[],
  state: ConversationState,
  request: FollowUpRequester = followUpConversation,
): Promise<{ response: ConversationResponse; explanation: string }> {
  if (messages.length === 0) {
    throw new Error("Select at least one follow-up action.");
  }

  let nextState = state;
  let finalResponse: ConversationResponse | null = null;
  const explanations: string[] = [];
  for (const message of messages) {
    finalResponse = await request(message, nextState);
    nextState = finalResponse.state;
    explanations.push(finalResponse.transition_explanation);
  }

  if (finalResponse === null) {
    throw new Error("No follow-up response was produced.");
  }
  return { response: finalResponse, explanation: explanations.join(" ") };
}
