"""
data_fetcher.py
Handles all financial data retrieval from FMP API and yfinance.
"""

import requests
import yfinance as yf
import os
from dotenv import load_dotenv

load_dotenv()

FMP_API_KEY = os.getenv("FMP_API_KEY")
FMP_BASE_URL = "https://financialmodelingprep.com/stable"


def _safe_float(series, row):
    """Return float from a yfinance Series row, or None if missing/NaN."""
    import math
    try:
        v = series.loc[row]
        return None if (v is None or (isinstance(v, float) and math.isnan(v))) else float(v)
    except (KeyError, TypeError):
        return None


def _yf_income_to_fmp(df, limit: int) -> list:
    """Normalize a yfinance income_stmt DataFrame to FMP-style list of dicts."""
    results = []
    for col in list(df.columns)[:limit]:
        s = df[col]
        results.append({
            "calendarYear": str(col.year),
            "date": col.strftime("%Y-%m-%d"),
            "revenue": _safe_float(s, "Total Revenue"),
            "grossProfit": _safe_float(s, "Gross Profit"),
            "operatingIncome": _safe_float(s, "Operating Income"),
            "netIncome": _safe_float(s, "Net Income"),
            "eps": _safe_float(s, "Diluted EPS"),
        })
    return results


def _yf_cashflow_to_fmp(df, limit: int) -> list:
    """Normalize a yfinance cash_flow DataFrame to FMP-style list of dicts."""
    results = []
    for col in list(df.columns)[:limit]:
        s = df[col]
        results.append({
            "calendarYear": str(col.year),
            "date": col.strftime("%Y-%m-%d"),
            "operatingCashFlow": _safe_float(s, "Operating Cash Flow"),
            "capitalExpenditure": _safe_float(s, "Capital Expenditure"),
        })
    return results


def get_company_profile(ticker: str) -> dict:
    """Fetch company profile from FMP."""
    url = f"{FMP_BASE_URL}/profile?symbol={ticker}&apikey={FMP_API_KEY}"
    try:
        response = requests.get(url)
        data = response.json()
        if data and isinstance(data, list):
            return data[0]
    except Exception:
        pass
    return {}


def get_income_statement(ticker: str, limit: int = 5) -> list:
    """Fetch annual income statements from FMP, with yfinance fallback."""
    url = f"{FMP_BASE_URL}/income-statement?symbol={ticker}&period=annual&limit={limit}&apikey={FMP_API_KEY}"
    try:
        response = requests.get(url)
        data = response.json()
        if isinstance(data, list) and data:
            return data
    except Exception:
        pass
    # Fallback: yfinance
    try:
        df = yf.Ticker(ticker).income_stmt
        if df is not None and not df.empty:
            return _yf_income_to_fmp(df, limit)
    except Exception:
        pass
    return []


def get_balance_sheet(ticker: str, limit: int = 5) -> list:
    """Fetch annual balance sheets from FMP."""
    url = f"{FMP_BASE_URL}/balance-sheet-statement?symbol={ticker}&period=annual&limit={limit}&apikey={FMP_API_KEY}"
    try:
        response = requests.get(url)
        data = response.json()
        if isinstance(data, list):
            return data
    except Exception:
        pass
    return []


def get_cash_flow(ticker: str, limit: int = 5) -> list:
    """Fetch annual cash flow statements from FMP, with yfinance fallback."""
    url = f"{FMP_BASE_URL}/cash-flow-statement?symbol={ticker}&period=annual&limit={limit}&apikey={FMP_API_KEY}"
    try:
        response = requests.get(url)
        data = response.json()
        if isinstance(data, list) and data:
            return data
    except Exception:
        pass
    # Fallback: yfinance
    try:
        df = yf.Ticker(ticker).cash_flow
        if df is not None and not df.empty:
            return _yf_cashflow_to_fmp(df, limit)
    except Exception:
        pass
    return []


def get_key_metrics(ticker: str, limit: int = 5) -> list:
    """Fetch key metrics from FMP."""
    url = f"{FMP_BASE_URL}/key-metrics?symbol={ticker}&period=annual&limit={limit}&apikey={FMP_API_KEY}"
    try:
        response = requests.get(url)
        data = response.json()
        if isinstance(data, list):
            return data
    except Exception:
        pass
    return []


