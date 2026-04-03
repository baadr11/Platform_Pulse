import os
from datetime import datetime

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

N_TOTAL = 18_165_000
ALPHA_LOW_DEFAULT = 0.4
ALPHA_HIGH_DEFAULT = 1.8

_DARK = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(15,23,42,0.35)",
    font=dict(family="Tajawal, Arial", size=13, color="#cbd5e1"),
    xaxis=dict(gridcolor="rgba(255,255,255,0.05)", linecolor="rgba(255,255,255,0.08)", color="#64748b"),
    yaxis=dict(gridcolor="rgba(255,255,255,0.05)", linecolor="rgba(255,255,255,0.08)", color="#64748b"),
    legend=dict(
        orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
        bgcolor="rgba(0,0,0,0.25)", bordercolor="rgba(255,255,255,0.08)", borderwidth=1,
        font=dict(color="#94a3b8"),
    ),
    margin=dict(l=40, r=40, t=60, b=40),
    hoverlabel=dict(bgcolor="#0d1526", bordercolor="rgba(255,255,255,0.12)", font_color="#e2e8f0"),
)


def _estimate_workers(index_value: float, alpha_low: float, alpha_high: float) -> int:
    ratio = (alpha_low + (alpha_high - alpha_low) * (index_value / 100)) / 100
    return int(N_TOTAL * ratio)


@st.cache_data(ttl=3600)
def _load_composite_csv(path: str) -> pd.DataFrame:
    df = pd.read_csv(path, encoding="utf-8-sig")
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    return df.sort_values("date")


def _get_last_modified(filepath: str) -> datetime:
    try:
        return datetime.fromtimestamp(os.path.getmtime(filepath))
    except (FileNotFoundError, OSError):
        return datetime.now()


def _apply_filters(df: pd.DataFrame, filters: dict) -> pd.DataFrame:
    if not filters:
        return df

    if "city" in df.columns:
        city_val = filters.get("city", "الكل")
        if city_val == "الكل":
            national = df[df["city"] == "الكل"]
            if not national.empty:
                df = national
        else:
            mask = df["city"].astype(str).str.contains(city_val, na=False)
            if "city_ar" in df.columns:
                mask = mask | df["city_ar"].astype(str).str.contains(city_val, na=False)
            if mask.any():
                df = df[mask]

    if filters.get("sector") and filters["sector"] != "الكل" and "sector" in df.columns:
        sec = filters["sector"].replace(" ", "_")
        mask = (
            df["sector"].astype(str).str.contains(sec, na=False)
            | df["sector"].astype(str).str.contains(filters["sector"], na=False)
        )
        if mask.any():
            df = df[mask]

    if "date" in df.columns:
        df = df.copy()
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        if df["date"].dt.tz is not None:
            df["date"] = df["date"].dt.tz_convert(None)
        if filters.get("date_from"):
            df = df[df["date"] >= pd.Timestamp(filters["date_from"])]
        if filters.get("date_to"):
            df = df[df["date"] <= pd.Timestamp(filters["date_to"])]

    return df


def _build_dummy_df(alpha_low: float, alpha_high: float) -> pd.DataFrame:
    dates = pd.date_range("2025-04-01", periods=12, freq="ME")
    np.random.seed(42)
    values = 45 + np.cumsum(np.random.randn(12) * 3)
    return pd.DataFrame({
        "date": dates,
        "city": ["الكل"] * 12,
        "sector": ["الكل"] * 12,
        "index_value": values,
        "confidence_lower": values - 8,
        "confidence_upper": values + 8,
        "estimated_workers": [_estimate_workers(v, alpha_low, alpha_high) for v in values],
        "reviews_component": np.random.uniform(40, 90, 12),
        "trends_component": np.random.uniform(35, 85, 12),
        "sentiment_component": np.random.uniform(30, 80, 12),
        "spatial_component": np.random.uniform(35, 75, 12),
    })


