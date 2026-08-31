"use client";

import { FormEvent, useState } from "react";

import {
  exploreInspections,
  InspectionExplorerRequest,
  InspectionExplorerResponse,
  InspectionResultFilter,
  PublicInspectionRestaurant,
} from "@/lib/api/inspections";
import { openStreetMapUrl } from "@/lib/location";


const SEARCH_CENTERS = [
  { id: "loop", label: "Chicago Loop", latitude: 41.8781, longitude: -87.6298 },
  { id: "iit", label: "Illinois Tech", latitude: 41.8349, longitude: -87.627 },
  { id: "chinatown", label: "Chinatown", latitude: 41.852, longitude: -87.6321 },
  { id: "hyde-park", label: "Hyde Park", latitude: 41.7943, longitude: -87.5907 },
  { id: "bridgeport", label: "Bridgeport", latitude: 41.8381, longitude: -87.6512 },
  { id: "lakeview", label: "Lakeview", latitude: 41.9439, longitude: -87.6493 },
  { id: "river-north", label: "River North", latitude: 41.8924, longitude: -87.6341 },
] as const;

type ExplorerState =
  | { kind: "idle" }
  | { kind: "loading" }
  | { kind: "success"; response: InspectionExplorerResponse }
  | { kind: "error"; message: string };

function resultStyles(level: PublicInspectionRestaurant["attention_level"]) {
  if (level === "latest_passed") {
    return "border-emerald-200 bg-emerald-50 text-emerald-800";
  }
  if (level === "conditions_noted") {
    return "border-amber-200 bg-amber-50 text-amber-900";
  }
  if (level === "review_latest_report") {
    return "border-red-200 bg-red-50 text-red-800";
  }
  return "border-slate-200 bg-slate-50 text-slate-700";
}

function formatRetrievedAt(value: string) {
  const date = new Date(value);
  return Number.isNaN(date.getTime())
    ? value
    : new Intl.DateTimeFormat("en-US", {
        dateStyle: "medium",
        timeStyle: "short",
      }).format(date);
}

function InspectionCard({ restaurant }: { restaurant: PublicInspectionRestaurant }) {
  const mapUrl = openStreetMapUrl({
    latitude: restaurant.latitude,
    longitude: restaurant.longitude,
  });

  return (
    <article className="group flex h-full flex-col rounded-[1.75rem] border border-slate-200 bg-white p-5 shadow-[0_16px_45px_rgba(15,23,42,0.07)] transition duration-200 hover:-translate-y-1 hover:border-sky-300 hover:shadow-[0_22px_55px_rgba(15,23,42,0.12)]">
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <p className="text-xs font-black uppercase tracking-[0.15em] text-sky-700">
            License {restaurant.license_number}
          </p>
          <h3 className="mt-1 text-xl font-black leading-tight tracking-[-0.025em] text-slate-950">
            {restaurant.name}
          </h3>
          {restaurant.alternate_name && (
            <p className="mt-1 text-xs text-slate-500">
              Also listed as {restaurant.alternate_name}
            </p>
          )}
        </div>
        {restaurant.distance_km !== null && (
          <span className="shrink-0 rounded-full bg-sky-950 px-3 py-1.5 text-xs font-bold text-white">
            {restaurant.distance_km.toFixed(1)} km
          </span>
        )}
      </div>

      <a
        href={mapUrl}
        target="_blank"
        rel="noreferrer"
        className="mt-4 flex items-start gap-2 text-sm font-medium leading-5 text-slate-600 underline decoration-slate-300 underline-offset-4 hover:text-sky-800 hover:decoration-sky-400"
      >
        <span aria-hidden="true">⌖</span>
        <span>{restaurant.address}</span>
      </a>

      <div className={`mt-5 rounded-2xl border p-4 ${resultStyles(restaurant.attention_level)}`}>
        <p className="text-xs font-black uppercase tracking-[0.14em]">
          Latest official result
        </p>
        <p className="mt-1 text-lg font-black">{restaurant.latest_inspection.result}</p>
        <p className="mt-1 text-xs font-semibold">{restaurant.attention_label}</p>
      </div>

      <dl className="mt-5 grid grid-cols-2 gap-3 text-sm">
        <div className="rounded-xl bg-slate-50 p-3">
          <dt className="text-xs font-bold uppercase tracking-wide text-slate-500">Date</dt>
          <dd className="mt-1 font-bold text-slate-900">
            {restaurant.latest_inspection.inspection_date}
          </dd>
        </div>
        <div className="rounded-xl bg-slate-50 p-3">
          <dt className="text-xs font-bold uppercase tracking-wide text-slate-500">City risk</dt>
          <dd className="mt-1 font-bold text-slate-900">{restaurant.city_risk_category}</dd>
        </div>
      </dl>

      <div className="mt-4 border-t border-slate-100 pt-4">
        <p className="text-sm font-bold text-slate-900">
          {restaurant.latest_inspection.inspection_type}
        </p>
        <p className="mt-1 text-xs leading-5 text-slate-500">
          {restaurant.history.records_in_query} inspection record
          {restaurant.history.records_in_query === 1 ? "" : "s"} appeared in this live query:
          {` ${restaurant.history.pass_count} pass, ${restaurant.history.conditions_count} conditions, ${restaurant.history.fail_count} fail.`}
        </p>
      </div>
    </article>
  );
}

