import { useEffect, useRef, useState } from "react";
import { api } from "../api/client";
import type { TickerItem } from "../types";

export default function TickerBar() {
  const [tickers, setTickers] = useState<TickerItem[]>([]);
  const trackRef = useRef<HTMLDivElement>(null);

  const load = async () => {
    try {
      const data = await api.ticker();
      setTickers(data.tickers ?? []);
    } catch {}
  };

  useEffect(() => {
    load();
    const id = setInterval(load, 120_000);
    return () => clearInterval(id);
  }, []);

  useEffect(() => {
    if (!trackRef.current || !tickers.length) return;
    const w = trackRef.current.scrollWidth / 2;
    const speed = Math.max(30, w / 8);
    trackRef.current.style.animationDuration = `${speed}s`;
  }, [tickers]);

  const items = [...tickers, ...tickers]; // duplicate for seamless loop

  return (
    <div className="w-full bg-[#080d18] border-b border-[#1f2a3d] h-9 flex items-center overflow-hidden">
      <span className="flex-shrink-0 px-3 text-[10px] font-black tracking-widest uppercase text-[#38bdf8] border-r border-[#1f2a3d] h-full flex items-center">
        ▌ LIVE
      </span>
      <div className="flex-1 overflow-hidden h-full">
        <div ref={trackRef} className="ticker-scroll flex items-center h-full whitespace-nowrap">
          {items.map((t, i) => {
            const up = t.direction === "up";
            const down = t.direction === "down";
            const sign = t.change_pct >= 0 ? "+" : "";
            return (
              <span
                key={i}
                className="inline-flex items-center gap-1.5 px-4 h-full text-[11px] border-r border-white/[0.04]"
              >
                <span className="font-black text-[#f1f5f9]">{t.symbol}</span>
                {t.price ? (
                  <span className="text-[#8b9cb3]">${t.price.toFixed(2)}</span>
                ) : null}
                <span
                  className={`font-bold ${up ? "text-[#34d399]" : down ? "text-[#f87171]" : "text-[#8b9cb3]"}`}
                >
                  {up ? "▲" : down ? "▼" : "▸"} {sign}{t.change_pct.toFixed(2)}%
                </span>
              </span>
            );
          })}
        </div>
      </div>
    </div>
  );
}
