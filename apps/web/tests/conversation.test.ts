import assert from "node:assert/strict";
import test from "node:test";

import {
  ConversationResponse,
  ConversationState,
  followUpConversationSequence,
} from "../src/lib/api/conversation.js";


const INITIAL_STATE: ConversationState = {
  filters: {
    cuisine: null,
    maximum_budget: 25,
    vegetarian_required: true,
    starting_area: "Illinois Tech",
    maximum_travel_time: 30,
  },
  sort_mode: "weighted",
  travel_preference: "any",
  theme_preference: null,
  result_limit: null,
};

function response(
  intent: string,
  state: ConversationState,
): ConversationResponse {
  return {
    intent,
    state,
    transition_explanation: `Applied ${intent}.`,
    candidate_count_before_limit: 0,
    results: {
      filters: state.filters,
      configured_weights: {},
      match_count: 0,
      assigned_categories: [],
      recommendations: [],
      data_notice: "Hybrid data.",
    },
  };
}


test("followUpConversationSequence carries state through selected actions", async () => {
  const receivedStates: ConversationState[] = [];
  const requester = async (
    message: string,
    state: ConversationState,
  ): Promise<ConversationResponse> => {
    receivedStates.push(state);
    if (message === "walkable") {
      return response("walkable", { ...state, travel_preference: "walkable" });
    }
    return response("cheapest", {
      ...state,
      sort_mode: "cheapest",
      result_limit: 1,
    });
  };

  const result = await followUpConversationSequence(
    ["walkable", "cheapest"],
    INITIAL_STATE,
    requester,
  );

  assert.equal(receivedStates[0].travel_preference, "any");
  assert.equal(receivedStates[1].travel_preference, "walkable");
  assert.equal(result.response.state.travel_preference, "walkable");
  assert.equal(result.response.state.sort_mode, "cheapest");
  assert.equal(result.response.state.result_limit, 1);
  assert.equal(result.explanation, "Applied walkable. Applied cheapest.");
});


test("followUpConversationSequence rejects an empty selection", async () => {
  await assert.rejects(
    followUpConversationSequence([], INITIAL_STATE),
    /at least one follow-up/,
  );
});
