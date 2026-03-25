"""
report_generator.py
Generates a clean PDF investment research report using FPDF2.
"""

import os
import tempfile
import requests
from fpdf import FPDF
from datetime import datetime


def _sanitize_text(text: str) -> str:
    """Replace Unicode characters unsupported by Helvetica (Latin-1) with ASCII equivalents."""
    replacements = {
        '\u2013': '-',    # en-dash
        '\u2014': '-',    # em-dash
        '\u2015': '-',    # horizontal bar
        '\u2018': "'",    # left single quotation mark
        '\u2019': "'",    # right single quotation mark / apostrophe
        '\u201a': ',',    # single low quotation mark
        '\u201b': "'",    # single high-reversed quotation mark
        '\u201c': '"',    # left double quotation mark
        '\u201d': '"',    # right double quotation mark
        '\u201e': '"',    # double low quotation mark
        '\u2026': '...',  # ellipsis
        '\u2022': '-',    # bullet
        '\u2023': '-',    # triangular bullet
        '\u2043': '-',    # hyphen bullet
        '\u00a0': ' ',    # non-breaking space
        '\u00b7': '.',    # middle dot
        '\u20ac': 'EUR',  # euro sign
        '\u00a3': 'GBP',  # pound sign
        '\u00a5': 'JPY',  # yen sign
        '\u2122': 'TM',   # trade mark sign
        '\u00ae': '(R)',  # registered sign
        '\u00a9': '(c)',  # copyright sign
    }
    for char, replacement in replacements.items():
        text = text.replace(char, replacement)
    # Strip anything still outside Latin-1
    return text.encode('latin-1', errors='ignore').decode('latin-1')


def _normalize_markdown(text: str) -> str:
    """Convert markdown headings (### Foo) to bold (**Foo**) so renderers can handle them."""
    import re
    lines = text.split("\n")
    result = []
    for line in lines:
        m = re.match(r'^(#{1,6})\s+(.*)', line)
        if m:
            heading_text = m.group(2).strip()
            # Don't double-wrap if already bold
            if not heading_text.startswith("**"):
                heading_text = f"**{heading_text}**"
            result.append(heading_text)
        else:
            result.append(line)
    return "\n".join(result)


def _write_markdown(pdf, line_height: float, text: str, font_size: int):
    """Write text with **bold** markdown rendered inline. Uses pdf.write() so
    bold and regular segments flow together with automatic line wrapping."""
    parts = text.split("**")
    for i, part in enumerate(parts):
        if not part:
            continue
        pdf.set_font("Helvetica", "B" if i % 2 == 1 else "", font_size)
        pdf.write(line_height, part)
    # Leave cursor at end of last segment; caller should pdf.ln() as needed
    pdf.set_font("Helvetica", "", font_size)


def _check_space(pdf, needed_mm: float):
    """Add a new page only when remaining vertical space is less than needed_mm."""
    available = pdf.h - pdf.b_margin - pdf.get_y()
    if available < needed_mm:
        pdf.add_page()


def _add_chart_image(pdf, path: str):
    """Insert a chart image with adaptive sizing:
    - Full width (190 mm) when the image fits on the current page.
    - Scaled down proportionally to fill available space (min 55 mm tall).
    - New page first if less than 55 mm remains.
    Charts are saved at 900x400 px, giving an aspect ratio of 9:4."""
    FULL_W  = 190.0          # mm at full size
    ASPECT  = 400.0 / 900.0  # height/width ratio of the source chart
    FULL_H  = FULL_W * ASPECT   # ≈ 84.4 mm
    MIN_H   = 55.0            # mm — minimum useful chart height

    available = pdf.h - pdf.b_margin - pdf.get_y()

    if available >= FULL_H:
        # Plenty of room — render at full width
        pdf.image(path, x=10, w=FULL_W)
    elif available >= MIN_H:
        # Scale down to fill available height; centre horizontally
        fit_w = available / ASPECT
        x = (pdf.w - fit_w) / 2
        pdf.image(path, x=x, h=available)
    else:
        # Too little space — start on a fresh page at full size
        pdf.add_page()
        pdf.image(path, x=10, w=FULL_W)


