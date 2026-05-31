import { useEffect, useRef } from "react";
import type { KronosForecast } from "../types";
import { Pill } from "./Card";

function Sparkline({ values, direction }: { values: number[]; direction: string }) {
  const ref = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = ref.current;
    if (!canvas || values.length < 2) return;
    const dpr = window.devicePixelRatio || 1;
    const w = canvas.offsetWidth;
    const h = canvas.offsetHeight;
    canvas.width = w * dpr;
    canvas.height = h * dpr;
    const ctx = canvas.getContext("2d")!;
    ctx.scale(dpr, dpr);

    const color = direction === "up" ? "#34d399" : direction === "down" ? "#f87171" : "#8b9cb3";
    const min = Math.min(...values);
    const max = Math.max(...values);
    const range = max - min || 1;
    const pad = 4;
    const pts = values.map((v, i) => ({
      x: pad + (i / (values.length - 1)) * (w - pad * 2),
      y: pad + (h - pad * 2) - ((v - min) / range) * (h - pad * 2),
    }));
    const split = Math.ceil(pts.length / 2);

    const grad = ctx.createLinearGradient(0, 0, 0, h);
    grad.addColorStop(0, "rgba(56,189,248,0.2)");
    grad.addColorStop(1, "rgba(56,189,248,0)");
    ctx.beginPath();
    ctx.moveTo(pts[0].x, h);
    pts.forEach((p) => ctx.lineTo(p.x, p.y));
    ctx.lineTo(pts[pts.length - 1].x, h);
    ctx.closePath();
    ctx.fillStyle = grad;
    ctx.fill();

    ctx.beginPath();
    ctx.moveTo(pts[0].x, pts[0].y);
    for (let i = 1; i < split; i++) ctx.lineTo(pts[i].x, pts[i].y);
    ctx.strokeStyle = "#38bdf8";
    ctx.lineWidth = 1.5;
    ctx.lineCap = "round";
    ctx.stroke();

    ctx.beginPath();
    ctx.moveTo(pts[split - 1].x, pts[split - 1].y);
    for (let i = split; i < pts.length; i++) ctx.lineTo(pts[i].x, pts[i].y);
    ctx.strokeStyle = color;
    ctx.setLineDash([4, 3]);
    ctx.stroke();
    ctx.setLineDash([]);

    const last = pts[pts.length - 1];
    ctx.beginPath();
    ctx.arc(last.x, last.y, 3, 0, Math.PI * 2);
    ctx.fillStyle = color;
    ctx.fill();
  }, [values, direction]);

  return <canvas ref={ref} className="w-full h-full block" />;
}

export default function ForecastStrip({
  forecasts,
  signalAgreement,
}: {
  forecasts: KronosForecast[];
  signalAgreement?: string;
}) {
  if (!forecasts.length) return null;

  return (
    <div className="bg-[#0e1420] border border-[#1f2a3d] rounded-2xl p-5 animate-fade-up">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xs font-black uppercase tracking-widest text-[#f1f5f9] m-0">
          Live Forecasts
        </h2>
        {signalAgreement && (
          <Pill variant={signalAgreement === "mixed" ? "warn" : "ok"}>
            {signalAgreement.toUpperCase()}
          </Pill>
        )}
      </div>

      <div className="flex gap-3 overflow-x-auto pb-1">
        {forecasts.map((f) => {
          const up = f.direction === "up";
          const down = f.direction === "down";
          const sign = f.return_pct >= 0 ? "+" : "";
          const colorCls = up ? "text-[#34d399]" : down ? "text-[#f87171]" : "text-[#8b9cb3]";
          const borderCls = up
            ? "border-t-[#34d399]"
            : down
            ? "border-t-[#f87171]"
            : "border-t-[#8b9cb3]";

          return (
            <div
              key={f.symbol}
              className={`flex-shrink-0 w-[152px] bg-[#141c2c] border border-[#1f2a3d] ${borderCls} border-t-2 rounded-xl p-3 transition-all duration-150 hover:-translate-y-0.5 hover:border-[#38bdf8]/30 cursor-default`}
            >
              <div className="flex items-center justify-between mb-1">
                <span className="font-black text-[15px] tracking-tight">{f.symbol}</span>
                <span
                  className={`text-[9px] font-black uppercase tracking-wider px-1.5 py-0.5 rounded-full ${
                    up
                      ? "bg-[#34d399]/10 text-[#34d399]"
                      : down
                      ? "bg-[#f87171]/10 text-[#f87171]"
                      : "bg-white/5 text-[#8b9cb3]"
                  }`}
                >
                  {up ? "↑" : down ? "↓" : "→"} {f.direction.toUpperCase()}
                </span>
              </div>

              {f.last_close != null && (
                <div className="text-[13px] font-bold text-[#f1f5f9] mb-0.5">
                  ${f.last_close.toFixed(2)}
                </div>
              )}
              {f.predicted_close != null && (
                <div className="text-[10px] text-[#8b9cb3] mb-2">
                  → <span className={colorCls}>${f.predicted_close.toFixed(2)}</span>
                </div>
              )}

              <div className="h-14 mb-2">
                <Sparkline values={f.sparkline ?? []} direction={f.direction} />
              </div>

              <div className={`text-[11px] font-bold ${colorCls}`}>
                {sign}{f.return_pct.toFixed(1)}% / {f.horizon_days}d
              </div>
              {f.volatility_pct != null && (
                <div className="text-[10px] text-[#8b9cb3]">Vol {f.volatility_pct.toFixed(1)}%</div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
