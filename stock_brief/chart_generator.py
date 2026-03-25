"""
chart_generator.py
Creates stock price charts using Plotly, exports as images for PDF.
"""

import os
import tempfile
import yfinance as yf
import plotly.graph_objects as go


def create_stock_chart(stock_data, index_data=None, ticker: str = "", period: str = "5y") -> str:
    """Create a stock price chart and save as PNG. Returns file path."""

    if stock_data.empty:
        return ""

    fig = go.Figure()

    # Normalize both to 100 for comparison
    stock_normalized = (stock_data["Close"] / stock_data["Close"].iloc[0]) * 100
    fig.add_trace(go.Scatter(
        x=stock_data.index,
        y=stock_normalized,
        mode="lines",
        name=ticker,
        line=dict(color="#2962FF", width=2),
    ))

    if index_data is not None and not index_data.empty:
        # Align index data to same start date
        start_date = stock_data.index[0]
        index_filtered = index_data[index_data.index >= start_date]
        if not index_filtered.empty:
            index_normalized = (index_filtered["Close"] / index_filtered["Close"].iloc[0]) * 100
            fig.add_trace(go.Scatter(
                x=index_filtered.index,
                y=index_normalized,
                mode="lines",
                name="S&P 500",
                line=dict(color="#B0BEC5", width=1.5, dash="dot"),
            ))

    fig.update_layout(
        title=f"{ticker} vs S&P 500 — Indexed to 100 ({period})",
        xaxis_title="",
        yaxis_title="Indexed Price (Start = 100)",
        template="plotly_white",
        height=400,
        width=900,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        margin=dict(l=50, r=30, t=60, b=40),
        font=dict(size=11),
    )

    chart_path = os.path.join(tempfile.gettempdir(), f"{ticker}_chart.png")
    fig.write_image(chart_path, scale=2)
    return chart_path


def create_peer_chart(tickers: list, period: str, main_ticker: str) -> str:
    """Create an indexed price comparison chart for the main company and its peers.
    Each line is indexed to 100 at its own start date. Returns file path or ''."""

    # Distinct colors: main ticker gets blue, peers get a rotating palette
    palette = ["#2962FF", "#E53935", "#2E7D32", "#F57C00", "#6A1B9A", "#00838F"]

    fig = go.Figure()
    excluded = []
    plotted = 0

    for i, t in enumerate(tickers):
        try:
            data = yf.Ticker(t).history(period=period)
            if data.empty or len(data) < 2:
                excluded.append(t)
                continue
            normalized = (data["Close"] / data["Close"].iloc[0]) * 100
            fig.add_trace(go.Scatter(
                x=data.index,
                y=normalized,
                mode="lines",
                name=t,
                line=dict(
                    color=palette[i % len(palette)],
                    width=2.5 if t == main_ticker else 1.5,
                ),
            ))
            plotted += 1
        except Exception:
            excluded.append(t)

    if plotted == 0:
        return ""

    fig.update_layout(
        title=f"Competitive Stock Performance — Indexed to 100 ({period})",
        xaxis_title="",
        yaxis_title="Indexed Price (Start = 100)",
        template="plotly_white",
        height=400,
        width=900,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
        ),
        margin=dict(l=50, r=30, t=60, b=50 if excluded else 40),
        font=dict(size=11),
    )

    if excluded:
        fig.add_annotation(
            text=f"Excluded (no data available): {', '.join(excluded)}",
            xref="paper", yref="paper",
            x=0, y=-0.12,
            showarrow=False,
            font=dict(size=9, color="#888888"),
            xanchor="left",
        )

    chart_path = os.path.join(tempfile.gettempdir(), f"{main_ticker}_peer_chart.png")
    fig.write_image(chart_path, scale=2)
    return chart_path
