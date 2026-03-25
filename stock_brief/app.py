"""
app.py
Streamlit web interface for Stock Brief.
"""

import streamlit as st
import os
import time
import base64
from dotenv import load_dotenv

load_dotenv()

# ── Page config ──
st.set_page_config(
    page_title="Stock Brief",
    page_icon="",
    layout="centered",
)

# ── Custom styling ──
st.markdown("""
<style>
    .stApp, .stApp > header, [data-testid="stAppViewContainer"],
    [data-testid="stHeader"], [data-testid="stToolbar"],
    [data-testid="stSidebar"], [data-testid="stAppViewBlockContainer"],
    section[data-testid="stMain"], .main, .block-container {
        background-color: #ffffff !important;
    }
    .stApp {
        max-width: 800px;
        margin: 0 auto;
    }
    .main-title {
        font-size: 2.5rem !important;
        font-weight: 900 !important;
        color: #1a1a1a !important;
        text-align: center !important;
        margin-bottom: 0.3rem !important;
        letter-spacing: -1px !important;
        line-height: 1.1 !important;
    }
    .subtitle {
        font-size: 0.95rem;
        color: #555555;
        text-align: center;
        margin-top: 0.6rem;
        margin-bottom: 2.5rem;
        line-height: 1.7;
    }
    .disclaimer {
        font-size: 0.75rem;
        color: #adb5bd;
        text-align: center;
        margin-top: 2rem;
        padding-top: 1rem;
        border-top: 1px solid #e9ecef;
    }
</style>
""", unsafe_allow_html=True)

# ── Header ──
st.markdown('<p class="main-title">Stock Brief</p>', unsafe_allow_html=True)
st.markdown(
    '<p class="subtitle">'
    "A starting point for analysts: generate an AI-assisted research report (PDF &amp; Word) "
    "that compiles key financials, competitor benchmarks, and market sentiment for any public company.<br><br>"
    "<strong>Supported tickers:</strong> US-listed stocks (NYSE / NASDAQ) work best — e.g. <code>AAPL</code>, <code>MSFT</code>, <code>MCD</code>. "
    "For foreign companies, use their <strong>US ADR ticker</strong> — e.g. <code>LVMUY</code> (LVMH), <code>NSRGY</code> (Nestle), <code>TSM</code> (TSMC). "
    "Exchange-suffixed formats like <code>MC.PA</code> are not supported."
    "</p>",
    unsafe_allow_html=True,
)

# ── Input form ──
col1, col2 = st.columns([2, 1])
with col1:
    ticker = st.text_input(
        "Stock Ticker (Yahoo Finance format)",
        placeholder="e.g. AAPL, MSFT, MCD, LVMUY",
        max_chars=10,
    ).upper().strip()

with col2:
    period = st.selectbox(
        "Chart Period",
        options=["3y", "5y", "10y"],
        index=1,
    )

num_peers = st.slider("Number of competitors to compare", min_value=2, max_value=5, value=3)

generate = st.button("Generate Report", type="primary", use_container_width=True)

