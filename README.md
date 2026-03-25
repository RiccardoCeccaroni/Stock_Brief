# Stock Brief

Enter a stock ticker, get a structured PDF and Word research report in under a minute.

<!--
![Report example](screenshot.png)
-->

## What it does

Takes a US stock ticker and generates a multi-page report covering:

- **Company Overview** — what the company does, in plain language.
- **Business Model & Revenue Breakdown** — revenue streams with sub-segment detail, customer concentration, contract structures, competitive moat, cost structure.
- **Financial Summary** — 5-year table with revenue, gross profit, operating income, net income, EPS, and free cash flow.
- **Stock Price Performance** — indexed chart vs. S&P 500.
- **Competitor Comparison** — P/E, EV/EBITDA, ROE, dividend yield. Competitors are picked by AI based on who actually competes, not just industry classification.
- **Competitive Stock Performance** — indexed price chart across the company and its peers.
- **Key Risks** — regulatory, customer concentration, supply chain, competitive threats, macro.
- **Market Sentiment** — recent news summary with source links.

Output: downloadable **PDF** and **Word (.docx)**.

## What it doesn't do

This is a summary tool, not investment research.

- No valuation model — no DCF, no comps, no target price.
- No scenario analysis — no bull/base/bear cases.
- No buy/sell/hold recommendation.
- No proprietary data — everything comes from public APIs and AI summaries.
- No real-time data — financials are annual, prices reflect most recent available.

The point is speed and structure: a consistent company overview in a minute, not a replacement for actual analysis.

## Inputs / Outputs

| | |
|---|---|
| **Input** | US stock ticker (`AAPL`, `NVDA`, `MCD`). For foreign companies, use the US ADR ticker (`LVMUY`, `TSM`). |
| **Options** | Chart period (3y / 5y / 10y), number of competitors (2–5). |
| **Output** | PDF and Word report. |

## Tech Stack

| Component | Tool |
|---|---|
| Web interface | [Streamlit](https://streamlit.io/) |
| Financial data | [Financial Modeling Prep](https://financialmodelingprep.com/) |
| Stock prices | [yfinance](https://github.com/ranaroussi/yfinance) |
| AI text generation | [OpenAI GPT-4o-mini](https://openai.com/) |
| AI research | [Perplexity Sonar](https://docs.perplexity.ai/) |
| PDF generation | [FPDF2](https://py-pdf.github.io/fpdf2/) |
| Word generation | [python-docx](https://python-docx.readthedocs.io/) |
| Charts | [Plotly](https://plotly.com/python/) |

## Setup

### 1. Clone and set up

```bash
git clone https://github.com/YOUR_USERNAME/stock-brief.git
cd stock-brief
python -m venv venv
# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure API keys

Copy `.env.example` to `.env` and add your keys:

```
FMP_API_KEY=your_key
OPENAI_API_KEY=your_key
PERPLEXITY_API_KEY=your_key
```

You'll need accounts with [Financial Modeling Prep](https://financialmodelingprep.com/) (free tier available), [OpenAI](https://platform.openai.com/), and [Perplexity](https://docs.perplexity.ai/).

### 3. Run

```bash
streamlit run app.py
```

Opens at `http://localhost:8501`.

## Deployment (Streamlit Cloud)

1. Push to GitHub.
2. Connect your repo at [share.streamlit.io](https://share.streamlit.io).
3. Set main file to `app.py`.
4. Add API keys under Settings > Secrets:
```toml
FMP_API_KEY = "your_key"
OPENAI_API_KEY = "your_key"
PERPLEXITY_API_KEY = "your_key"
```

## Limitations

- US-listed tickers only. Use ADR tickers for foreign companies.
- Annual financials only — no quarterly data.
- AI-generated text may contain inaccuracies.
- Free-tier API keys may hit rate limits. Each report makes multiple API calls.
- No caching — regenerating the same ticker costs the same.

## Disclaimer

This tool generates reports for **informational purposes only**. It is not investment advice and should not be used as the basis for any investment decision. Data comes from public APIs and AI-generated summaries, which may be incomplete or inaccurate.
