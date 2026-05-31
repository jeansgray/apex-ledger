import { useState, type KeyboardEvent } from "react";

interface Props {
  onRun: (question: string, cash: number) => void;
  loading: boolean;
  status: string;
}

export default function QueryBar({ onRun, loading, status }: Props) {
  const [question, setQuestion] = useState("");
  const [cash, setCash] = useState(1000);

  const handleRun = () => {
    if (question.trim().length < 3) return;
    onRun(question.trim(), cash);
  };

  const handleKey = (e: KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) handleRun();
  };

  return (
    <div className="bg-[#0e1420] border border-[#1f2a3d] rounded-2xl p-5 mb-5">
      <div className="flex gap-3 items-end">
        <div className="flex-1">
          <label className="block text-[10px] font-black uppercase tracking-widest text-[#8b9cb3] mb-2">
            Ask your council
          </label>
          <textarea
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyDown={handleKey}
            placeholder="e.g. Should I buy more NVDA given my current exposure?"
            rows={2}
            className="w-full bg-[#141c2c] border border-[#1f2a3d] rounded-xl px-4 py-3 text-[14px] text-[#f1f5f9] placeholder:text-[#8b9cb3]/50 resize-none outline-none focus:border-[#38bdf8]/50 transition-colors"
          />
        </div>
        <div className="flex-shrink-0">
          <label className="block text-[10px] font-black uppercase tracking-widest text-[#8b9cb3] mb-2">
            Cash ($)
          </label>
          <input
            type="number"
            value={cash}
            onChange={(e) => setCash(Number(e.target.value))}
            min={100}
            step={100}
            className="w-28 bg-[#141c2c] border border-[#1f2a3d] rounded-xl px-3 py-3 text-[14px] text-[#f1f5f9] outline-none focus:border-[#38bdf8]/50 transition-colors"
          />
        </div>
        <button
          onClick={handleRun}
          disabled={loading || question.trim().length < 3}
          className="flex-shrink-0 bg-[#38bdf8] hover:bg-[#0ea5e9] disabled:opacity-40 disabled:cursor-not-allowed text-[#05080f] font-black text-[13px] uppercase tracking-widest px-6 py-3 rounded-xl transition-all duration-150 active:scale-95"
        >
          {loading ? (
            <span className="flex items-center gap-2">
              <span className="inline-block w-3 h-3 border-2 border-[#05080f]/30 border-t-[#05080f] rounded-full animate-spin" />
              Running
            </span>
          ) : (
            "Analyze"
          )}
        </button>
      </div>
      {status && (
        <p className="text-[12px] text-[#8b9cb3] mt-3">{status}</p>
      )}
    </div>
  );
}
