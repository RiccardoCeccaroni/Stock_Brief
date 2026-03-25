"""
ai_generator.py
Uses OpenAI to generate company descriptions and summarize revenue segments.
"""

import os
import re
import requests
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def generate_company_description(profile: dict) -> str:
    """Generate a 2-3 sentence company description based on profile data."""
    prompt = f"""Write exactly 2-3 sentences describing what this company does. 
Be factual and concise. No opinions or investment advice.

Company: {profile.get('companyName', 'Unknown')}
Ticker: {profile.get('symbol', 'N/A')}
Sector: {profile.get('sector', 'N/A')}
Industry: {profile.get('industry', 'N/A')}
Description from filing: {profile.get('description', 'N/A')[:500]}
"""
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200,
            temperature=0.3,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Company description unavailable. ({str(e)})"


def generate_sentiment_summary(ticker: str, company_name: str, articles: list) -> str:
    """Generate a market sentiment summary based on recent news articles."""
    if not articles:
        return ""

    articles_text = "\n".join(
        f"- [{item['date']}] {item['headline']} ({item['source']})"
        for item in articles
        if item.get("headline")
    )

    if not articles_text:
        return ""

    prompt = f"""Based on these recent news articles about {company_name} ({ticker}), write a 3-4 sentence factual summary of the current market sentiment. Do not give investment advice or opinions. Just summarize the tone and key themes of recent coverage.

{articles_text}"""
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=250,
            temperature=0.3,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Sentiment summary unavailable. ({str(e)})"


def generate_market_sentiment(company_name: str, ticker: str) -> tuple:
    """Generate a market sentiment summary using the Perplexity API.
    Returns (summary_text, citations_list)."""
    api_key = os.getenv("PERPLEXITY_API_KEY")
    if not api_key or api_key == "your_perplexity_api_key_here":
        return "", []

    prompt = (
        f"What is the latest news and market sentiment around {company_name} ({ticker})? "
        "Summarize in 3-4 factual sentences covering key themes from recent coverage. "
        "Do not give investment advice."
    )
    try:
        response = requests.post(
            "https://api.perplexity.ai/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": "sonar",
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=30,
        )
        if not response.ok:
            return "", []
        data = response.json()
        summary = data["choices"][0]["message"]["content"].strip()
        summary = re.sub(r'\s*\[\d+\]', '', summary)
        citations = data.get("citations", [])
        return summary, citations
    except Exception:
        return "", []


def fetch_business_model_research(company_name: str, ticker: str) -> str:
    """Fetch business model and revenue breakdown research via Perplexity API."""
    api_key = os.getenv("PERPLEXITY_API_KEY")
    if not api_key or api_key == "your_perplexity_api_key_here":
        return ""

    prompt = (
        f"Describe the business model and revenue breakdown of {company_name} ({ticker}). "
        "Cover these aspects with factual, specific information: "
        "1) Value Proposition — what problem it solves and for whom, "
        "2) Revenue Streams — how it makes money, with approximate revenue split by segment "
        "and/or geography if available, "
        "3) Customer Segments — B2B, B2C, B2G, mass market vs niche, "
        "4) Distribution & Channels — how products/services reach customers, "
        "5) Cost Structure — major costs, capital-intensive vs asset-light, "
        "6) Key Resources & Activities — essential assets and capabilities. "
        "Be factual and specific to this company. Use the most recent data available. "
        "No opinions or investment recommendations."
    )
    try:
        response = requests.post(
            "https://api.perplexity.ai/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": "sonar",
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=30,
        )
        if not response.ok:
            return ""
        data = response.json()
        text = data["choices"][0]["message"]["content"].strip()
        return re.sub(r'\s*\[\d+\]', '', text)
    except Exception:
        return ""