# ── Report generation ──
if generate:
    if not ticker:
        st.error("Please enter a ticker symbol.")
        st.stop()

    # Check API keys
    if not os.getenv("FMP_API_KEY") or os.getenv("FMP_API_KEY") == "your_fmp_api_key_here":
        st.error("FMP API key not configured. Please add it to your .env file.")
        st.stop()
    if not os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY") == "your_openai_api_key_here":
        st.error("OpenAI API key not configured. Please add it to your .env file.")
        st.stop()

    # Import modules here to avoid slow startup
    from data_fetcher import (
        get_company_profile,
        get_income_statement,
        get_cash_flow,
        get_key_metrics,
        get_peers,
        get_peer_comparison,
        get_stock_price_history,
        get_index_history,
    )
    from ai_generator import (
        generate_company_description,
        fetch_business_model_research,
        fetch_revenue_deep_dive,
        fetch_competitive_moat_research,
        fetch_risk_factors_research,
        fetch_competitor_tickers,
        generate_business_model_section,
        generate_risk_section,
        generate_market_sentiment,
    )
    from chart_generator import create_stock_chart, create_peer_chart
    from report_generator import generate_report
    from word_report_generator import generate_word_report

    progress = st.progress(0, text="Starting...")

    try:
        # Step 1: Company profile
        progress.progress(10, text="Fetching company profile...")
        profile = get_company_profile(ticker)
        if not profile:
            st.error(f"Could not find company data for '{ticker}'. Please check the ticker symbol.")
            st.stop()

        company_name = profile.get("companyName", ticker)
        st.info(f"Generating report for **{company_name}** ({ticker})...")

        # Step 2: Financial data
        progress.progress(20, text="Fetching financial statements...")
        income_stmts = get_income_statement(ticker, limit=5)
        cash_flows = get_cash_flow(ticker, limit=5)
        metrics = get_key_metrics(ticker, limit=5)

        # Step 3: AI-generated content
        progress.progress(30, text="Generating company description (AI)...")
        description = generate_company_description(profile)

        progress.progress(38, text="Researching business model (AI)...")
        business_model_research = fetch_business_model_research(company_name, ticker)

        progress.progress(42, text="Researching revenue breakdown (AI)...")
        revenue_deep_dive = fetch_revenue_deep_dive(company_name, ticker)

        progress.progress(50, text="Researching competitive moat (AI)...")
        moat_research = fetch_competitive_moat_research(company_name, ticker)

        progress.progress(58, text="Generating business model section (AI)...")
        business_model_section = generate_business_model_section(
            business_model_research, moat_research, company_name,
            revenue_deep_dive=revenue_deep_dive,
        )

        progress.progress(62, text="Researching risk factors (AI)...")
        risk_research = fetch_risk_factors_research(company_name, ticker)
        risk_section = generate_risk_section(risk_research, company_name)

        progress.progress(68, text="Analyzing market sentiment (AI)...")
        sentiment_summary, sentiment_citations = generate_market_sentiment(company_name, ticker)

        # Step 5: Peers (AI-curated, with FMP fallback)
        progress.progress(74, text="Identifying competitors (AI)...")
        peers = fetch_competitor_tickers(company_name, ticker, num_peers=num_peers)
        if not peers:
            peers = get_peers(ticker)
        if not peers:
            peer_comparison = []
        else:
            peer_comparison = get_peer_comparison(ticker, peers, max_peers=num_peers)

        # Step 7: Stock price chart
        progress.progress(78, text="Building stock price chart...")
        stock_data = get_stock_price_history(ticker, period=period)
        index_data = get_index_history(period=period)
        chart_path = create_stock_chart(stock_data, index_data, ticker=ticker, period=period)

        # Step 8: Peer comparison chart
        progress.progress(86, text="Building competitive price chart...")
        peer_tickers = [p["ticker"] for p in peer_comparison] if peer_comparison else []
        peer_chart_path = create_peer_chart(peer_tickers, period, ticker) if peer_tickers else ""

        # Step 9: Generate PDF
        progress.progress(90, text="Generating PDF report...")
        pdf_path = generate_report(
            profile=profile,
            description=description,
            business_model_section=business_model_section,
            income_statements=income_stmts,
            cash_flows=cash_flows,
            key_metrics=metrics,
            peer_comparison=peer_comparison,
            stock_chart_path=chart_path,
            ticker=ticker,
            peer_chart_path=peer_chart_path,
            sentiment_summary=sentiment_summary,
            sentiment_citations=sentiment_citations,
            risk_section=risk_section,
        )

        # Step 10: Generate Word report
        progress.progress(95, text="Generating Word report...")
        docx_path = generate_word_report(
            profile=profile,
            description=description,
            business_model_section=business_model_section,
            income_statements=income_stmts,
            cash_flows=cash_flows,
            key_metrics=metrics,
            peer_comparison=peer_comparison,
            stock_chart_path=chart_path,
            ticker=ticker,
            peer_chart_path=peer_chart_path,
            sentiment_summary=sentiment_summary,
            sentiment_citations=sentiment_citations,
            risk_section=risk_section,
        )

        progress.progress(100, text="Done!")
        time.sleep(0.5)
        progress.empty()

        # Read file bytes and store in session state so they persist across reruns
        with open(pdf_path, "rb") as pdf_file:
            pdf_bytes = pdf_file.read()
        with open(docx_path, "rb") as docx_file:
            docx_bytes = docx_file.read()

        # Render PDF pages as images for preview
        preview_images = []
        try:
            import fitz  # PyMuPDF
            pdf_doc = fitz.open(pdf_path)
            for page_num in range(len(pdf_doc)):
                page = pdf_doc[page_num]
                pix = page.get_pixmap(dpi=150)
                preview_images.append(pix.tobytes("png"))
            pdf_doc.close()
        except ImportError:
            pass

        st.session_state["report"] = {
            "ticker": ticker,
            "company_name": company_name,
            "pdf_bytes": pdf_bytes,
            "docx_bytes": docx_bytes,
            "preview_images": preview_images,
        }

    except Exception as e:
        progress.empty()
        st.error(f"An error occurred: {str(e)}")
        st.exception(e)

# ── Display results (persists across reruns) ──
if "report" in st.session_state:
    report = st.session_state["report"]
    r_ticker = report["ticker"]
    company_name = report["company_name"]
    pdf_bytes = report["pdf_bytes"]
    docx_bytes = report["docx_bytes"]
    preview_images = report["preview_images"]

    st.success(f"Report for {company_name} generated successfully!")

    # Download buttons (top) — side by side
    dl_top_1, dl_top_2 = st.columns(2)
    with dl_top_1:
        st.download_button(
            label="Download PDF Report",
            data=pdf_bytes,
            file_name=f"{r_ticker}_Research_Report.pdf",
            mime="application/pdf",
            type="primary",
            use_container_width=True,
        )
    with dl_top_2:
        st.download_button(
            label="Download Word Report",
            data=docx_bytes,
            file_name=f"{r_ticker}_Research_Report.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            type="primary",
            use_container_width=True,
        )

    # Inline PDF preview as page images
    if preview_images:
        st.markdown("---")
        st.markdown("### Report Preview")
        for img_bytes in preview_images:
            st.image(img_bytes, use_container_width=True)


# ── Footer ──
st.markdown(
    '<p class="disclaimer">'
    "This tool generates factual reports using public financial data. "
    "It does not provide investment advice or recommendations. "
    "Data sources: Financial Modeling Prep, Yahoo Finance. AI: OpenAI."
    "</p>",
    unsafe_allow_html=True,
)
