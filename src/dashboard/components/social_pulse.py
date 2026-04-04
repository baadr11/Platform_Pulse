from __future__ import annotations
import os
import sys
from typing import Optional

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

SOCIAL_RAW_PATH     = os.path.join("data", "raw",       "social_raw.csv")
SOCIAL_SAMPLE_PATH  = os.path.join("data", "sample",    "sample_social.csv")
TWITTER_SAMPLE_PATH = os.path.join("data", "sample",    "twitter_sample.csv")
COMPOSITE_PATH      = os.path.join("data", "processed", "composite_index.csv")
SOCIAL_AGG_PATH     = os.path.join("data", "processed", "social_sentiment_agg.csv")

POSITIVE_KW = ["ممتاز","رائع","سريع","شكرا","جيد","ممتازة","حلو","زين","مناسب","excellent","great","fast","good","love"]
NEGATIVE_KW = ["سيء","بطيء","مرتفع","غالي","مشكلة","تأخر","يلغي","رفض","bad","slow","expensive","late","problem"]

_DARK = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(15,23,42,0.35)",
    font=dict(family="Tajawal, Arial", size=13, color="#cbd5e1"),
    legend=dict(
        orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
        bgcolor="rgba(0,0,0,0.25)", bordercolor="rgba(255,255,255,0.08)", borderwidth=1,
        font=dict(color="#94a3b8"),
    ),
    margin=dict(l=30, r=30, t=50, b=30),
    hoverlabel=dict(bgcolor="#0d1526", bordercolor="rgba(255,255,255,0.12)", font_color="#e2e8f0"),
)

_AXES = dict(gridcolor="rgba(255,255,255,0.05)", linecolor="rgba(255,255,255,0.08)", color="#64748b")


def _apply_axes(fig):
    fig.update_xaxes(**_AXES)
    fig.update_yaxes(**_AXES)
    return fig


def _polarity(text: str) -> float:
    t = str(text).lower()
    pos = sum(1 for w in POSITIVE_KW if w in t)
    neg = sum(1 for w in NEGATIVE_KW if w in t)
    if pos + neg == 0:
        return 0.5
    return pos / (pos + neg)


@st.cache_data(ttl=3600)
def _load_social_raw() -> Optional[pd.DataFrame]:
    frames = []
    for path in [SOCIAL_RAW_PATH, SOCIAL_SAMPLE_PATH, TWITTER_SAMPLE_PATH]:
        if not os.path.exists(path):
            continue
        try:
            df = pd.read_csv(path, encoding="utf-8-sig")
            if "date" not in df.columns or df.empty:
                continue
            df["date"] = pd.to_datetime(df["date"], errors="coerce")
            df = df.dropna(subset=["date"])
            if not df.empty:
                frames.append(df)
        except Exception:
            continue
        if path == SOCIAL_RAW_PATH and frames:
            break
    if not frames:
        return None
    combined = pd.concat(frames, ignore_index=True)
    if "message_id" in combined.columns and "platform" in combined.columns:
        combined = combined.drop_duplicates(subset=["platform", "message_id"])
    return combined.sort_values("date", ascending=False).reset_index(drop=True)


@st.cache_data(ttl=3600)
def _aggregate_from_df(df_json: str) -> pd.DataFrame:
    from io import StringIO
    df = pd.read_json(StringIO(df_json), orient="records")
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date", "text"])
    df["polarity"] = df["text"].apply(_polarity)
    df["month"]    = df["date"].dt.to_period("M").dt.to_timestamp()
    group_cols     = [c for c in ["month", "sector"] if c in df.columns]
    agg = (
        df.groupby(group_cols)
        .agg(mean_polarity=("polarity", "mean"), message_count=("text", "count"))
        .reset_index()
        .rename(columns={"month": "date"})
    )
    agg["social_score"] = (agg["mean_polarity"] * 100).round(2)
    return agg[["date", "sector", "social_score", "message_count"]]


@st.cache_data(ttl=3600)
def _load_composite_social() -> Optional[pd.DataFrame]:
    if not os.path.exists(COMPOSITE_PATH):
        return None
    try:
        df = pd.read_csv(COMPOSITE_PATH, encoding="utf-8-sig")
        if "social_component" not in df.columns:
            return None
        national = df[df["city"] == "الكل"].copy()
        national["date"] = pd.to_datetime(national["date"], errors="coerce")
        national = national.dropna(subset=["date"]).sort_values("date")
        return national[["date", "social_component"]]
    except Exception:
        return None


