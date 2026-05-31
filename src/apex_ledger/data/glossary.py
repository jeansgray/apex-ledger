"""Financial Terms Glossary — plain English definitions for council jargon.

Scans research notes and risk flags for known financial terms and returns
a dict of {term: definition} for any terms found. Zero API cost, fully static.
"""

from __future__ import annotations

import re

TERMS: dict[str, str] = {
    # Valuation
    "P/E ratio": (
        "Price-to-Earnings ratio — how much investors pay per $1 of company profit. "
        "A P/E of 37 means you're paying $37 for every $1 the company earns. "
        "Higher = more expensive relative to earnings; lower = cheaper."
    ),
    "PEG ratio": (
        "Price/Earnings-to-Growth ratio — P/E divided by expected earnings growth rate. "
        "A PEG below 1 often suggests undervaluation; above 2 may indicate overvaluation."
    ),
    "EPS": (
        "Earnings Per Share — company profit divided by number of shares outstanding. "
        "A key metric for profitability; rising EPS generally means the business is growing."
    ),
    "EPS surprise": (
        "The difference between actual EPS reported and what analysts predicted. "
        "A positive surprise (+3%) means the company beat expectations — often moves the stock up."
    ),
    "market cap": (
        "Market Capitalization — total market value of all a company's shares. "
        "Calculated as share price × shares outstanding. "
        "Large cap (>$10B), mid cap ($2B–$10B), small cap (<$2B)."
    ),
    "dividend yield": (
        "Annual dividend payment divided by stock price, expressed as a percentage. "
        "A 0.33% yield on AAPL means for every $100 invested you receive $0.33/year in dividends."
    ),
    "analyst target": (
        "The average price analysts at investment banks predict a stock will reach "
        "within the next 12 months. Not a guarantee — just professional estimates."
    ),
    "52-week range": (
        "The highest and lowest price a stock has traded at over the past year. "
        "Useful for understanding where current price sits relative to recent history."
    ),
    # Macro indicators
    "VIX": (
        "CBOE Volatility Index — measures expected market volatility over the next 30 days. "
        "Often called the 'fear gauge'. Below 20 = calm market; above 30 = high fear/uncertainty."
    ),
    "10-year Treasury yield": (
        "Interest rate the US government pays on 10-year bonds. "
        "A key benchmark — rising yields tend to pressure growth stock valuations "
        "and make bonds more attractive relative to stocks."
    ),
    "Fed funds rate": (
        "The interest rate banks charge each other for overnight loans, set by the Federal Reserve. "
        "Cuts lower borrowing costs economy-wide; hikes slow spending and inflation."
    ),
    "CPI": (
        "Consumer Price Index — measures the average change in prices paid by consumers. "
        "The main inflation gauge. High CPI = inflation rising; Fed may raise rates in response."
    ),
    "unemployment rate": (
        "Percentage of the labor force actively looking for work but not employed. "
        "Low unemployment = strong economy; very low can signal inflation pressure."
    ),
    # Trading concepts
    "OHLCV": (
        "Open, High, Low, Close, Volume — the five data points used to describe a stock's "
        "price action over a given period. Foundation of technical analysis and forecasting."
    ),
    "momentum": (
        "The tendency of an asset to continue moving in its current direction. "
        "Strong upward momentum means recent price gains are likely to persist short-term."
    ),
    "volatility": (
        "How much a stock's price moves up and down. High volatility = larger swings = more risk. "
        "Often measured as annualized standard deviation of daily returns."
    ),
    "basis points": (
        "A unit equal to 0.01% (1/100th of a percent). Used to describe small interest rate changes. "
        "25 basis points = 0.25%. A 'quarter-point rate cut' = 25 basis points."
    ),
    "yield curve": (
        "A graph showing interest rates across different bond maturities. "
        "Normally slopes upward (longer = higher yield). An inverted yield curve "
        "(short rates > long rates) has historically preceded recessions."
    ),
    # Strategies
    "rebalancing": (
        "Adjusting your portfolio back to your target allocation after market moves. "
        "If AAPL grew to 40% of your portfolio but your target is 25%, rebalancing means selling some AAPL."
    ),
    "diversification": (
        "Spreading investments across different assets, sectors, or geographies to reduce risk. "
        "The core idea: don't put all your eggs in one basket."
    ),
    "concentration risk": (
        "The risk of having too much of your portfolio in one stock, sector, or asset type. "
        "A single position >30% of portfolio is generally considered high concentration."
    ),
    "ETF": (
        "Exchange-Traded Fund — a basket of securities that trades on an exchange like a stock. "
        "VTI holds ~3,800 US stocks; BND holds thousands of US bonds. Low cost, instant diversification."
    ),
    "cost basis": (
        "The original purchase price of an investment, used to calculate capital gains/losses for taxes. "
        "If you bought AAPL at $150 and it's now $200, your cost basis is $150, gain is $50/share."
    ),
    "capital gains": (
        "Profit from selling an investment above its cost basis. "
        "Short-term (held <1 year) taxed as ordinary income; long-term (held >1 year) taxed at lower rates."
    ),
    "liquidity": (
        "How easily an investment can be sold without significantly affecting its price. "
        "Large-cap stocks like AAPL are highly liquid; small companies or real estate are less liquid."
    ),
    # Ratings / analyst terms
    "strong buy": "Analyst's highest conviction recommendation — expects significant price appreciation.",
    "buy": "Analyst expects the stock to outperform the market over the next 12 months.",
    "hold": "Analyst expects the stock to perform in line with the market — neither buy nor sell.",
    "sell": "Analyst expects the stock to underperform the market over the next 12 months.",
    "strong sell": "Analyst's lowest conviction — expects significant price decline.",
    "consensus": (
        "The average view across multiple analyst ratings. "
        "A 'Buy consensus' means most analysts covering the stock recommend buying."
    ),
    # Risk terms
    "downside risk": (
        "The potential for an investment to lose value. "
        "Quantifying downside risk helps set expectations for worst-case scenarios."
    ),
    "upside": "The potential for an investment to gain value above its current price.",
    "drawdown": (
        "The peak-to-trough decline of a portfolio or investment. "
        "A 20% drawdown means the value fell 20% from its highest point before recovering."
    ),
}

