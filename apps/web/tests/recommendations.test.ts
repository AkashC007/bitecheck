import assert from "node:assert/strict";
import test from "node:test";

import {
  buildRecommendationRequest,
  parseRestaurantRecommendationResponse,
} from "../src/lib/api/recommendations.js";


const validResponse = {
  filters: {
    cuisine: null,
    maximum_budget: 25,
    vegetarian_required: true,
    starting_area: "Illinois Tech",
    maximum_travel_time: 30,
  },
  configured_weights: { rating: 0.1, review_confidence: 0.2 },
  match_count: 1,
  assigned_categories: ["best_overall"],
  recommendations: [
    {
      rank: 1,
      restaurant_id: "CHI-COC-1766001",
      name: "The Bog",
      address: "3241 S Federal St, Chicago, IL 60616",
      latitude: 41.8351,
      longitude: -87.62876,
      cuisine: "Japanese",
      neighborhood: "Bridgeport",
      price_category: "$$",
      estimated_cost_per_person: 22,
      vegetarian_available: true,
      vegan_available: false,
      rating: 4.8,
      dataset_review_count: 418,
      total_score: 79.2,
      categories: [
        {
          category: "best_overall",
          label: "Best overall",
          reason: "Highest weighted score.",
        },
      ],
      travel: {
        starting_area: "Illinois Tech",
        walking_minutes: 20,
        public_transit_minutes: 16,
        driving_minutes: 9,
        category: "comfortable_walk",
        selected_mode: "walking",
        selected_minutes: 20,
        explanation: "Comfortable walk: 20 minutes by walking.",
      },
      top_positive_themes: [
        { theme: "food_quality", label: "Food quality", mention_count: 3 },
      ],
      top_negative_themes: [
        { theme: "waiting_time", label: "Waiting time", mention_count: 2 },
      ],
      review_confidence_score: 70.78,
      review_confidence_band: "medium",
      ranking_factors: {
        review_confidence: {
          status: "active",
          score: 70.78,
          configured_weight: 0.2,
          effective_weight: 0.2,
          contribution: 14.16,
          explanation: "Evidence reliability, not truth.",
        },
      },
      ranking_explanation: "Strongest score contribution: rating.",
      latest_review_date: "2026-01-13",
      data_freshness_label: "Latest synthetic review: 2026-01-13",
      latest_inspection: {
        inspection_id: "2602706",
        inspection_date: "2024-08-19",
        result: "Pass",
        inspection_type: "Canvass",
        risk: "Risk 1 (High)",
      },
    },
  ],
  data_notice: "Real City identities with synthetic recommendation fields.",
};


test("buildRecommendationRequest maps personalized filters", () => {
  assert.deepEqual(
    buildRecommendationRequest({
      cuisine: "Japanese",
      maximumBudget: 25,
      vegetarianRequired: true,
      startingArea: "Illinois Tech",
      maximumTravelTime: 30,
    }),
    {
      filters: {
        cuisine: "Japanese",
        maximum_budget: 25,
        vegetarian_required: true,
        starting_area: "Illinois Tech",
        maximum_travel_time: 30,
      },
    },
  );
});


test("buildRecommendationRequest omits empty optional filters", () => {
  assert.deepEqual(buildRecommendationRequest({ vegetarianRequired: false }), {
    filters: { vegetarian_required: false },
  });
});


test("parseRestaurantRecommendationResponse accepts the card contract", () => {
  assert.deepEqual(
    parseRestaurantRecommendationResponse(validResponse),
    validResponse,
  );
});


test("parseRestaurantRecommendationResponse rejects mismatched counts", () => {
  assert.equal(
    parseRestaurantRecommendationResponse({ ...validResponse, match_count: 2 }),
    null,
  );
});


test("parseRestaurantRecommendationResponse rejects malformed themes", () => {
  const invalid = {
    ...validResponse,
    recommendations: [
      {
        ...validResponse.recommendations[0],
        top_positive_themes: [
          { label: "Food quality", mention_count: "three" },
        ],
      },
    ],
  };
  assert.equal(parseRestaurantRecommendationResponse(invalid), null);
});
