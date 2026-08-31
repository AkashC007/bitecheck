"use client";

import { useState } from "react";

import { InspectionExplorer } from "@/components/inspection-explorer";
import { RestaurantSearch } from "@/components/restaurant-search";


export function BiteCheckExperience({ backendConnected }: { backendConnected: boolean }) {
  const [view, setView] = useState<"public" | "lab">("public");

  return (
    <>
      <nav className="border-b border-slate-200 bg-white" aria-label="BiteCheck experiences">
        <div className="mx-auto flex max-w-7xl gap-2 px-5 py-3 sm:px-8 lg:px-10">
          <button type="button" aria-pressed={view === "public"} onClick={() => setView("public")} className={`rounded-xl px-4 py-2.5 text-sm font-black transition ${view === "public" ? "bg-slate-950 text-white shadow-sm" : "text-slate-500 hover:bg-slate-100 hover:text-slate-950"}`}>
            Public inspection explorer
          </button>
          <button type="button" aria-pressed={view === "lab"} onClick={() => setView("lab")} className={`rounded-xl px-4 py-2.5 text-sm font-black transition ${view === "lab" ? "bg-orange-700 text-white shadow-sm" : "text-slate-500 hover:bg-orange-50 hover:text-orange-900"}`}>
            Synthetic analytics lab
          </button>
        </div>
      </nav>
      {view === "public" ? (
        <InspectionExplorer backendConnected={backendConnected} />
      ) : (
        <div>
          <div className="border-b border-orange-200 bg-orange-50 px-5 py-3 text-center text-xs font-bold leading-5 text-orange-900">
            Portfolio experiment: ratings, reviews, cuisine, prices, travel times, themes, and confidence below are synthetic—not claims about these businesses.
          </div>
          <RestaurantSearch backendConnected={backendConnected} />
        </div>
      )}
    </>
  );
}