def fetch_revenue_deep_dive(company_name: str, ticker: str) -> str:
    """Fetch granular revenue breakdown: sub-segments, customer mix, demand drivers."""
    api_key = os.getenv("PERPLEXITY_API_KEY")
    if not api_key or api_key == "your_perplexity_api_key_here":
        return ""

    prompt = (
        f"Provide a detailed revenue deep-dive for {company_name} ({ticker}). "
        "Cover the following with the most recent data available: "
        "1) Sub-segment breakdown within each major revenue segment "
        "(e.g. for a chip company: training vs inference, or for a software company: "
        "subscription vs services vs licensing), with approximate revenue shares if known. "
        "2) Key customers and customer concentration — who are the largest buyers, "
        "what percentage of revenue do top customers represent? "
        "3) Contract structures and revenue visibility — recurring vs one-time, "
        "backlog, long-term agreements, order book. "
        "4) Growth drivers — what is fueling growth in each segment, "
        "and what are the risks to each revenue stream? "
        "Be factual and specific. Use the most recent earnings data and filings. "
        "No opinions or investment recommendations."
    )
    try:
        response = requests.post(
            "https://api.perplexity.ai/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": "sonar",
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=30,
        )
        if not response.ok:
            return ""
        data = response.json()
        text = data["choices"][0]["message"]["content"].strip()
        return re.sub(r'\s*\[\d+\]', '', text)
    except Exception:
        return ""


def fetch_competitive_moat_research(company_name: str, ticker: str) -> str:
    """Fetch competitive advantages and moat research via Perplexity API."""
    api_key = os.getenv("PERPLEXITY_API_KEY")
    if not api_key or api_key == "your_perplexity_api_key_here":
        return ""

    prompt = (
        f"Analyze the competitive advantages and moat of {company_name} ({ticker}). "
        "Cover: "
        "1) What are the company's main competitive advantages? (brand, patents, network effects, "
        "switching costs, economies of scale, regulatory barriers, etc.) "
        "2) What are the key barriers to entry in its industry? "
        "3) How defensible is its market position compared to competitors? "
        "Be factual and specific. Cite concrete examples where possible. "
        "No opinions or investment recommendations."
    )
    try:
        response = requests.post(
            "https://api.perplexity.ai/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": "sonar",
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=30,
        )
        if not response.ok:
            return ""
        data = response.json()
        text = data["choices"][0]["message"]["content"].strip()
        return re.sub(r'\s*\[\d+\]', '', text)
    except Exception:
        return ""


def fetch_risk_factors_research(company_name: str, ticker: str) -> str:
    """Fetch company-specific risk factors via Perplexity API."""
    api_key = os.getenv("PERPLEXITY_API_KEY")
    if not api_key or api_key == "your_perplexity_api_key_here":
        return ""

    prompt = (
        f"What are the most important risk factors facing {company_name} ({ticker}) right now? "
        "Cover these categories with specific, factual details: "
        "1) Regulatory & geopolitical risks — export controls, sanctions, antitrust, pending legislation. "
        "2) Customer concentration — dependence on a few large customers, revenue share of top clients. "
        "3) Supply chain dependencies — reliance on key suppliers or manufacturing partners, "
        "single points of failure. "
        "4) Competitive threats — emerging competitors, technology disruption, "
        "potential margin compression. "
        "5) Macro & cyclical risks — sensitivity to economic cycles, demand volatility, "
        "inventory risk. "
        "6) Execution risks — key-person dependency, integration of acquisitions, "
        "technology roadmap challenges. "
        "Be specific to this company. Use the most recent data, filings, and news. "
        "No opinions or investment recommendations."
    )
    try:
        response = requests.post(
            "https://api.perplexity.ai/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": "sonar",
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=30,
        )
        if not response.ok:
            return ""
        data = response.json()
        text = data["choices"][0]["message"]["content"].strip()
        return re.sub(r'\s*\[\d+\]', '', text)
    except Exception:
        return ""