def _render_kpi_cards(raw_df: pd.DataFrame) -> None:
    total        = len(raw_df)
    pos_count    = raw_df["text"].apply(_polarity).gt(0.5).sum() if "text" in raw_df.columns else 0
    pos_pct      = round(pos_count / total * 100, 1) if total > 0 else 0
    top_platform = raw_df["platform"].value_counts().idxmax() if "platform" in raw_df.columns and total > 0 else "—"
    top_sector   = raw_df["sector"].value_counts().idxmax()   if "sector"   in raw_df.columns and total > 0 else "—"

    s = "border-radius:14px;padding:20px 16px;direction:rtl;color:white;border:1px solid rgba(255,255,255,0.07);margin-bottom:4px;"
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f'<div style="background:linear-gradient(135deg,#0f3460,#1a4a7a);{s}"><p style="margin:0;font-size:.78rem;color:#64748b">إجمالي الرسائل</p><h2 style="margin:8px 0 4px;font-size:2rem;font-weight:800;color:#f1f5f9">{total:,}</h2><p style="margin:0;font-size:.72rem;color:#475569">Telegram + Twitter/X</p></div>', unsafe_allow_html=True)
    with c2:
        color = "#00c896" if pos_pct >= 50 else "#ff6b6b"
        st.markdown(f'<div style="background:linear-gradient(135deg,{color}18,{color}08);border:1px solid {color}30;{s}"><p style="margin:0;font-size:.78rem;color:#64748b">نسبة الإيجابية</p><h2 style="margin:8px 0 4px;font-size:2rem;font-weight:800;color:{color}">{pos_pct}%</h2><p style="margin:0;font-size:.72rem;color:#475569">تحليل الكلمات المفتاحية</p></div>', unsafe_allow_html=True)
    with c3:
        st.markdown(f'<div style="background:linear-gradient(135deg,#2d1b4e,#3d2a6e);{s}"><p style="margin:0;font-size:.78rem;color:#64748b">المنصة الأعلى نشاطاً</p><h2 style="margin:8px 0 4px;font-size:1.5rem;font-weight:800;color:#a78bfa">{top_platform}</h2><p style="margin:0;font-size:.72rem;color:#475569">حجم الرسائل</p></div>', unsafe_allow_html=True)
    with c4:
        st.markdown(f'<div style="background:linear-gradient(135deg,#2d1b00,#3d2800);{s}"><p style="margin:0;font-size:.78rem;color:#64748b">القطاع الأكثر نشاطاً</p><h2 style="margin:8px 0 4px;font-size:1.5rem;font-weight:800;color:#f59e0b">{top_sector}</h2><p style="margin:0;font-size:.72rem;color:#475569">عدد القنوات</p></div>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)


def _render_volume_chart(raw_df: pd.DataFrame) -> None:
    if "date" not in raw_df.columns:
        return
    df = raw_df.copy()
    df["date"]  = pd.to_datetime(df["date"], errors="coerce")
    df          = df.dropna(subset=["date"])
    df["month"] = df["date"].dt.to_period("M").dt.to_timestamp()
    group_cols  = [c for c in ["month", "sector"] if c in df.columns]
    vol = df.groupby(group_cols).size().reset_index(name="count")
    fig = px.bar(
        vol, x="month", y="count",
        color="sector" if "sector" in vol.columns else None,
        labels={"month": "الشهر", "count": "عدد الرسائل", "sector": "القطاع"},
        color_discrete_sequence=["#4f8ef7", "#00c896", "#f59e0b"],
        barmode="stack",
    )
    fig.update_layout(title=dict(text="حجم الرسائل الشهري", font=dict(size=16, color="#f1f5f9")), height=360, **_DARK)
    _apply_axes(fig)
    st.plotly_chart(fig, use_container_width=True)


def _render_sample_table(raw_df: pd.DataFrame, n: int = 20) -> None:
    st.markdown('<p style="font-size:1rem;font-weight:700;color:#94a3b8;margin:20px 0 10px;">عينة من الرسائل المجمّعة</p>', unsafe_allow_html=True)
    cols   = [c for c in ["date", "platform", "channel_or_tag", "sector", "text"] if c in raw_df.columns]
    sample = raw_df.sort_values("date", ascending=False).head(n)[cols].rename(columns={
        "date": "التاريخ", "platform": "المنصة",
        "channel_or_tag": "القناة / الوسم", "sector": "القطاع", "text": "نص الرسالة",
    })
    if "التاريخ" in sample.columns:
        sample["التاريخ"] = pd.to_datetime(sample["التاريخ"]).dt.strftime("%Y-%m-%d")
    if "نص الرسالة" in sample.columns:
        sample["نص الرسالة"] = sample["نص الرسالة"].astype(str).str[:120] + "…"
    st.dataframe(sample, use_container_width=True, hide_index=True)


def render_social_pulse(filters: dict) -> None:
    raw_df = _load_social_raw()

    if raw_df is None or raw_df.empty:
        st.markdown("""
        <div style="background:rgba(79,142,247,0.06);border:1px solid rgba(79,142,247,0.15);
                    padding:24px 28px;border-radius:14px;direction:rtl;">
            <h4 style="color:#4f8ef7;margin:0 0 12px;">💬 لا تتوفر بيانات اجتماعية بعد</h4>
            <p style="color:#64748b;margin:0;">شغّل جامع البيانات الاجتماعية للحصول على بيانات حية.</p>
        </div>
        """, unsafe_allow_html=True)
        return

    sector_filter = filters.get("sector", "الكل")
    if sector_filter != "الكل" and "sector" in raw_df.columns:
        filtered = raw_df[raw_df["sector"] == sector_filter]
        if not filtered.empty:
            raw_df = filtered

    if "date" in raw_df.columns:
        raw_df = raw_df.copy()
        raw_df["date"] = pd.to_datetime(raw_df["date"], errors="coerce")
        if raw_df["date"].dt.tz is not None:
            raw_df["date"] = raw_df["date"].dt.tz_convert(None)
        date_from = filters.get("date_from")
        date_to   = filters.get("date_to")
        if date_from is not None:
            raw_df = raw_df[raw_df["date"] >= pd.Timestamp(date_from)]
        if date_to is not None:
            raw_df = raw_df[raw_df["date"] <= pd.Timestamp(date_to)]

    if raw_df.empty:
        st.warning("لا توجد بيانات اجتماعية في الفترة المحددة")
        return

    _render_kpi_cards(raw_df)

    agg_df = _aggregate_from_df(raw_df.to_json(orient="records"))

    col_left, col_right = st.columns([3, 2])

    with col_left:
        if agg_df is not None and not agg_df.empty:
            plot_df = agg_df if sector_filter == "الكل" else agg_df[agg_df["sector"] == sector_filter]
            if not plot_df.empty:
                fig = px.line(
                    plot_df, x="date", y="social_score", color="sector",
                    markers=True,
                    labels={"date": "الشهر", "social_score": "النقاط (0–100)", "sector": "القطاع"},
                    color_discrete_sequence=["#4f8ef7", "#00c896", "#f59e0b", "#a78bfa"],
                )
                fig.update_traces(line=dict(width=2.5), marker=dict(size=7))
                fig.update_layout(
                    title=dict(text="مؤشر النبض الاجتماعي الشهري — حسب القطاع", font=dict(size=16, color="#f1f5f9")),
                    height=360, **_DARK,
                )
                _apply_axes(fig)
                fig.update_yaxes(range=[0, 105])
                st.plotly_chart(fig, use_container_width=True)

    with col_right:
        comp_df = _load_composite_social()
        if comp_df is not None and not comp_df.empty:
            fig2 = go.Figure()
            fig2.add_trace(go.Scatter(
                x=comp_df["date"], y=comp_df["social_component"],
                mode="lines+markers", fill="tozeroy",
                line=dict(color="#4f8ef7", width=2.5),
                fillcolor="rgba(79,142,247,0.08)",
                marker=dict(size=6, color="#4f8ef7", line=dict(color="#0d1526", width=1.5)),
                name="المكوّن الاجتماعي",
            ))
            fig2.add_shape(type="line", x0=0, x1=1, xref="paper", y0=50, y1=50, yref="y",
                           line=dict(dash="dot", color="rgba(255,255,255,0.2)", width=1))
            fig2.update_layout(
                title=dict(text="مساهمة النبض في المؤشر المركب", font=dict(size=16, color="#f1f5f9")),
                height=360, **_DARK,
            )
            _apply_axes(fig2)
            fig2.update_yaxes(range=[0, 105])
            st.plotly_chart(fig2, use_container_width=True)

    st.markdown("<hr style='border-color:rgba(255,255,255,0.06);margin:24px 0;'>", unsafe_allow_html=True)
    _render_volume_chart(raw_df.copy())
    st.markdown("<hr style='border-color:rgba(255,255,255,0.06);margin:24px 0;'>", unsafe_allow_html=True)
    _render_sample_table(raw_df)
