import assert from "node:assert/strict";
import test from "node:test";

import {
  buildRestaurantSearchParams,
  parseRestaurantSearchResponse,
} from "../src/lib/api/restaurants.js";


const validResponse = {
  applied_filters: {
    cuisine: "Japanese",
    maximum_budget: 25,
    vegetarian_required: true,
    starting_area: "Illinois Tech",
    maximum_travel_time: 30,
  },
  match_count: 1,
  restaurants: [
    {
      restaurant_id: "CHI-SYN-011",
      name: "Copper Maple Kitchen",
      address: "513 Fictional Street, Chicago, IL 60616",
      neighborhood: "Bridgeport",
      latitude: 41.84,
      longitude: -87.64,
      cuisine: "Japanese",
      price_category: "$",
      estimated_cost_per_person: 17,
      vegetarian_available: true,
      vegan_available: false,
      rating: 4.4,
      review_count: 321,
      travel: {
        starting_area: "Illinois Tech",
        mode: "walking",
        minutes: 18,
      },
    },
  ],
};


test("buildRestaurantSearchParams maps every form filter to the API contract", () => {
  const params = buildRestaurantSearchParams({
    cuisine: "Japanese",
    maximumBudget: 25,
    vegetarianRequired: true,
    startingArea: "Illinois Tech",
    maximumTravelTime: 30,
  });

  assert.deepEqual(Object.fromEntries(params), {
    cuisine: "Japanese",
    maximum_budget: "25",
    vegetarian_required: "true",
    starting_area: "Illinois Tech",
    maximum_travel_time: "30",
  });
});


test("buildRestaurantSearchParams omits optional empty filters", () => {
  const params = buildRestaurantSearchParams({ vegetarianRequired: false });

  assert.equal(params.toString(), "");
});


test("parseRestaurantSearchResponse accepts the complete backend contract", () => {
  assert.deepEqual(parseRestaurantSearchResponse(validResponse), validResponse);
});


test("parseRestaurantSearchResponse rejects a mismatched match count", () => {
  const invalidResponse = { ...validResponse, match_count: 2 };

  assert.equal(parseRestaurantSearchResponse(invalidResponse), null);
});


test("parseRestaurantSearchResponse rejects malformed restaurant fields", () => {
  const invalidResponse = {
    ...validResponse,
    restaurants: [
      {
        ...validResponse.restaurants[0],
        estimated_cost_per_person: "seventeen",
      },
    ],
  };

  assert.equal(parseRestaurantSearchResponse(invalidResponse), null);
});
