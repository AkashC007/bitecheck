import assert from "node:assert/strict";
import test from "node:test";

import {
  formatDistance,
  openStreetMapUrl,
  straightLineDistanceKm,
} from "../src/lib/location.js";


test("straightLineDistanceKm returns zero for the same point", () => {
  const point = { latitude: 41.8781, longitude: -87.6298 };
  assert.equal(straightLineDistanceKm(point, point), 0);
});


test("straightLineDistanceKm measures a known Chicago span", () => {
  const distance = straightLineDistanceKm(
    { latitude: 41.8781, longitude: -87.6298 },
    { latitude: 41.7943, longitude: -87.5907 },
  );
  assert.ok(distance > 9.5 && distance < 10.5);
});


test("formatDistance uses readable metre and kilometre labels", () => {
  assert.equal(formatDistance(0.42), "420 m");
  assert.equal(formatDistance(2.36), "2.4 km");
});


test("openStreetMapUrl points to the exact public coordinates", () => {
  assert.equal(
    openStreetMapUrl({ latitude: 41.8351, longitude: -87.62876 }),
    "https://www.openstreetmap.org/?mlat=41.835100&mlon=-87.628760#map=18/41.835100/-87.628760",
  );
});