def get_ratios(ticker: str, limit: int = 1) -> list:
    """Fetch financial ratios from FMP."""
    url = f"{FMP_BASE_URL}/ratios?symbol={ticker}&period=annual&limit={limit}&apikey={FMP_API_KEY}"
    try:
        response = requests.get(url)
        data = response.json()
        if isinstance(data, list):
            return data
    except Exception:
        pass
    return []


def get_revenue_segments(ticker: str) -> dict:
    """Fetch revenue by product/geographic segment from FMP."""
    # Product segments
    url_product = f"https://financialmodelingprep.com/stable/revenue-product-segmentation?symbol={ticker}&structure=flat&period=annual&apikey={FMP_API_KEY}"
    # Geographic segments
    url_geo = f"https://financialmodelingprep.com/stable/revenue-geographic-segmentation?symbol={ticker}&structure=flat&period=annual&apikey={FMP_API_KEY}"

    product_data = []
    geo_data = []

    try:
        resp = requests.get(url_product)
        product_data = resp.json() if resp.status_code == 200 else []
    except Exception:
        pass

    try:
        resp = requests.get(url_geo)
        geo_data = resp.json() if resp.status_code == 200 else []
    except Exception:
        pass

    return {"product": product_data, "geographic": geo_data}


def get_peers(ticker: str) -> list:
    """Fetch peer/competitor tickers from FMP."""
    url = f"{FMP_BASE_URL}/stock-peers?symbol={ticker}&apikey={FMP_API_KEY}"
    try:
        response = requests.get(url)
        data = response.json()
        if data and isinstance(data, list):
            # New API returns list of peer objects with 'symbol' key
            return [peer.get("symbol") for peer in data if peer.get("symbol")]
    except Exception:
        pass
    return []


def get_peer_comparison(ticker: str, peers: list, max_peers: int = 4) -> list:
    """Fetch profiles for the company and its peers for comparison."""
    tickers_to_compare = [ticker] + peers[:max_peers]
    results = []
    for t in tickers_to_compare:
        profile = get_company_profile(t)
        if profile:
            entry = {
                "ticker": t,
                "companyName": profile.get("companyName", "N/A"),
                "mktCap": profile.get("marketCap", 0),
                "price": profile.get("price", 0),
                "sector": profile.get("sector", "N/A"),
            }
            try:
                info = yf.Ticker(t).info
                entry["peRatio"] = info.get("trailingPE") or None
                entry["evToEbitda"] = info.get("enterpriseToEbitda") or None
                entry["roe"] = info.get("returnOnEquity") or None
                # yfinance returns dividendYield as a plain % value (e.g. 0.91 = 0.91%)
                # report_generator uses is_pct=True which multiplies by 100, so normalise to decimal
                raw_yield = info.get("dividendYield")
                entry["dividendYield"] = raw_yield / 100 if raw_yield else None
                # Fall back to yfinance market cap if FMP returned zero
                if not entry["mktCap"] and info.get("marketCap"):
                    entry["mktCap"] = info.get("marketCap")
            except Exception:
                entry["peRatio"] = None
                entry["evToEbitda"] = None
                entry["roe"] = None
                entry["dividendYield"] = None
            results.append(entry)
    return results


def get_stock_news(ticker: str, limit: int = 10) -> list:
    """Fetch recent news articles for a ticker from FMP."""
    url = f"https://financialmodelingprep.com/api/v3/stock_news?tickers={ticker}&limit={limit}&apikey={FMP_API_KEY}"
    try:
        response = requests.get(url)
        data = response.json()
        if isinstance(data, list):
            articles = []
            for item in data:
                articles.append({
                    "headline": item.get("title", ""),
                    "date": item.get("publishedDate", "")[:10],
                    "source": item.get("site", ""),
                    "snippet": item.get("text", ""),
                })
            return articles
    except Exception:
        pass
    return []


def get_stock_price_history(ticker: str, period: str = "5y") -> "pd.DataFrame":
    """Fetch historical stock prices using yfinance."""
    import pandas as pd
    stock = yf.Ticker(ticker)
    hist = stock.history(period=period)
    if hist.empty:
        return pd.DataFrame()
    return hist


def get_index_history(period: str = "5y") -> "pd.DataFrame":
    """Fetch S&P 500 history for comparison."""
    import pandas as pd
    spy = yf.Ticker("^GSPC")
    hist = spy.history(period=period)
    if hist.empty:
        return pd.DataFrame()
    return hist
