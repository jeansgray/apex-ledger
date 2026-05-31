import { useState, useEffect } from "react";
import "./index.css";
import { api } from "./api/client";
import type { CouncilRunState, AppConfig } from "./types";
import TickerBar from "./components/TickerBar";
import QueryBar from "./components/QueryBar";
import RecBuys from "./components/RecBuys";
import ForecastStrip from "./components/ForecastStrip";
import Verdict from "./components/Verdict";
import ResearchFeed from "./components/ResearchFeed";

function StatusPill({ config }: { config: AppConfig | null }) {
  if (!config) return null;
  const live = config.keys?.valid && config.keys?.llm_configured;
  return (
    <span
      className={`text-[10px] font-black uppercase tracking-widest px-3 py-1.5 rounded-full border ${
        live
          ? "border-[#34d399]/40 text-[#34d399] bg-[#34d399]/8"
          : "border-[#1f2a3d] text-[#8b9cb3] bg-[#0e1420]"
      }`}
    >
      {config.ledger_mode === "personal" ? "Personal" : "Demo"} · {live ? "Live" : "Offline"}
    </span>
  );
}

export default function App() {
  const [config, setConfig] = useState<AppConfig | null>(null);
  const [state, setState] = useState<CouncilRunState | null>(null);
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState("");
  const [tab, setTab] = useState<"scenarios" | "portfolio" | "records">("scenarios");

  useEffect(() => {
    api.config().then(setConfig).catch(() => {});
  }, []);

  const runCouncil = async (question: string, cash: number) => {
    setLoading(true);
    setStatus("Running council analysis…");
    try {
      const result = await api.runCouncil({
        question,
        seed_demo: true,
        cash_to_deploy: cash,
        use_live_simulation: config?.use_live_simulation !== false,
      });
      setState(result);
      setStatus("Done.");
      setTimeout(() => setStatus(""), 3000);
    } catch (err) {
      setStatus(`Error: ${(err as Error).message}`);
    } finally {
      setLoading(false);
    }
  };

  const forecasts = state?.kronos_forecasts ?? state?.friendly_brief?.kronos_forecasts ?? [];

  return (
    <div className="min-h-screen">
      {/* Ticker */}
      <TickerBar />

      <div className="max-w-[1140px] mx-auto px-4 pb-16">
        {/* App bar */}
        <header className="flex items-center justify-between gap-4 py-5 border-b border-[#1f2a3d] mb-5">
          <div className="flex items-center gap-3">
            <img
              src="/static/apex-logo.svg"
              alt="Apex Ledger"
              width={44}
              height={44}
              className="rounded-xl shadow-lg shadow-[#38bdf8]/10"
            />
            <div>
              <h1 className="m-0 text-[15px] font-black uppercase tracking-widest text-[#f1f5f9]">
                Apex Ledger
              </h1>
              <p className="m-0 text-[11px] text-[#8b9cb3]">
                Portfolio intelligence · apex predator clarity
              </p>
            </div>
          </div>
          <StatusPill config={config} />
        </header>

        {/* Query */}
        <QueryBar onRun={runCouncil} loading={loading} status={status} />

        {/* Results */}
        {state && (
          <div className="flex flex-col gap-4">
            {/* Recommended Buys */}
            {state.recommended_buys?.length > 0 && (
              <RecBuys buys={state.recommended_buys} />
            )}

            {/* Live Forecasts */}
            {forecasts.length > 0 && (
              <ForecastStrip
                forecasts={forecasts}
                signalAgreement={state.signal_agreement}
              />
            )}

            {/* Verdict */}
            <Verdict state={state} />

            {/* Research Feed */}
            <ResearchFeed state={state} />

            {/* Tabs */}
            <div className="bg-[#0e1420] border border-[#1f2a3d] rounded-2xl overflow-hidden animate-fade-up">
              <div className="flex border-b border-[#1f2a3d]">
                {(["scenarios", "portfolio", "records"] as const).map((t) => (
                  <button
                    key={t}
                    onClick={() => setTab(t)}
                    className={`px-5 py-3.5 text-[11px] font-black uppercase tracking-widest transition-colors ${
                      tab === t
                        ? "text-[#38bdf8] border-b-2 border-[#38bdf8] bg-[#38bdf8]/5"
                        : "text-[#8b9cb3] hover:text-[#f1f5f9]"
                    }`}
                  >
                    {t}
                  </button>
                ))}
              </div>
              <div className="p-5 text-[13px] text-[#8b9cb3]">
                {tab === "scenarios" && (
                  <p className="text-[#f1f5f9]">{state.friendly_brief?.intro ?? "No scenarios yet."}</p>
                )}
                {tab === "portfolio" && (
                  <p>Holdings count: {config?.holdings_count ?? "—"}</p>
                )}
                {tab === "records" && (
                  <p>Transaction reconciliation coming soon.</p>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
