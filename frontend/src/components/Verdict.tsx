import type { CouncilRunState } from "../types";

export default function Verdict({ state }: { state: CouncilRunState }) {
  const brief = state.friendly_brief ?? {};
  const headline = brief.headline ?? state.user_question;
  const intro = brief.intro ?? "";
  const directAnswer = brief.direct_answer ?? "";
  const bottomLine = brief.bottom_line ?? "";

  return (
    <div className="bg-[#0e1420] border border-[#1f2a3d] rounded-2xl p-6 animate-fade-up">
      <h3 className="text-xl font-black tracking-tight text-[#f1f5f9] mb-3 leading-snug">
        {headline}
      </h3>
      {intro && <p className="text-[#8b9cb3] text-[15px] leading-relaxed mb-4">{intro}</p>}
      {directAnswer && (
        <div className="bg-[#38bdf8]/5 border border-[#38bdf8]/15 rounded-xl p-4 mb-4">
          <span className="text-[10px] font-black uppercase tracking-widest text-[#38bdf8] block mb-1">
            Direct Answer
          </span>
          <p className="text-[#f1f5f9] text-[14px] leading-relaxed">{directAnswer}</p>
        </div>
      )}
      {bottomLine && (
        <div className="border-t border-[#1f2a3d] pt-4">
          <span className="text-[10px] font-black uppercase tracking-widest text-[#8b9cb3] block mb-1">
            Bottom Line
          </span>
          <p className="text-[#f1f5f9] text-[14px] font-medium leading-relaxed">{bottomLine}</p>
        </div>
      )}
    </div>
  );
}
