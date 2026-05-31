import type { RecommendedBuy } from "../types";
import { Pill } from "./Card";

function sentimentVariant(reasoning: string): "ok" | "danger" | "default" {
  if (/FinBERT:\s*positive/i.test(reasoning)) return "ok";
  if (/FinBERT:\s*negative/i.test(reasoning)) return "danger";
  return "default";
}

function sentimentLabel(reasoning: string): string | null {
  const pos = reasoning.match(/FinBERT:\s*positive[^(]*\(([^)]+)\)/i);
  const neg = reasoning.match(/FinBERT:\s*negative[^(]*\(([^)]+)\)/i);
  const neu = reasoning.match(/FinBERT:\s*neutral/i);
  if (pos) return `▲ Bullish ${pos[1]}`;
  if (neg) return `▼ Bearish ${neg[1]}`;
  if (neu) return "▸ Neutral";
  return null;
}

export default function RecBuys({ buys }: { buys: RecommendedBuy[] }) {
  if (!buys.length) return null;

  return (
    <div className="bg-[#0e1420] border border-[#1f2a3d] rounded-2xl p-5 animate-fade-up">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xs font-black uppercase tracking-widest text-[#f1f5f9] m-0">
          Today's Recommended Buys
        </h2>
        <Pill variant="ok">Top {buys.length} picks · this run</Pill>
      </div>

      <div className="flex gap-3 overflow-x-auto pb-1 scrollbar-thin">
        {buys.map((b, i) => {
          const isTop = i === 0;
          const dir = b.direction;
          const pctStr =
            dir === "up"
              ? `▲ +${b.return_pct.toFixed(1)}% / ${b.horizon_days}d`
              : "→ Flat";
          const badge = sentimentLabel(b.reasoning);
          const badgeVariant = sentimentVariant(b.reasoning);

          return (
            <div
              key={b.symbol}
              style={{ animationDelay: `${i * 0.07}s` }}
              className={`animate-fade-up flex-shrink-0 w-[168px] rounded-xl p-3.5 border transition-all duration-150 hover:-translate-y-1 hover:shadow-xl cursor-default relative overflow-hidden
                ${isTop
                  ? "border-[#34d399]/50 bg-gradient-to-br from-[#141c2c] to-[#34d399]/5"
                  : "border-[#1f2a3d] bg-[#141c2c] hover:border-[#38bdf8]/30"
                }`}
            >
              {isTop && (
                <span className="absolute top-0 right-0 text-[9px] font-black bg-[#34d399] text-black px-2 py-0.5 rounded-bl-lg rounded-tr-xl tracking-wider">
                  ★ TOP
                </span>
              )}
              {!isTop && (
                <div className="text-[10px] font-black uppercase tracking-widest text-[#8b9cb3] mb-1">
                  #{i + 1}
                </div>
              )}
              {isTop && <div className="h-4" />}

              <div className="text-xl font-black tracking-tight mb-1">{b.symbol}</div>

              <span className="inline-flex items-center text-[10px] font-black bg-[#34d399]/10 text-[#34d399] px-1.5 py-0.5 rounded-full mb-2">
                {b.score.toFixed(0)} / 100
              </span>

              <div
                className={`text-[13px] font-bold mb-2 ${
                  dir === "up" ? "text-[#34d399]" : "text-[#8b9cb3]"
                }`}
              >
                {pctStr}
              </div>

              {badge && (
                <Pill variant={badgeVariant} >{badge}</Pill>
              )}

              {b.analyst_note && (
                <p className="text-[10px] text-[#8b9cb3] mt-1.5 leading-snug">{b.analyst_note}</p>
              )}
              {b.top_headline && (
                <p className="text-[10px] text-[#8b9cb3] mt-1 leading-snug line-clamp-2">
                  {b.top_headline}
                </p>
              )}
              {b.social_mentions > 0 && (
                <p className="text-[10px] text-[#38bdf8] mt-1">▲ {b.social_mentions} social</p>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
