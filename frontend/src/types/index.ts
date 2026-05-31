export interface Holding {
  id: number;
  symbol: string;
  quantity: number;
  cost_basis: number | null;
  account: string;
}

export interface Transaction {
  id: number;
  posted_on: string;
  description: string;
  amount: number;
  account: string;
  category: string | null;
  status: string;
  memo: string | null;
}

export interface KronosForecast {
  symbol: string;
  direction: "up" | "down" | "flat";
  return_pct: number;
  volatility_pct: number;
  horizon_days: number;
  last_close: number | null;
  predicted_close: number | null;
  citation: string;
  sparkline: number[];
}

export interface RecommendedBuy {
  symbol: string;
  score: number;
  direction: string;
  return_pct: number;
  horizon_days: number;
  analyst_note: string;
  top_headline: string;
  headline_url: string;
  social_mentions: number;
  reasoning: string;
}

export interface TrendingStock {
  symbol: string;
  mentions: number;
  score: number;
  sources: string[];
}

export interface TickerItem {
  symbol: string;
  price: number;
  change_pct: number;
  direction: "up" | "down" | "flat";
}

export interface CouncilRunState {
  run_id: string;
  status: string;
  user_question: string;
  friendly_brief: {
    headline?: string;
    intro?: string;
    direct_answer?: string;
    bottom_line?: string;
    signal_agreement?: string;
    suggested_moves?: unknown[];
    action_items?: unknown[];
    kronos_forecasts?: KronosForecast[];
  };
  kronos_forecasts: KronosForecast[];
  recommended_buys: RecommendedBuy[];
  trending_social: TrendingStock[];
  research_notes: string[];
  risk_flags: string[];
  glossary: Record<string, string>;
  signal_agreement: string;
  error: string | null;
}

export interface AppConfig {
  default_simulation_id: string;
  keys: { valid: boolean; llm_configured: boolean };
  ledger_mode: string;
  holdings_count: number;
  default_cash_to_deploy: number;
  use_live_simulation: boolean;
}

export interface LedgerDetail {
  holdings: Holding[];
  transactions: Transaction[];
  unmatched_count: number;
  total_market_value_estimate: number;
  ledger_mode: string;
  is_demo: boolean;
}
