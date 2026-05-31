import type { AppConfig, CouncilRunState, LedgerDetail, TickerItem } from "../types";

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return res.json();
}

export const api = {
  config: () => req<AppConfig>("/config"),

  ticker: () => req<{ tickers: TickerItem[] }>("/ticker"),

  runCouncil: (body: {
    question: string;
    simulation_id?: string | null;
    seed_demo?: boolean;
    cash_to_deploy?: number;
    use_live_simulation?: boolean;
  }) => req<CouncilRunState>("/council/run", { method: "POST", body: JSON.stringify(body) }),

  getRun: (runId: string) => req<CouncilRunState>(`/council/run/${runId}`),

  approveGate: (runId: string, gate_kind: string, approved: boolean) =>
    req<CouncilRunState>(`/council/run/${runId}/approve`, {
      method: "POST",
      body: JSON.stringify({ gate_kind, approved }),
    }),

  ledger: () => req<LedgerDetail>("/ledger/detail"),

  addHolding: (data: { symbol: string; quantity: number; cost_basis?: number; account: string }) =>
    req("/ledger/holdings", { method: "POST", body: JSON.stringify(data) }),

  deleteHolding: (id: number) => req(`/ledger/holdings/${id}`, { method: "DELETE" }),

  addTransaction: (data: { posted_on: string; description: string; amount: number; account: string }) =>
    req("/ledger/transactions", { method: "POST", body: JSON.stringify(data) }),

  deleteTransaction: (id: number) => req(`/ledger/transactions/${id}`, { method: "DELETE" }),

  watchlist: () => req<{ symbols: string[] }>("/watchlist"),
  addWatch: (symbol: string) =>
    req<{ symbols: string[] }>("/watchlist", { method: "POST", body: JSON.stringify({ symbol }) }),
  removeWatch: (symbol: string) => req(`/watchlist/${symbol}`, { method: "DELETE" }),
};
