import os
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import streamlit as st

st.set_page_config(
    page_title="نبض المنصات | Platform Pulse",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Tajawal:wght@300;400;500;700;800;900&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
<style>
*, *::before, *::after { box-sizing: border-box; }
html, body, [class*="css"] { font-family: 'Tajawal', 'Arial', sans-serif !important; direction: rtl; }
.stApp {
    background-color: #0a0f1e;
    background-image:
        radial-gradient(ellipse 80% 50% at 50% -10%, rgba(0,200,150,0.07) 0%, transparent 60%),
        radial-gradient(ellipse 60% 40% at 90% 80%, rgba(79,142,247,0.05) 0%, transparent 50%);
}
.main .block-container { padding: 1.5rem 2.5rem 3rem; max-width: 1500px; }
[data-testid="stSidebar"] {
    direction: rtl;
    background: linear-gradient(180deg, #0d1526 0%, #0a0f1e 100%);
    border-left: 1px solid rgba(0,200,150,0.15);
    border-right: none;
}
[data-testid="stSidebar"] * { color: #94a3b8; }
[data-testid="stSidebar"] .stSelectbox > label,
[data-testid="stSidebar"] .stMultiSelect > label {
    color: #64748b !important;
    font-size: 0.75rem !important;
    letter-spacing: 0.08em;
    text-transform: uppercase;
}
[data-testid="stSidebar"] [data-baseweb="select"] {
    background: rgba(255,255,255,0.04) !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    border-radius: 8px !important;
}
h1, h2, h3, h4, h5 { font-family: 'Tajawal', sans-serif !important; color: #f1f5f9; }
.pulse-header {
    position: relative;
    overflow: hidden;
    background: linear-gradient(135deg, #0d1f3c 0%, #0f2a1e 50%, #0d1526 100%);
    border: 1px solid rgba(0,200,150,0.2);
    border-radius: 20px;
    padding: 36px 48px;
    margin-bottom: 28px;
}
.pulse-header::before {
    content: '';
    position: absolute;
    top: -60px; left: -60px;
    width: 300px; height: 300px;
    background: radial-gradient(circle, rgba(0,200,150,0.12) 0%, transparent 70%);
    border-radius: 50%;
    pointer-events: none;
}
.pulse-header::after {
    content: '';
    position: absolute;
    bottom: -80px; right: -40px;
    width: 280px; height: 280px;
    background: radial-gradient(circle, rgba(79,142,247,0.08) 0%, transparent 70%);
    border-radius: 50%;
    pointer-events: none;
}
.pulse-header .eyebrow {
    font-size: 0.7rem;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: #00c896;
    font-weight: 700;
    margin-bottom: 10px;
}
.pulse-header h1 { font-size: 2.4rem !important; font-weight: 900 !important; color: #f1f5f9; margin: 0 0 10px 0 !important; line-height: 1.2; }
.pulse-header h1 span { color: #00c896; }
.pulse-header .subtitle { color: #94a3b8; font-size: 0.95rem; margin: 0; }
.pulse-header .badge-row { display: flex; gap: 10px; margin-top: 18px; flex-wrap: wrap; }
.source-badge {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 0.72rem;
    font-weight: 600;
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.1);
    color: rgba(255,255,255,0.7);
}
.stTabs [data-baseweb="tab-list"] {
    gap: 4px;
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 14px;
    padding: 6px;
    margin-bottom: 24px;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 10px;
    padding: 10px 22px;
    font-weight: 600;
    font-size: 0.85rem;
    color: #64748b;
    transition: all 0.2s ease;
    background: transparent;
}
.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, #00c896, #00a07a);
    color: #0a0f1e !important;
    box-shadow: 0 4px 16px rgba(0,200,150,0.3);
}
div[data-testid="stMetric"] {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 14px;
    padding: 18px 20px;
    direction: rtl;
}
div[data-testid="stMetricValue"] { color: #f1f5f9; font-family: 'JetBrains Mono', monospace !important; font-weight: 700 !important; }
div[data-testid="stMetricLabel"] { color: #64748b; font-size: 0.78rem !important; }
div[data-testid="stAlert"] {
    background: rgba(0,200,150,0.06) !important;
    border: 1px solid rgba(0,200,150,0.2) !important;
    border-radius: 12px !important;
    color: #94a3b8 !important;
}
.stSpinner > div { border-top-color: #00c896 !important; }
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: rgba(255,255,255,0.03); }
::-webkit-scrollbar-thumb { background: rgba(0,200,150,0.3); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: rgba(0,200,150,0.5); }
input, textarea, select, .stSelectbox, .stMultiSelect { direction: rtl !important; text-align: right !important; }
th, td { text-align: right !important; }
.data-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 5px 14px;
    border-radius: 20px;
    font-size: 0.78rem;
    font-weight: 700;
    letter-spacing: 0.03em;
}
.badge-live { background: rgba(0,200,150,0.15); color: #00c896; border: 1px solid rgba(0,200,150,0.3); }
.badge-sample { background: rgba(251,188,4,0.12); color: #fbbc04; border: 1px solid rgba(251,188,4,0.25); }
hr { border: none; border-top: 1px solid rgba(255,255,255,0.06) !important; margin: 20px 0 !important; }
.pulse-footer { text-align: center; padding: 32px 20px; margin-top: 40px; border-top: 1px solid rgba(255,255,255,0.06); color: #334155; font-size: 0.82rem; }
.pulse-footer strong { color: #00c896; }
</style>
""", unsafe_allow_html=True)

from components.monthly_index import render_monthly_index
from components.sector_breakdown import render_sector_breakdown
from components.heatmap import render_heatmap
from components.forecast import render_forecast
from components.gap_analysis import render_gap_analysis
from components.social_pulse import render_social_pulse
from cloud_collector import run_live_collection_cached, _data_is_stale


def _get_data_status() -> dict:
    composite_path = os.path.join("data", "processed", "composite_index.csv")
    if not os.path.exists(composite_path):
        return {"status": "sample", "label": "⬤ بيانات عينة", "css": "badge-sample"}
    if _data_is_stale(composite_path, max_age_hours=6):
        return {"status": "stale", "label": "⬤ بيانات قديمة", "css": "badge-sample"}
    import time
    age_min = int((time.time() - os.path.getmtime(composite_path)) / 60)
    return {"status": "live", "label": f"⬤ بيانات حية ({age_min}د)", "css": "badge-live"}


def render_sidebar() -> dict:
    data_status = st.session_state.get("data_status", _get_data_status())

    with st.sidebar:
        st.markdown(f"""
        <div style="padding: 28px 20px 20px; border-bottom: 1px solid rgba(255,255,255,0.06);">
            <div style="display:flex; align-items:center; gap:12px; margin-bottom:8px;">
                <div style="width:36px; height:36px; border-radius:10px;
                            background: linear-gradient(135deg, #00c896, #00a07a);
                            display:flex; align-items:center; justify-content:center;
                            font-size:18px; flex-shrink:0;">⚡</div>
                <div>
                    <div style="font-size:1.1rem; font-weight:800; color:#f1f5f9; line-height:1;">نبض المنصات</div>
                    <div style="font-size:0.7rem; color:#334155; letter-spacing:0.1em;">PLATFORM PULSE</div>
                </div>
            </div>
            <div style="margin-top:14px;">
                <span class="data-badge {data_status['css']}">{data_status['label']}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div style="padding: 16px 4px 8px; font-size:0.7rem; letter-spacing:0.12em;
                    text-transform:uppercase; color:#475569;">الفلاتر</div>
        """, unsafe_allow_html=True)

        sector = st.selectbox("القطاع", ["الكل", "نقل", "توصيل", "عمل حر"], index=0)
        city = st.selectbox("المدينة", [
            "الكل", "الرياض", "جدة", "الدمام", "مكة المكرمة",
            "المدينة المنورة", "الخبر", "أبها", "تبوك",
            "الطائف", "بريدة", "حائل", "نجران", "جازان"
        ], index=0)
        time_period = st.selectbox("الفترة الزمنية",
            ["آخر 12 شهراً", "آخر 6 أشهر", "آخر 3 أشهر", "2025", "2024"], index=0)

        now = datetime.now()
        period_map = {
            "آخر 12 شهراً": (now - timedelta(days=365), now),
            "آخر 6 أشهر":  (now - timedelta(days=180), now),
            "آخر 3 أشهر":  (now - timedelta(days=90),  now),
            "2025": (datetime(2025, 1, 1), datetime(2025, 12, 31)),
            "2024": (datetime(2024, 1, 1), datetime(2024, 12, 31)),
        }
        date_from, date_to = period_map[time_period]
        date_from = date_from.replace(tzinfo=None)
        date_to   = date_to.replace(tzinfo=None)

        st.markdown("""
        <div style="margin-top:20px; padding-top:16px; border-top:1px solid rgba(255,255,255,0.06);">
            <div style="font-size:0.7rem; letter-spacing:0.12em; text-transform:uppercase;
                        color:#475569; margin-bottom:8px;">تحديث البيانات</div>
        </div>
        """, unsafe_allow_html=True)

        if st.button("🔄 تحديث البيانات الحية", use_container_width=True):
            run_live_collection_cached.clear()
            st.session_state["force_refresh"] = True
            st.rerun()

        st.markdown("""
        <div style="margin-top:20px; padding-top:16px; border-top:1px solid rgba(255,255,255,0.06);">
            <div style="font-size:0.7rem; letter-spacing:0.12em; text-transform:uppercase;
                        color:#475569; margin-bottom:10px;">مصادر البيانات</div>
        </div>
        """, unsafe_allow_html=True)

        for icon, label in [("📱","تقييمات التطبيقات"),("🔍","Google Trends"),
                             ("🗺️","OpenStreetMap"),("💬","Telegram / X"),("🏛️","GASTAT / GOSI")]:
            st.markdown(f"""
            <div style="display:flex; align-items:center; gap:8px; padding:5px 0;
                        color:#64748b; font-size:0.82rem;">
                <span>{icon}</span><span>{label}</span>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("""
        <div style="margin-top:auto; padding: 24px 4px 8px; text-align:center;
                    color:#475569; font-size:0.75rem; line-height:1.6;">
            هاكاثون الابتكار في البيانات<br>المسار الأول
        </div>
        """, unsafe_allow_html=True)

    return {"sector": sector, "city": city, "date_from": date_from, "date_to": date_to}


def main():
        collection_result = run_live_collection_cached()

    st.session_state["data_status"] = _get_data_status()
    is_sample = collection_result.get("source") == "sample"

    filters = render_sidebar()

    st.markdown("""
    <div class="pulse-header">
        <div class="eyebrow">🇸🇦 هاكاثون الابتكار في البيانات — المسار الأول</div>
        <h1>⚡ نبض <span>المنصات</span></h1>
        <p class="subtitle">مرصد ذكي آلي يستدل على حجم القوى العاملة في اقتصاد المنصات عبر الآثار الرقمية العامة</p>
        <div class="badge-row">
            <span class="source-badge">📱 App Reviews</span>
            <span class="source-badge">🔍 Google Trends</span>
            <span class="source-badge">🗺️ OpenStreetMap</span>
            <span class="source-badge">💬 Telegram · X</span>
            <span class="source-badge">🏛️ GASTAT · GOSI</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if is_sample:
        st.info("📦 يعمل المرصد ببيانات العينة — اضغط «تحديث البيانات الحية» في الشريط الجانبي أو انتظر التحديث التلقائي.")
    elif collection_result.get("status") == "collected":
        st.success(f"✅ تم جمع بيانات حية — Trends: {'✓' if collection_result.get('trends') else '✗'}  Reviews: {'✓' if collection_result.get('reviews') else '✗'}")

    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "⚡ المؤشر الشهري",
        "📊 التفصيل القطاعي",
        "🗺️ الخريطة الحرارية",
        "🔮 التنبؤات",
        "📉 فجوة الرصد",
        "💬 النبض الاجتماعي",
    ])

    with tab1:
        render_monthly_index(filters)
    with tab2:
        render_sector_breakdown(filters)
    with tab3:
        render_heatmap(filters)
    with tab4:
        render_forecast(filters)
    with tab5:
        render_gap_analysis(filters)
    with tab6:
        render_social_pulse(filters)

    st.markdown("""
    <div class="pulse-footer">
        <strong>نبض المنصات</strong> · Platform Pulse · هاكاثون الابتكار في البيانات
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