def _render_calibration_expander() -> tuple[float, float]:
    with st.expander("⚙️ معايرة نطاق اقتصاد المنصات — ILO MENA"):
        col1, col2 = st.columns(2)
        alpha_low = col1.slider(
            "الحد الأدنى للحصة %",
            min_value=0.2, max_value=1.0,
            value=ALPHA_LOW_DEFAULT, step=0.1,
        )
        alpha_high = col2.slider(
            "الحد الأقصى للحصة %",
            min_value=1.0, max_value=3.0,
            value=ALPHA_HIGH_DEFAULT, step=0.1,
        )
        st.caption(
            f"المعادلة: {N_TOTAL:,} × "
            f"[{alpha_low:.1f}% + ({alpha_high:.1f}% − {alpha_low:.1f}%) × (المؤشر ÷ 100)]"
        )
    return alpha_low, alpha_high


def render_monthly_index(filters=None):
    composite_path = os.path.join("data", "processed", "composite_index.csv")

    alpha_low, alpha_high = _render_calibration_expander()

    if os.path.exists(composite_path):
        df = _load_composite_csv(composite_path)
        last_updated = _get_last_modified(composite_path)
        st.caption(f"آخر تحديث: {last_updated.strftime('%d %b %Y — %H:%M')}")
    else:
        df = _build_dummy_df(alpha_low, alpha_high)

    df = _apply_filters(df, filters)

    if df.empty:
        st.warning("لا توجد بيانات للمؤشر المركّب في الفترة المحددة")
        return

    try:
        from src.models.sentiment_marbert import get_model_status
        if get_model_status() == "lexicon":
            st.warning("نموذج المشاعر يعمل في وضع الاحتياط — تأكد من توافر النموذج العربي")
    except Exception:
        pass

    df = df.copy().sort_values("date")
    df["estimated_workers"] = df["index_value"].apply(
        lambda idx: _estimate_workers(idx, alpha_low, alpha_high)
    )

    latest = df.iloc[-1]
    current_value = float(latest.get("index_value", 0))
    estimated_workers = int(latest.get("estimated_workers", 0))
    ci_lower = float(latest.get("confidence_lower", current_value - 5))
    ci_upper = float(latest.get("confidence_upper", current_value + 5))

    if len(df) > 1:
        prev_value = float(df.iloc[-2].get("index_value", current_value))
        change = current_value - prev_value
        change_pct = (change / prev_value * 100) if prev_value != 0 else 0.0
    else:
        change = change_pct = 0.0

    change_pct_label = "بدون تغيير" if change_pct == 0.0 else f"{change_pct:+.1f}%"

    c1, c2, c3, c4 = st.columns(4)
    delta_color = "#00c896" if change >= 0 else "#ff6b6b"
    kpi_style = "border-radius:14px; padding:20px 16px; direction:rtl; border:1px solid rgba(255,255,255,0.07);"

    with c1:
        st.markdown(
            f'<div style="background:linear-gradient(135deg,#0f3460,#1a4a7a);{kpi_style}">'
            f'<p style="margin:0;font-size:0.78rem;color:#64748b">مؤشر نبض المنصات</p>'
            f'<h2 style="margin:8px 0 0;font-size:2.2rem;color:#f1f5f9;font-weight:800">'
            f'{current_value:.1f}</h2></div>', unsafe_allow_html=True
        )
    with c2:
        st.markdown(
            f'<div style="background:linear-gradient(135deg,rgba(0,200,150,.1),rgba(0,200,150,.05));'
            f'border:1px solid rgba(0,200,150,.2);{kpi_style}">'
            f'<p style="margin:0;font-size:0.78rem;color:#64748b">التغير الشهري</p>'
            f'<h2 style="margin:8px 0 0;font-size:2.2rem;color:{delta_color};font-weight:800">'
            f'{change_pct_label}</h2></div>', unsafe_allow_html=True
        )
    with c3:
        st.markdown(
            f'<div style="background:linear-gradient(135deg,#1e1b4b,#2d2a6e);{kpi_style}">'
            f'<p style="margin:0;font-size:0.78rem;color:#64748b">العاملون المقدّرون</p>'
            f'<h2 style="margin:8px 0 0;font-size:1.9rem;color:#f1f5f9;font-weight:800">'
            f'{estimated_workers:,}</h2></div>', unsafe_allow_html=True
        )
    with c4:
        st.markdown(
            f'<div style="background:linear-gradient(135deg,#1a1a2e,#2a2a4e);{kpi_style}">'
            f'<p style="margin:0;font-size:0.78rem;color:#64748b">فترة الثقة 95%</p>'
            f'<h2 style="margin:8px 0 0;font-size:1.6rem;color:#94a3b8;font-weight:700;'
            f'font-family:JetBrains Mono,monospace">'
            f'{ci_lower:.1f} – {ci_upper:.1f}</h2></div>', unsafe_allow_html=True
        )

    st.markdown("<br>", unsafe_allow_html=True)

    fig = go.Figure()

    if "confidence_upper" in df.columns and "confidence_lower" in df.columns:
        fig.add_trace(go.Scatter(
            x=pd.concat([df["date"], df["date"][::-1]]),
            y=pd.concat([df["confidence_upper"], df["confidence_lower"][::-1]]),
            fill="toself",
            fillcolor="rgba(79,142,247,0.08)",
            line=dict(color="rgba(0,0,0,0)"),
            name="فترة الثقة 95%",
            hoverinfo="skip",
        ))

    fig.add_trace(go.Scatter(
        x=df["date"], y=df["index_value"],
        mode="lines+markers",
        name="مؤشر نبض المنصات",
        line=dict(color="#4f8ef7", width=3),
        marker=dict(size=7, color="#4f8ef7", line=dict(color="#0d1526", width=2)),
    ))

    fig.update_layout(
        title=dict(text="تطور مؤشر نبض المنصات المركّب", font=dict(size=17, color="#f1f5f9")),
        xaxis_title="التاريخ",
        yaxis_title="قيمة المؤشر",
        yaxis_range=[0, 105],
        height=440,
        **_DARK,
    )
    st.plotly_chart(fig, use_container_width=True)

    component_cols = {
        "reviews_component": ("التقييمات", "#4f8ef7"),
        "trends_component": ("اتجاهات البحث", "#00c896"),
        "sentiment_component": ("المشاعر", "#f59e0b"),
        "spatial_component": ("المكاني", "#ff6b6b"),
        "social_component": ("الاجتماعي", "#a78bfa"),
    }

    fig_comp = go.Figure()
    for col_name, (label, color) in component_cols.items():
        if col_name in df.columns:
            fig_comp.add_trace(go.Scatter(
                x=df["date"], y=df[col_name],
                mode="lines",
                name=label,
                line=dict(color=color, width=2),
            ))

    fig_comp.update_layout(
        title=dict(text="تطور المؤشرات الفرعية", font=dict(size=16, color="#f1f5f9")),
        xaxis_title="التاريخ",
        yaxis_title="القيمة",
        yaxis_range=[0, 105],
        height=380,
        **_DARK,
    )
    st.plotly_chart(fig_comp, use_container_width=True)

    csv_data = df.to_csv(index=False, encoding="utf-8-sig")
    st.download_button(
        label="⬇ تصدير المؤشر المركب (CSV)",
        data=csv_data.encode("utf-8-sig"),
        file_name=f"platform_pulse_index_{datetime.now():%Y%m%d}.csv",
        mime="text/csv",
    )

    with st.expander("📚 مصادر البيانات"):
        st.markdown("""
| المصدر | البيانات المستخدمة |
|---|---|
| GASTAT | حجم القوى العاملة Q4-2024 |
| ILO / MENA | نطاق حصة اقتصاد المنصات 0.4%–1.8% |
| Google Play + App Store | تقييمات التطبيقات |
| Google Trends | مؤشرات الاهتمام بالبحث |
| Telegram / X | مشاعر قنوات السائقين والعمال |
        """)