def generate_risk_section(risk_research: str, company_name: str) -> str:
    """Generate the Key Risks section using OpenAI."""
    if not risk_research:
        return ""

    prompt = (
        f"Based on the following research about risks facing {company_name}, write a professional "
        "section for an investment research report called 'Key Risks'. "
        "Structure it with these bold sub-headings: "
        "**Regulatory & Geopolitical**, **Customer Concentration**, "
        "**Supply Chain**, **Competitive Threats**, **Macro & Cyclical**. "
        "Each sub-paragraph should be 2-3 sentences, factual and specific to this company. "
        "Only include a sub-heading if there is meaningful, company-specific content for it. "
        "No investment opinions or recommendations.\n\n"
        f"Research Input:\n{risk_research}"
    )
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=600,
            temperature=0.3,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Risk section unavailable. ({str(e)})"


def fetch_competitor_tickers(company_name: str, ticker: str, num_peers: int = 4) -> list:
    """Use Perplexity to identify actual competitive rivals (not just same-industry).
    Returns a list of ticker strings, excluding the company itself."""
    api_key = os.getenv("PERPLEXITY_API_KEY")
    if not api_key or api_key == "your_perplexity_api_key_here":
        return []

    prompt = (
        f"List the top {num_peers} direct public-market competitors of {company_name} ({ticker}). "
        "Focus on companies that compete for the same customers or markets, "
        "not just companies in the same industry classification. "
        "Return ONLY the US ticker symbols, one per line, no explanations. "
        "If a company trades as an ADR in the US, use the ADR ticker. "
        "Do not include ETFs, indices, or the company itself."
    )
    try:
        response = requests.post(
            "https://api.perplexity.ai/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": "sonar",
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=30,
        )
        if not response.ok:
            return []
        data = response.json()
        text = data["choices"][0]["message"]["content"].strip()
        # Parse tickers: one per line, strip whitespace/bullets/numbers
        tickers = []
        for line in text.splitlines():
            cleaned = re.sub(r'^[\s\-\d\.\)\*]+', '', line).strip()
            # Take only the first word (the ticker) in case there's extra text
            if cleaned:
                candidate = cleaned.split()[0].strip('(),:').upper()
                if candidate.isalpha() and len(candidate) <= 6 and candidate != ticker.upper():
                    tickers.append(candidate)
        return tickers[:num_peers]
    except Exception:
        return []


def generate_business_model_section(
    business_model_research: str, moat_research: str, company_name: str,
    revenue_deep_dive: str = "",
) -> str:
    """Generate the Business Model & Revenue Breakdown section using OpenAI."""
    if not business_model_research and not moat_research and not revenue_deep_dive:
        return "Business model information is not available for this company."

    revenue_input = ""
    if revenue_deep_dive:
        revenue_input = f"\n\nResearch Input 3 (Revenue Deep-Dive):\n{revenue_deep_dive}"

    prompt = (
        f"Based on the following research inputs about {company_name}, write a professional "
        "section for an investment research report called 'Business Model & Revenue Breakdown'. "
        "Structure it with these sub-paragraphs, each with a bold sub-heading: "
        "**Value Proposition**, **Revenue Streams**, **Customer Segments**, "
        "**Distribution & Channels**, **Cost Structure**, **Competitive Moat**, **Key Resources**. "
        "For **Revenue Streams**, go deep: include sub-segment breakdowns within major segments, "
        "approximate revenue shares, key customer concentration, contract structures, "
        "revenue visibility (backlog, recurring vs one-time), and growth drivers per segment. "
        "This sub-section should be the most detailed (4-6 sentences). "
        "Other sub-paragraphs should be 2-3 sentences each, factual and specific. "
        "No investment opinions or recommendations.\n\n"
        f"Research Input 1 (Business Model):\n{business_model_research}\n\n"
        f"Research Input 2 (Competitive Moat):\n{moat_research}"
        f"{revenue_input}"
    )
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=800,
            temperature=0.3,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Business model section unavailable. ({str(e)})"
