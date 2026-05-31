import { useState, useEffect } from "react";
import type { CouncilRunState } from "../types";
import { api } from "../api/client";

function parseNote(note: string) {
  const srcMatch = note.match(/^\[([^\]]+)\]/);
  const src = srcMatch ? srcMatch[1] : "data";
  const body = note.replace(/^\[[^\]]+\]\s*/, "");
  const urlMatch = body.match(/Source:\s*(https?:\/\/\S+)/i);
  const url = urlMatch ? urlMatch[1] : null;
  const text = body.replace(/\s*Source:\s*https?:\/\/\S+/i, "").trim();
  const domain = url ? url.replace(/^https?:\/\//, "").split("/")[0] : null;
  return { src, text, url, domain };
}

const DOT: Record<string, string> = {
  you: "bg-[#38bdf8]",
  analyst: "bg-[#34d399]",
  macro: "bg-[#fbbf24]",
  risk: "bg-[#f87171]",
};

function NoteItem({ note, type }: { note: string; type: string }) {
  const { src, text, url, domain } = parseNote(note);
  return (
    <div className="flex gap-3 py-3 border-b border-[#1f2a3d] last:border-0">
      <span className={`flex-shrink-0 w-1.5 h-1.5 rounded-full mt-2 ${DOT[type] ?? "bg-[#38bdf8]"}`} />
      <div className="min-w-0 flex-1">
        <div className="text-[10px] font-black uppercase tracking-widest text-[#8b9cb3] mb-0.5">{src}</div>
        <p className="text-[13px] text-[#f1f5f9] leading-snug">{text}</p>
        {url && domain && (
          <a
            href={url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-[11px] text-[#38bdf8] hover:underline mt-0.5 block truncate"
          >
            {domain}
          </a>
        )}
      </div>
    </div>
  );
}

function SectionHead({ label }: { label: string }) {
  return (
    <div className="flex items-center gap-3 mb-3">
      <span className="text-[10px] font-black uppercase tracking-widest text-[#38bdf8]">{label}</span>
      <div className="flex-1 h-px bg-[#1f2a3d]" />
    </div>
  );
}

export default function ResearchFeed({ state }: { state: CouncilRunState }) {
  const [watchlist, setWatchlist] = useState<string[]>([]);
  const [wlInput, setWlInput] = useState("");

  useEffect(() => {
    api.watchlist().then((d) => setWatchlist(d.symbols)).catch(() => {});
  }, []);

  const addWatch = async () => {
    const sym = wlInput.trim().toUpperCase();
    if (!sym) return;
    const d = await api.addWatch(sym);
    setWatchlist(d.symbols);
    setWlInput("");
  };

  const removeWatch = async (sym: string) => {
    const d = await api.removeWatch(sym) as { symbols: string[] };
    setWatchlist(d.symbols);
  };

  const notes = state.research_notes ?? [];
  const news     = notes.filter((n) => n.startsWith("[YOU") || n.startsWith("[News"));
  const analyst  = notes.filter((n) => n.startsWith("[Analyst") || n.startsWith("[FINNHUB"));
  const macro    = notes.filter((n) => n.startsWith("[Macro") || n.startsWith("[FRED"));
  const trending = state.trending_social ?? [];
  const risks    = state.risk_flags ?? [];
  const glossary = Object.entries(state.glossary ?? {});

  return (
    <div className="bg-[#0e1420] border border-[#1f2a3d] rounded-2xl p-5 animate-fade-up">
      {/* Header + Watchlist */}
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-xs font-black uppercase tracking-widest text-[#f1f5f9] m-0">
          Research Feed
        </h2>
        <div className="flex items-center gap-2">
          <input
            value={wlInput}
            onChange={(e) => setWlInput(e.target.value.toUpperCase())}
            onKeyDown={(e) => e.key === "Enter" && addWatch()}
            placeholder="Watch ticker…"
            maxLength={12}
            className="w-32 bg-[#141c2c] border border-[#1f2a3d] rounded-lg px-3 py-1.5 text-[12px] text-[#f1f5f9] placeholder:text-[#8b9cb3]/50 outline-none focus:border-[#38bdf8]/50"
          />
          <button
            onClick={addWatch}
            className="bg-[#38bdf8]/10 hover:bg-[#38bdf8]/20 text-[#38bdf8] text-[11px] font-black px-3 py-1.5 rounded-lg transition-colors"
          >
            + Watch
          </button>
        </div>
      </div>

      {watchlist.length > 0 && (
        <div className="flex flex-wrap gap-1.5 mb-4">
          {watchlist.map((sym) => (
            <span
              key={sym}
              className="flex items-center gap-1 bg-[#141c2c] border border-[#1f2a3d] text-[#38bdf8] text-[11px] font-bold px-2.5 py-1 rounded-full"
            >
              {sym}
              <button
                onClick={() => removeWatch(sym)}
                className="text-[#8b9cb3] hover:text-[#f87171] ml-0.5 leading-none"
              >
                ×
              </button>
            </span>
          ))}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {/* Left: News + Analyst + Macro */}
        <div>
          {news.length > 0 && (
            <div className="mb-5">
              <SectionHead label="Live News" />
              {news.map((n, i) => <NoteItem key={i} note={n} type="you" />)}
            </div>
          )}
          {analyst.length > 0 && (
            <div className="mb-5">
              <SectionHead label="Analyst Ratings & Earnings" />
              {analyst.map((n, i) => <NoteItem key={i} note={n} type="analyst" />)}
            </div>
          )}
          {macro.length > 0 && (
            <div>
              <SectionHead label="Macro Indicators" />
              {macro.map((n, i) => <NoteItem key={i} note={n} type="macro" />)}
            </div>
          )}
          {!news.length && !analyst.length && !macro.length && (
            <p className="text-[13px] text-[#8b9cb3]">Run analysis to load news.</p>
          )}
        </div>

        {/* Right: Social + Risk + Glossary */}
        <div>
          {trending.length > 0 && (
            <div className="mb-5">
              <SectionHead label="Trending on Social" />
              <div className="flex flex-wrap gap-2">
                {trending.slice(0, 20).map((t) => (
                  <span
                    key={t.symbol}
                    className="flex items-center gap-1.5 bg-[#141c2c] border border-[#1f2a3d] rounded-full px-2.5 py-1 text-[11px]"
                  >
                    <span className="font-black">{t.symbol}</span>
                    <span className="text-[#38bdf8]">{t.mentions}</span>
                  </span>
                ))}
              </div>
            </div>
          )}

          {risks.length > 0 && (
            <div className="mb-5">
              <SectionHead label="Risk & Compliance Flags" />
              {risks.map((r, i) => (
                <div key={i} className="bg-[#f87171]/5 border border-[#f87171]/15 rounded-lg px-3 py-2 text-[12px] text-[#f1f5f9] mb-2">
                  {r}
                </div>
              ))}
            </div>
          )}

          {glossary.length > 0 && (
            <div>
              <SectionHead label="Financial Terms Glossary" />
              <div className="grid grid-cols-1 gap-2">
                {glossary.map(([term, def]) => (
                  <div key={term} className="bg-[#141c2c] border border-[#1f2a3d] rounded-xl p-3">
                    <div className="text-[11px] font-black text-[#38bdf8] mb-0.5">{term}</div>
                    <div className="text-[12px] text-[#8b9cb3] leading-snug">{def}</div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