export function InspectionExplorer({ backendConnected }: { backendConnected: boolean }) {
  const [centerId, setCenterId] = useState("loop");
  const [radiusKm, setRadiusKm] = useState("3");
  const [query, setQuery] = useState("");
  const [resultFilter, setResultFilter] =
    useState<InspectionResultFilter>("all");
  const [state, setState] = useState<ExplorerState>({ kind: "idle" });
  const [centerLabel, setCenterLabel] = useState("Chicago Loop");
  const [locationStatus, setLocationStatus] = useState<string | null>(null);

  async function runSearch(
    coordinates?: { latitude: number; longitude: number },
    label?: string,
  ) {
    const cleanedQuery = query.trim();
    if (coordinates === undefined && !cleanedQuery) {
      setState({
        kind: "error",
        message: "Enter a restaurant, address, or ZIP for a citywide search.",
      });
      return;
    }

    setState({ kind: "loading" });
    const request: InspectionExplorerRequest = {
      radius_km: Number(radiusKm),
      result_filter: resultFilter,
      limit: 24,
      ...(cleanedQuery ? { query: cleanedQuery } : {}),
      ...(coordinates ?? {}),
    };
    try {
      const response = await exploreInspections(request);
      setState({ kind: "success", response });
      setCenterLabel(label ?? "Citywide search");
    } catch (error) {
      setState({
        kind: "error",
        message:
          error instanceof Error
            ? error.message
            : "Live inspection data could not be loaded.",
      });
    }
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const center = SEARCH_CENTERS.find((item) => item.id === centerId);
    if (center === undefined) {
      await runSearch();
      return;
    }
    await runSearch(
      { latitude: center.latitude, longitude: center.longitude },
      center.label,
    );
  }

  function useCurrentLocation() {
    if (!("geolocation" in navigator)) {
      setLocationStatus("Location is unavailable in this browser.");
      return;
    }
    setLocationStatus("Requesting location permission…");
    navigator.geolocation.getCurrentPosition(
      (position) => {
        setLocationStatus(
          "Location received. Coordinates are used for this live City query and are not stored.",
        );
        void runSearch(
          {
            latitude: position.coords.latitude,
            longitude: position.coords.longitude,
          },
          "Your current location",
        );
      },
      (error) => {
        setLocationStatus(
          error.code === error.PERMISSION_DENIED
            ? "Location permission was not granted. Chicago area search still works."
            : "Current location could not be read. Try a Chicago area instead.",
        );
      },
      { enableHighAccuracy: false, timeout: 10_000, maximumAge: 300_000 },
    );
  }

  return (
    <>
      <section className="relative isolate overflow-hidden bg-slate-950 text-white">
        <div aria-hidden="true" className="absolute -left-24 top-0 -z-10 size-96 rounded-full bg-sky-500/20 blur-3xl" />
        <div aria-hidden="true" className="absolute -right-20 bottom-0 -z-10 size-96 rounded-full bg-emerald-400/15 blur-3xl" />
        <div className="mx-auto grid max-w-7xl gap-9 px-5 py-12 sm:px-8 lg:grid-cols-[0.9fr_1.1fr] lg:items-center lg:px-10 lg:py-16">
          <div>
            <span className="inline-flex items-center gap-2 rounded-full border border-emerald-300/25 bg-emerald-300/10 px-3 py-1.5 text-xs font-black uppercase tracking-[0.16em] text-emerald-200">
              <span className="size-2 rounded-full bg-emerald-300 shadow-[0_0_12px_rgba(110,231,183,0.8)]" />
              Live public data
            </span>
            <h1 className="mt-5 max-w-2xl text-4xl font-black tracking-[-0.045em] sm:text-5xl lg:text-6xl">
              Know what Chicago inspectors actually observed.
            </h1>
            <p className="mt-5 max-w-xl text-base leading-7 text-slate-300 sm:text-lg">
              Search real establishments, addresses, and the newest official inspection result—without demo ratings or invented reviews.
            </p>
            <div className="mt-7 flex flex-wrap gap-3 text-xs font-bold text-slate-300">
              <span className="rounded-full border border-white/10 bg-white/5 px-3 py-2">Official City source</span>
              <span className="rounded-full border border-white/10 bg-white/5 px-3 py-2">No API key</span>
              <span className="rounded-full border border-white/10 bg-white/5 px-3 py-2">Chicago only</span>
            </div>
          </div>

          <form onSubmit={handleSubmit} className="rounded-[2rem] border border-white/10 bg-white p-5 text-slate-950 shadow-2xl sm:p-7">
            <div className="flex items-center justify-between gap-3 border-b border-slate-100 pb-5">
              <div>
                <p className="text-xs font-black uppercase tracking-[0.16em] text-sky-700">Live inspection search</p>
                <h2 className="mt-1 text-2xl font-black tracking-tight">Choose where to look</h2>
              </div>
              <span className={`rounded-full px-3 py-1.5 text-xs font-bold ${backendConnected ? "bg-emerald-50 text-emerald-700" : "bg-red-50 text-red-700"}`}>
                {backendConnected ? "Service online" : "Service offline"}
              </span>
            </div>

            <label className="mt-5 block text-sm font-bold" htmlFor="inspection-center">Search center</label>
            <select id="inspection-center" value={centerId} onChange={(event) => setCenterId(event.target.value)} className="mt-2 h-12 w-full rounded-xl border border-slate-200 bg-slate-50 px-4 outline-none focus:border-sky-500 focus:ring-3 focus:ring-sky-100">
              {SEARCH_CENTERS.map((center) => <option key={center.id} value={center.id}>{center.label}</option>)}
              <option value="citywide">Citywide text search</option>
            </select>

            <div className="mt-4 grid gap-4 sm:grid-cols-[1fr_0.45fr]">
              <div>
                <label className="block text-sm font-bold" htmlFor="inspection-query">Restaurant, address, or ZIP <span className="font-normal text-slate-400">(optional)</span></label>
                <input id="inspection-query" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Example: 60616 or cafe" className="mt-2 h-12 w-full rounded-xl border border-slate-200 bg-slate-50 px-4 outline-none focus:border-sky-500 focus:ring-3 focus:ring-sky-100" />
              </div>
              <div>
                <label className="block text-sm font-bold" htmlFor="inspection-radius">Radius</label>
                <select id="inspection-radius" value={radiusKm} onChange={(event) => setRadiusKm(event.target.value)} disabled={centerId === "citywide"} className="mt-2 h-12 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 disabled:text-slate-400">
                  <option value="1">1 km</option><option value="2">2 km</option><option value="3">3 km</option><option value="5">5 km</option>
                </select>
              </div>
            </div>

            <fieldset className="mt-5">
              <legend className="text-sm font-bold">Latest result</legend>
              <div className="mt-2 flex flex-wrap gap-2">
                {(["all", "pass", "conditions", "fail"] as const).map((filter) => (
                  <button key={filter} type="button" aria-pressed={resultFilter === filter} onClick={() => setResultFilter(filter)} className={`rounded-full border px-3 py-2 text-xs font-bold capitalize transition ${resultFilter === filter ? "border-sky-700 bg-sky-700 text-white" : "border-slate-200 bg-white text-slate-600 hover:border-sky-300"}`}>{filter}</button>
                ))}
              </div>
            </fieldset>

            <div className="mt-6 grid gap-3 sm:grid-cols-2">
              <button type="submit" disabled={!backendConnected || state.kind === "loading"} className="h-12 rounded-xl bg-sky-700 px-5 font-black text-white shadow-lg shadow-sky-700/15 transition hover:-translate-y-0.5 hover:bg-sky-800 disabled:cursor-not-allowed disabled:bg-slate-300">
                {state.kind === "loading" ? "Checking City data…" : "Explore inspections"}
              </button>
              <button type="button" onClick={useCurrentLocation} disabled={!backendConnected || state.kind === "loading"} className="h-12 rounded-xl border border-sky-200 bg-sky-50 px-5 font-black text-sky-900 transition hover:-translate-y-0.5 hover:border-sky-400 disabled:cursor-not-allowed disabled:text-slate-400">
                Use my current location
              </button>
            </div>
            <p className="mt-4 text-xs leading-5 text-slate-500">
              Preset areas share no personal location. If you choose current location, coordinates are sent for the live City query and are not stored by BiteCheck.
            </p>
            {locationStatus && <p className="mt-2 text-xs font-semibold text-sky-700" role="status">{locationStatus}</p>}
          </form>
        </div>
      </section>

      <section className="mx-auto max-w-7xl px-5 py-10 sm:px-8 lg:px-10 lg:py-14" aria-live="polite">
        {state.kind === "idle" && (
          <div className="rounded-[1.75rem] border border-dashed border-slate-300 bg-white px-6 py-12 text-center">
            <p className="text-sm font-black uppercase tracking-[0.16em] text-sky-700">Ready for a live query</p>
            <h2 className="mt-2 text-2xl font-black text-slate-950">Start with a Chicago area or search by name.</h2>
            <p className="mx-auto mt-3 max-w-2xl text-sm leading-6 text-slate-500">The City dataset covers inspections, not menus, ratings, prices, opening hours, or a guarantee of current operation.</p>
          </div>
        )}
        {state.kind === "error" && (
          <div className="rounded-[1.75rem] border border-red-200 bg-red-50 px-6 py-10 text-center" role="alert">
            <p className="text-sm font-black uppercase tracking-wider text-red-700">Live search unavailable</p>
            <p className="mt-2 font-semibold text-red-900">{state.message}</p>
          </div>
        )}
        {state.kind === "loading" && (
          <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-3" aria-label="Loading live inspection results">
            {[1, 2, 3].map((item) => <div key={item} className="h-80 animate-pulse rounded-[1.75rem] bg-slate-200" />)}
          </div>
        )}
        {state.kind === "success" && (
          <>
            <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
              <div>
                <p className="text-xs font-black uppercase tracking-[0.16em] text-sky-700">{centerLabel}</p>
                <h2 className="mt-1 text-3xl font-black tracking-tight text-slate-950">{state.response.restaurant_count} real establishment{state.response.restaurant_count === 1 ? "" : "s"}</h2>
                <p className="mt-2 text-sm text-slate-500">Retrieved {formatRetrievedAt(state.response.retrieved_at)} · {state.response.source_record_count} source records examined</p>
              </div>
              <a href={state.response.source_url} target="_blank" rel="noreferrer" className="text-sm font-bold text-sky-700 underline underline-offset-4 hover:text-sky-900">View the official City dataset ↗</a>
            </div>
            <div className="mt-5 rounded-2xl border border-amber-200 bg-amber-50 p-4 text-xs leading-5 text-amber-900">{state.response.data_notice}</div>
            {state.response.restaurant_count === 0 ? (
              <div className="mt-7 rounded-[1.75rem] border border-dashed border-slate-300 bg-white px-6 py-12 text-center">
                <h3 className="text-xl font-black">No matching inspection records found.</h3>
                <p className="mt-2 text-sm text-slate-500">This can happen outside Chicago, with a narrow radius, or when the latest-result filter removes the available records.</p>
              </div>
            ) : (
              <div className="mt-7 grid gap-5 md:grid-cols-2 xl:grid-cols-3">
                {state.response.restaurants.map((restaurant) => <InspectionCard key={restaurant.license_number} restaurant={restaurant} />)}
              </div>
            )}
          </>
        )}
      </section>
    </>
  );
}