# Map lowercase/alternate forms to canonical term keys
_ALIASES: dict[str, str] = {
    "p/e": "P/E ratio",
    "pe ratio": "P/E ratio",
    "price to earnings": "P/E ratio",
    "earnings per share": "EPS",
    "eps surprise": "EPS surprise",
    "earnings surprise": "EPS surprise",
    "market capitalization": "market cap",
    "vix": "VIX",
    "10-year treasury": "10-year Treasury yield",
    "10yr treasury": "10-year Treasury yield",
    "treasury yield": "10-year Treasury yield",
    "federal funds rate": "Fed funds rate",
    "fed rate": "Fed funds rate",
    "consumer price index": "CPI",
    "exchange-traded fund": "ETF",
    "exchange traded fund": "ETF",
    "rebalance": "rebalancing",
    "diversify": "diversification",
    "cost basis": "cost basis",
    "capital gain": "capital gains",
    "basis point": "basis points",
    "bps": "basis points",
}


def extract_terms(texts: list[str]) -> dict[str, str]:
    """Scan a list of text strings and return definitions for any known terms found."""
    found: dict[str, str] = {}
    combined = " ".join(texts).lower()

    for term, definition in TERMS.items():
        pattern = re.compile(re.escape(term.lower()))
        if pattern.search(combined):
            found[term] = definition

    for alias, canonical in _ALIASES.items():
        if alias in combined and canonical not in found and canonical in TERMS:
            found[canonical] = TERMS[canonical]

    return found
