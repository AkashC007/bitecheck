import { getBackendHealth } from "@/lib/api/health";
import { RestaurantSearch } from "@/components/restaurant-search";

export default async function Home() {
  const backendHealth = await getBackendHealth();
  const isBackendConnected = backendHealth.state === "connected";

  return (
    <main className="min-h-screen bg-[#fbfaf7] text-stone-950">
      <header className="border-b border-stone-200 bg-[#fbfaf7]/95">
        <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-5 py-4 sm:px-8 lg:px-10">
          <div className="flex items-center gap-3">
            <span className="grid size-10 place-items-center rounded-xl bg-orange-700 font-serif text-xl font-bold text-white shadow-sm">
              B
            </span>
            <div>
              <p className="font-bold tracking-tight">BiteCheck</p>
              <p className="text-xs text-stone-500">Restaurant intelligence</p>
            </div>
          </div>

          <span className="rounded-full border border-stone-200 bg-white px-3 py-1.5 text-xs font-semibold text-stone-600">
            Explainable recommendations · Portfolio MVP
          </span>
        </div>
      </header>

      <RestaurantSearch backendConnected={isBackendConnected} />

      <footer className="border-t border-stone-200 bg-white">
        <div className="mx-auto flex max-w-7xl flex-col justify-between gap-2 px-5 py-6 text-xs text-stone-500 sm:flex-row sm:px-8 lg:px-10">
          <p>Real City identities with clearly labeled synthetic enrichment.</p>
          <p>City of Chicago Food Inspections snapshot · 2026-08-30.</p>
        </div>
      </footer>
    </main>
  );
}