def _download_logo(url: str, ticker: str) -> str:
    """Download company logo and return local path."""
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            logo_path = os.path.join(tempfile.gettempdir(), f"{ticker}_logo.png")
            with open(logo_path, "wb") as f:
                f.write(response.content)
            return logo_path
    except Exception:
        pass
    return ""


class ReportPDF(FPDF):
    """Custom PDF class with header and footer."""

    def __init__(self, company_name: str, ticker: str):
        super().__init__()
        self.company_name = company_name
        self.ticker = ticker

    def header(self):
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(120, 120, 120)
        self.cell(0, 8, f"{self.company_name} ({self.ticker}) | Investment Research Report", 0, 1, "L")
        self.set_draw_color(200, 200, 200)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(4)

    def footer(self):
        self.set_y(-20)
        self.set_draw_color(200, 200, 200)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(2)
        self.set_font("Helvetica", "I", 7)
        self.set_text_color(150, 150, 150)
        self.cell(0, 5, "This report is auto-generated for informational purposes only. It does not constitute investment advice.", 0, 1, "C")
        self.cell(0, 5, f"Generated on {datetime.now().strftime('%B %d, %Y')} | Page {self.page_no()}", 0, 0, "C")


def _fmt_number(value, decimals=1, is_pct=False, is_currency=False):
    """Format numbers for display."""
    if value is None:
        return "N/A"
    try:
        value = float(value)
    except (ValueError, TypeError):
        return "N/A"

    if is_pct:
        return f"{value * 100:.{decimals}f}%"

    if is_currency or abs(value) >= 1_000:
        if abs(value) >= 1_000_000_000_000:
            return f"${value / 1_000_000_000_000:.{decimals}f}T"
        elif abs(value) >= 1_000_000_000:
            return f"${value / 1_000_000_000:.{decimals}f}B"
        elif abs(value) >= 1_000_000:
            return f"${value / 1_000_000:.{decimals}f}M"
        else:
            return f"${value:,.0f}"
    return f"{value:.{decimals}f}"


def generate_report(
    profile: dict,
    description: str,
    business_model_section: str,
    income_statements: list,
    cash_flows: list,
    key_metrics: list,
    peer_comparison: list,
    stock_chart_path: str,
    ticker: str,
    peer_chart_path: str = "",
    sentiment_summary: str = "",
    sentiment_citations: list = None,
    risk_section: str = "",
) -> str:
    """Generate PDF report and return the file path."""

    description = _sanitize_text(description)
    business_model_section = _normalize_markdown(_sanitize_text(business_model_section))
    sentiment_summary = _sanitize_text(sentiment_summary)
    risk_section = _normalize_markdown(_sanitize_text(risk_section))

    company_name = profile.get("companyName", ticker)
    pdf = ReportPDF(company_name, ticker)
    pdf.set_auto_page_break(auto=True, margin=25)
    pdf.add_page()

    # ── LOGO + TITLE ──
    logo_path = ""
    if profile.get("image"):
        logo_path = _download_logo(profile["image"], ticker)

    # Position for logo and title side by side
    start_y = pdf.get_y()
    logo_width = 0

    if logo_path and os.path.exists(logo_path):
        try:
            pdf.image(logo_path, x=10, y=start_y, w=20)
            logo_width = 25  # logo width + spacing
        except Exception:
            logo_width = 0

    # Title next to logo
    pdf.set_xy(10 + logo_width, start_y)
    pdf.set_font("Helvetica", "B", 22)
    pdf.set_text_color(20, 20, 20)
    pdf.multi_cell(190 - logo_width, 12, company_name, 0, "L")

    # Subtitle
    pdf.set_x(10 + logo_width)
    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(80, 80, 80)
    subtitle_parts = []
    if profile.get("symbol"):
        subtitle_parts.append(profile["symbol"])
    if profile.get("exchange"):
        subtitle_parts.append(profile["exchange"])
    if profile.get("sector"):
        subtitle_parts.append(profile["sector"])
    if profile.get("industry"):
        subtitle_parts.append(profile["industry"])
    pdf.cell(0, 7, " | ".join(subtitle_parts), 0, 1, "L")

    # Generation date
    pdf.set_x(10 + logo_width)
    pdf.set_font("Helvetica", "I", 9)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 6, f"Report generated: {datetime.now().strftime('%B %d, %Y')}", 0, 1, "L")

    # Ensure we're below the logo
    if logo_width > 0:
        pdf.set_y(max(pdf.get_y(), start_y + 22))

    # Key stats row
    pdf.ln(3)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(60, 60, 60)

    # Format employee count with thousand separators
    employees = profile.get('fullTimeEmployees', 'N/A')
    if employees and employees != 'N/A':
        try:
            employees = f"{int(employees):,}"
        except (ValueError, TypeError):
            pass

    stats_text = (
        f"Market Cap: {_fmt_number(profile.get('marketCap'), is_currency=True)}    "
        f"Price: ${profile.get('price', 'N/A')}    "
        f"Currency: {profile.get('currency', 'N/A')}    "
        f"Employees: {employees}"
    )
    pdf.cell(0, 6, stats_text, 0, 1, "L")
    pdf.ln(6)

    # ── SECTION 1: COMPANY OVERVIEW ──
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(30, 30, 30)
    pdf.cell(0, 8, "1. Company Overview", 0, 1, "L")
    pdf.set_draw_color(50, 100, 200)
    pdf.set_line_width(0.5)
    pdf.line(10, pdf.get_y(), 60, pdf.get_y())
    pdf.ln(4)

    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(40, 40, 40)
    pdf.multi_cell(0, 5.5, description)
    pdf.ln(4)

    # ── SECTION 2: BUSINESS MODEL & REVENUE BREAKDOWN ──
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(30, 30, 30)
    pdf.cell(0, 8, "2. Business Model & Revenue Breakdown", 0, 1, "L")
    pdf.set_draw_color(50, 100, 200)
    pdf.set_line_width(0.5)
    pdf.line(10, pdf.get_y(), 60, pdf.get_y())
    pdf.ln(4)

    pdf.set_text_color(40, 40, 40)
    for paragraph in business_model_section.split("\n\n"):
        paragraph = paragraph.strip()
        if not paragraph:
            continue
        # Skip if the AI repeated the section title
        stripped = paragraph.lstrip("#* ").strip()
        if stripped.lower().startswith("business model") and "revenue" in stripped.lower():
            continue
        _check_space(pdf, 15)
        _write_markdown(pdf, 5.5, paragraph, 10)
        pdf.ln(8)

    pdf.ln(2)

    # ── SECTION 3: FINANCIAL SUMMARY TABLE ──
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(30, 30, 30)
    pdf.cell(0, 8, "3. Financial Summary", 0, 1, "L")
    pdf.set_draw_color(50, 100, 200)
    pdf.line(10, pdf.get_y(), 60, pdf.get_y())
    pdf.ln(4)

    if income_statements:
        # Build table data
        years = []
        revenues = []
        gross_profits = []
        operating_incomes = []
        net_incomes = []
        eps_values = []
        fcf_values = []

        for i, stmt in enumerate(reversed(income_statements)):
            year = stmt.get("calendarYear", stmt.get("date", "N/A")[:4])
            years.append(str(year))
            revenues.append(stmt.get("revenue"))
            gross_profits.append(stmt.get("grossProfit"))
            operating_incomes.append(stmt.get("operatingIncome"))
            net_incomes.append(stmt.get("netIncome"))
            eps_values.append(stmt.get("eps"))

        # Get FCF from cash flow
        for cf in reversed(cash_flows):
            fcf = None
            ocf = cf.get("operatingCashFlow", 0) or 0
            capex = cf.get("capitalExpenditure", 0) or 0
            if ocf:
                fcf = ocf + capex  # capex is typically negative
            fcf_values.append(fcf)

        # Pad if different lengths
        while len(fcf_values) < len(years):
            fcf_values.append(None)

        rows = [
            ("Revenue", revenues, True),
            ("Gross Profit", gross_profits, True),
            ("Operating Income", operating_incomes, True),
            ("Net Income", net_incomes, True),
            ("EPS", eps_values, False),
            ("Free Cash Flow", fcf_values, True),
        ]

        # Table dimensions
        label_w = 35
        n_cols = len(years)
        col_w = (190 - label_w) / n_cols

        # Header row
        pdf.set_font("Helvetica", "B", 8)
        pdf.set_fill_color(40, 60, 120)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(label_w, 7, "Metric", 1, 0, "C", True)
        for y in years:
            pdf.cell(col_w, 7, y, 1, 0, "C", True)
        pdf.ln()

        # Data rows
        pdf.set_font("Helvetica", "", 8)
        for idx, (label, values, is_curr) in enumerate(rows):
            if idx % 2 == 0:
                pdf.set_fill_color(240, 243, 250)
            else:
                pdf.set_fill_color(255, 255, 255)
            pdf.set_text_color(40, 40, 40)
            pdf.cell(label_w, 6.5, label, 1, 0, "L", True)
            for v in values:
                if is_curr:
                    display = _fmt_number(v, is_currency=True)
                else:
                    display = f"{v:.2f}" if v is not None else "N/A"
                pdf.cell(col_w, 6.5, display, 1, 0, "C", True)
            pdf.ln()

    else:
        pdf.set_font("Helvetica", "I", 10)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(0, 8, "Financial statement data unavailable for this ticker.", 0, 1, "L")

    pdf.ln(6)

    # ── SECTION 4: STOCK PRICE CHART ──
    # Need room for heading (~20 mm) + at least the minimum chart height
    _check_space(pdf, 20 + 55)
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(30, 30, 30)
    pdf.cell(0, 8, "4. Stock Price Performance", 0, 1, "L")
    pdf.set_draw_color(50, 100, 200)
    pdf.line(10, pdf.get_y(), 60, pdf.get_y())
    pdf.ln(4)

    if stock_chart_path and os.path.exists(stock_chart_path):
        _add_chart_image(pdf, stock_chart_path)
    else:
        pdf.set_font("Helvetica", "I", 10)
        pdf.cell(0, 8, "Stock price chart unavailable.", 0, 1, "L")

    pdf.ln(6)

    # ── SECTION 5: COMPETITOR COMPARISON ──
    # heading (12mm) + header row (7mm) + data rows (6.5mm each) + padding (8mm)
    n_rows = len(peer_comparison) if peer_comparison else 1
    table_height = 12 + 7 + (n_rows * 6.5) + 8
    _check_space(pdf, table_height)
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(30, 30, 30)
    pdf.cell(0, 8, "5. Competitor Comparison", 0, 1, "L")
    pdf.set_draw_color(50, 100, 200)
    pdf.line(10, pdf.get_y(), 60, pdf.get_y())
    pdf.ln(4)

    if peer_comparison:
        headers = ["Company", "Ticker", "Mkt Cap", "P/E", "EV/EBITDA", "ROE", "Div Yield"]
        col_widths = [40, 18, 28, 22, 24, 22, 22]

        # Header
        pdf.set_font("Helvetica", "B", 8)
        pdf.set_fill_color(40, 60, 120)
        pdf.set_text_color(255, 255, 255)
        for i, h in enumerate(headers):
            pdf.cell(col_widths[i], 7, h, 1, 0, "C", True)
        pdf.ln()

        # Data
        pdf.set_font("Helvetica", "", 8)
        for idx, peer in enumerate(peer_comparison):
            if idx % 2 == 0:
                pdf.set_fill_color(240, 243, 250)
            else:
                pdf.set_fill_color(255, 255, 255)
            pdf.set_text_color(40, 40, 40)

            name = peer.get("companyName", "N/A")
            if len(name) > 22:
                name = name[:20] + ".."

            row_data = [
                name,
                peer.get("ticker", "N/A"),
                _fmt_number(peer.get("mktCap"), is_currency=True),
                f"{peer.get('peRatio', 0):.1f}x" if peer.get("peRatio") else "N/A",
                f"{peer.get('evToEbitda', 0):.1f}x" if peer.get("evToEbitda") else "N/A",
                _fmt_number(peer.get("roe"), is_pct=True) if peer.get("roe") else "N/A",
                _fmt_number(peer.get("dividendYield"), is_pct=True) if peer.get("dividendYield") else "N/A",
            ]

            for i, val in enumerate(row_data):
                pdf.cell(col_widths[i], 6.5, str(val), 1, 0, "C", True)
            pdf.ln()
    else:
        pdf.set_font("Helvetica", "I", 10)
        pdf.cell(0, 8, "Peer comparison data unavailable.", 0, 1, "L")

    # ── SECTION 6: COMPETITIVE STOCK PERFORMANCE ──
    pdf.ln(8)
    _check_space(pdf, 20 + 55)
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(30, 30, 30)
    pdf.cell(0, 8, "6. Competitive Stock Performance", 0, 1, "L")
    pdf.set_draw_color(50, 100, 200)
    pdf.set_line_width(0.5)
    pdf.line(10, pdf.get_y(), 60, pdf.get_y())
    pdf.ln(4)

    if peer_chart_path and os.path.exists(peer_chart_path):
        _add_chart_image(pdf, peer_chart_path)
    else:
        pdf.set_font("Helvetica", "I", 10)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(0, 8, "Competitive price chart unavailable.", 0, 1, "L")

    pdf.ln(6)

    # ── SECTION 7: KEY RISKS ──
    if risk_section:
        pdf.ln(6)
        _check_space(pdf, 20)
        pdf.set_font("Helvetica", "B", 13)
        pdf.set_text_color(30, 30, 30)
        pdf.cell(0, 8, "7. Key Risks", 0, 1, "L")
        pdf.set_draw_color(50, 100, 200)
        pdf.set_line_width(0.5)
        pdf.line(10, pdf.get_y(), 60, pdf.get_y())
        pdf.ln(4)

        pdf.set_text_color(40, 40, 40)
        for paragraph in risk_section.split("\n\n"):
            paragraph = paragraph.strip()
            if not paragraph:
                continue
            stripped = paragraph.lstrip("#* ").strip()
            if stripped.lower().startswith("key risk"):
                continue
            _check_space(pdf, 15)
            _write_markdown(pdf, 5.5, paragraph, 10)
            pdf.ln(8)

    # ── SECTION 8: MARKET SENTIMENT ──
    if sentiment_summary:
        pdf.ln(6)
        pdf.set_font("Helvetica", "B", 13)
        pdf.set_text_color(30, 30, 30)
        pdf.cell(0, 8, "8. Market Sentiment and Recent News", 0, 1, "L")
        pdf.set_draw_color(50, 100, 200)
        pdf.set_line_width(0.5)
        pdf.line(10, pdf.get_y(), 60, pdf.get_y())
        pdf.ln(4)

        pdf.set_text_color(40, 40, 40)
        _write_markdown(pdf, 5.5, sentiment_summary, 10)
        pdf.ln(6)

        if sentiment_citations:
            pdf.set_font("Helvetica", "B", 8)
            pdf.set_text_color(80, 80, 80)
            pdf.cell(0, 5, "Sources:", 0, 1, "L")
            pdf.ln(1)
            pdf.set_font("Helvetica", "I", 7)
            pdf.set_text_color(100, 100, 100)
            for i, url in enumerate(sentiment_citations, 1):
                display = url if len(url) <= 90 else url[:87] + "..."
                pdf.multi_cell(0, 4.5, f"[{i}]  {display}")
                pdf.ln(0.5)

    # ── SAVE ──
    output_path = os.path.join(tempfile.gettempdir(), f"{ticker}_report.pdf")
    pdf.output(output_path)
    return output_path
