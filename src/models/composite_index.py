import logging
import os
import sys
from datetime import datetime

import pandas as pd
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

logger = logging.getLogger(__name__)

# ══════════════════════════════════════════════════════════════════
#  N_total — إجمالي القوى العاملة (مشتق من مصدرين رسميين)
#
#  ⚠️  ملاحظة منهجية:
#  لا تنشر GASTAT رقماً مطلقاً لإجمالي قوة العمل في بياناتها المتاحة
#  (البيانات المتاحة تحتوي على معدلات ونسب فقط)، لذا يُشتق هذا الرقم
#  رياضياً من مصدرين رسميين وفق المعادلة:
#
#       قوة العمل = السكان (15+) × معدل المشاركة
#
#  ┌─────────────────────────────────────────────────────────────┐
#  │  المصدر 1: التقديرات السكانية لعام 2024م — GASTAT          │
#  │  الرابط:                                                    │
#  │  stats.gov.sa/documents/20117/2067012/                      │
#  │  Population+Estimates+Publication+2024.pdf                  │
#  │                                                             │
#  │  - إجمالي سكان المملكة 2024:      35,300,000               │
#  │  - الفئة 15–64 سنة (74.7%):      26,369,100               │
#  │  - الفئة 65+ سنة  ( 2.8%):          988,400               │
#  │  - السكان في سن العمل (15+):     27,357,500               │
#  └─────────────────────────────────────────────────────────────┘
#  ┌─────────────────────────────────────────────────────────────┐
#  │  المصدر 2: نشرة إحصاءات سوق العمل Q4-2024 — GASTAT        │
#  │  الرابط:                                                    │
#  │  stats.gov.sa/documents/d/guest/                            │
#  │  lms-q4_2024_pr_ar-press-release-pdf                        │
#  │                                                             │
#  │  - معدل المشاركة الإجمالي (جدول 1):  66.4%                │
#  └─────────────────────────────────────────────────────────────┘
#
#  الحساب:
#    قوة العمل = 27,357,500 × 66.4% = 18,165,380 ≈ 18,165,000
#
#  📌 هذا الرقم مشتق وموثق المصدر، وليس منشوراً مباشرةً في جدول واحد.

_TOTAL_POP_2024  = 35_300_000        # إجمالي سكان المملكة 2024
_PCT_15_64       = 0.747             # الفئة 15-64 سنة = 74.7% من الإجمالي
_PCT_65_PLUS     = 0.028             # الفئة 65+ سنة   =  2.8% من الإجمالي
_POP_15_64       = round(_TOTAL_POP_2024 * _PCT_15_64)    # = 26,369,100
_POP_65_PLUS     = round(_TOTAL_POP_2024 * _PCT_65_PLUS)  # =    988,400
_POP_15_PLUS     = _POP_15_64 + _POP_65_PLUS              # = 27,357,500

# ── المصدر 2: نشرة سوق العمل Q4-2024 — GASTAT ────────────────────
_LFPR_Q4_2024    = 0.664             # معدل المشاركة الإجمالي (جدول 1) = 66.4%

# ── الاشتقاق: قوة العمل = السكان (15+) × معدل المشاركة ───────────
_N_TOTAL_DERIVED = round(_POP_15_PLUS * _LFPR_Q4_2024)    # = 18,165,380

GASTAT_ANCHORS = {
    # الرقم الرئيسي المستخدم في النموذج
    "total_workforce"      : _N_TOTAL_DERIVED,  # ≈ 18,165,380

    # نطاق ILO لاقتصاد المنصات في الشرق الأوسط
    "gig_share_low"        : 0.004,   # 0.4%  — الحد الأدنى
    "gig_share_high"       : 0.018,   # 1.8%  — الحد الأقصى

    # --- توثيق المصدر (للمراجعة والشفافية) ---
    "_pop_total_2024"      : _TOTAL_POP_2024,
    "_pop_15_plus"         : _POP_15_PLUS,
    "_lfpr_q4_2024"        : _LFPR_Q4_2024,
    "_derivation"          : "N = POP_15_PLUS × LFPR = 27,357,500 × 0.664 ≈ 18,165,380",
    "_source_pop"          : "GASTAT — نشرة التقديرات السكانية 2024م",
    "_source_lfpr"         : "GASTAT — نشرة سوق العمل Q4-2024، جدول (1)، معدل المشاركة الإجمالي = 66.4%",
    "_note"                : "رقم مشتق — غير منشور مباشرةً في جدول واحد من GASTAT",
}

logger.info(
    "GASTAT_ANCHORS initialised: "
    "POP_15+=%d, LFPR=%.1f%%, N_total=%d",
    _POP_15_PLUS, _LFPR_Q4_2024 * 100, _N_TOTAL_DERIVED,
)


def min_max_scale(series: pd.Series) -> pd.Series:
    min_val = series.min()
    max_val = series.max()
    if max_val == min_val:
        logger.warning(
            "min_max_scale received a constant series (all values = %s); "
            "returning 50.0 for all observations — check input data quality",
            min_val,
        )
        return pd.Series([50.0] * len(series), index=series.index)
    return ((series - min_val) / (max_val - min_val)) * 100


def load_all_components() -> dict:
    components = {}

    reviews_paths = [
        os.path.join("data", "processed", "reviews_normalized.csv"),
        os.path.join("data", "processed", "reviews_cleaned.csv"),
        os.path.join("data", "sample", "sample_reviews.csv"),
    ]
    for path in reviews_paths:
        if os.path.exists(path):
            try:
                df = pd.read_csv(path, encoding="utf-8-sig")
                df["date"] = pd.to_datetime(df["date"], errors="coerce")
                df = df.dropna(subset=["date"])
                monthly = df.groupby(pd.Grouper(key="date", freq="ME")).size().reset_index(name="review_count")
                monthly["reviews_score"] = min_max_scale(monthly["review_count"])
                components["reviews"] = monthly
                logger.info("Reviews component: %d months", len(monthly))
            except Exception as e:
                logger.warning("Failed to load reviews: %s", e)
            break

    trends_paths = [
        os.path.join("data", "processed", "trends_normalized.csv"),
        os.path.join("data", "processed", "trends_cleaned.csv"),
        os.path.join("data", "sample", "sample_trends.csv"),
    ]
    for path in trends_paths:
        if os.path.exists(path):
            try:
                df = pd.read_csv(path, encoding="utf-8-sig")
                df["date"] = pd.to_datetime(df["date"], errors="coerce")
                df = df.dropna(subset=["date"])
                monthly = df.groupby(pd.Grouper(key="date", freq="ME"))["interest_value"].mean().reset_index()
                monthly["trends_score"] = min_max_scale(monthly["interest_value"])
                components["trends"] = monthly
                logger.info("Trends component: %d months", len(monthly))
            except Exception as e:
                logger.warning("Failed to load trends: %s", e)
            break

    sentiment_path = os.path.join("data", "processed", "sentiment_results.csv")
    if os.path.exists(sentiment_path):
        try:
            df = pd.read_csv(sentiment_path, encoding="utf-8-sig")
            df["date"] = pd.to_datetime(df["date"], errors="coerce")
            df = df.dropna(subset=["date"])
            sentiment_map = {"إيجابي": 1, "محايد": 0.5, "سلبي": 0}
            df["sentiment_num"] = df["sentiment"].map(sentiment_map)
            monthly = df.groupby(pd.Grouper(key="date", freq="ME"))["sentiment_num"].mean().reset_index()
            monthly["sentiment_score"] = min_max_scale(monthly["sentiment_num"])
            components["sentiment"] = monthly
            logger.info("Sentiment component: %d months", len(monthly))
        except Exception as e:
            logger.warning("Failed to load sentiment: %s", e)

    social_path = os.path.join("data", "raw", "social_raw.csv")
    if os.path.exists(social_path):
        try:
            from src.collectors.social_collector import aggregate_social_sentiment
            soc_agg = aggregate_social_sentiment()
            if not soc_agg.empty:
                national_social = (
                    soc_agg.groupby("date")["social_score"]
                    .mean().reset_index()
                )
                components["social"] = national_social
                components["social_by_sector"] = soc_agg
                logger.info("Social component: %d months", len(national_social))
        except Exception as e:
            logger.warning("Failed to load social component: %s", e)

    spatial_paths = [
        os.path.join("data", "processed", "spatial_clustered.csv"),
        os.path.join("data", "sample", "sample_spatial.csv"),
    ]
    for path in spatial_paths:
        if os.path.exists(path):
            try:
                df = pd.read_csv(path, encoding="utf-8-sig")
                avg_score = df["activity_score"].mean() if "activity_score" in df.columns else 50
                components["spatial_avg"] = avg_score
                if "city_ar" in df.columns and "activity_score" in df.columns:
                    components["spatial_df"] = df
                logger.info("Spatial component: average %.1f", avg_score)
            except Exception as e:
                logger.warning("Failed to load spatial: %s", e)
            break

    forecast_signal = load_forecast_signal()
    if forecast_signal is not None:
        components["forecast_signal"] = forecast_signal
        logger.info("Forecast signal component loaded from Prophet output")

    return components


def load_forecast_signal(base_path: str = "data/processed") -> "pd.DataFrame | None":
    forecast_path = os.path.join(base_path, "forecast_results.csv")
    if not os.path.exists(forecast_path):
        return None

    try:
        fc = pd.read_csv(forecast_path, parse_dates=["ds"])
        future_cutoff = fc["ds"].max() - pd.Timedelta(days=90)
        historical = fc[fc["ds"] <= future_cutoff]
        future = fc[fc["ds"] > future_cutoff]

        if len(future) < 2:
            return None

        slope = (future["yhat"].iloc[-1] - future["yhat"].iloc[0]) / max(len(future), 1)
        historical_std = float(historical["yhat"].std()) if len(historical) > 1 else 1.0
        slope_normalized = slope / (historical_std or 1.0)
        score = float(min(max(50 + slope_normalized * 25, 0), 100))

        monthly_future = future.set_index("ds")["yhat"].resample("ME").mean().dropna()
        if monthly_future.empty:
            return None
        scaled = (monthly_future - monthly_future.min()) / (monthly_future.max() - monthly_future.min() + 1e-9) * 100
        return pd.DataFrame({"date": scaled.index, "score": scaled.values})
    except Exception as e:
        logger.warning("Could not load forecast signal: %s", e)
        return None


def compute_weights_elasticnet(components: dict) -> dict:
    from sklearn.linear_model import ElasticNetCV

    GIG_SHARE_QUARTERLY_ESTIMATES = np.array([
        0.011, 0.012, 0.013, 0.013,
        0.012, 0.014, 0.014, 0.015,
    ])

    indicator_names = []
    score_series = []

    for name in ["reviews", "trends", "sentiment", "social"]:
        if name not in components:
            continue
        df = components[name]
        score_col = "social_score" if name == "social" else f"{name}_score"
        if score_col in df.columns and len(df) >= 2:
            indicator_names.append(name)
            score_series.append(df[score_col].values)

    if "spatial_df" in components and "activity_score" in components["spatial_df"].columns:
        spatial_vals = components["spatial_df"]["activity_score"].values
        indicator_names.append("spatial")
        score_series.append(spatial_vals)
    elif "spatial_avg" in components:
        indicator_names.append("spatial")
        score_series.append(np.array([float(components["spatial_avg"])]))

    if len(indicator_names) < 2:
        logger.warning("ElasticNet: insufficient components — falling back to equal weights")
        return {
            "reviews": 0.25, "trends": 0.25,
            "sentiment": 0.25, "social": 0.10, "spatial": 0.15,
        }

    try:
        min_len = min(len(s) for s in score_series)
        min_len = max(min_len, 2)

        if min_len < 12:
            logger.warning(
                "Insufficient observations for ElasticNetCV (min_len=%d < 6) — "
                "using IVW fallback directly", min_len,
            )
            return _compute_weights_ivw_fallback(components, indicator_names, score_series)

        X = np.column_stack([s[:min_len] for s in score_series])
        y = (
            pd.Series(GIG_SHARE_QUARTERLY_ESTIMATES)
            .reindex(range(min_len))
            .interpolate(method="linear")
            .values
        )

        model = ElasticNetCV(
            cv=min(5, min_len),
            l1_ratio=[0.1, 0.5, 0.9],
            max_iter=5000,
            random_state=42,
        )
        model.fit(X, y)

        raw = np.abs(model.coef_)
        total = raw.sum() or 1.0
        weights = {n: round(float(raw[i] / total), 4) for i, n in enumerate(indicator_names)}
        for n in ["reviews", "trends", "sentiment", "social", "spatial"]:
            weights.setdefault(n, 0.0)

        logger.info(
            "ElasticNetCV weights: %s",
            ", ".join(f"{k}={v:.3f}" for k, v in weights.items()),
        )
        return weights

    except Exception as e:
        logger.warning("ElasticNetCV failed (%s) — falling back to IVW", e)
        return _compute_weights_ivw_fallback(components, indicator_names, score_series)


def _compute_weights_ivw_fallback(components: dict, indicator_names: list, score_series: list) -> dict:
    inv_var: dict = {}
    for name, series in zip(indicator_names, score_series):
        variance = max(float(np.var(series)), 1.0)
        inv_var[name] = 1.0 / variance

    if not inv_var:
        return {"reviews": 0.25, "trends": 0.25, "sentiment": 0.25, "social": 0.10, "spatial": 0.15}

    total = sum(inv_var.values())
    weights = {k: round(v / total, 4) for k, v in inv_var.items()}
    logger.info(
        "IVW fallback weights: %s",
        ", ".join(f"{k}={v:.3f}" for k, v in weights.items()),
    )
    return weights


def compute_weights(components: dict) -> dict:
    return compute_weights_elasticnet(components)


def bootstrap_confidence(monthly_values: np.ndarray, n_samples: int = 1000,
                         confidence: float = 0.95) -> tuple:
    if len(monthly_values) < 2:
        mean_val = float(np.mean(monthly_values)) if len(monthly_values) > 0 else 50.0
        return round(mean_val - 5.0, 2), round(mean_val + 5.0, 2)

    bootstrap_means = []
    for _ in range(n_samples):
        sample = np.random.choice(monthly_values, size=len(monthly_values), replace=True)
        bootstrap_means.append(np.mean(sample))

    alpha = (1 - confidence) / 2
    lower = np.percentile(bootstrap_means, alpha * 100)
    upper = np.percentile(bootstrap_means, (1 - alpha) * 100)
    return round(lower, 2), round(upper, 2)


def estimate_workers(
    index_value: float,
    official_total: float = GASTAT_ANCHORS["total_workforce"],
) -> int:
    """
    يُقدّر عدد العاملين في اقتصاد المنصات بناءً على:
      - N_total: إجمالي القوى العاملة (مشتق من GASTAT، انظر التوثيق أعلاه)
      - نطاق ILO للشرق الأوسط: 0.4% – 1.8%
      - قيمة المؤشر المركّب (0–100) للاستيفاء داخل النطاق
    """
    lower_gig_pct = GASTAT_ANCHORS["gig_share_low"]   # 0.4%
    upper_gig_pct = GASTAT_ANCHORS["gig_share_high"]  # 1.8%

    adjusted  = lower_gig_pct + (upper_gig_pct - lower_gig_pct) * (index_value / 100)
    estimated = int(official_total * adjusted)
    return estimated


def compute_composite_index() -> pd.DataFrame:
    logger.info("=" * 60)
    logger.info("Computing Platform Pulse Composite Index")
    logger.info(
        "N_total = %d (POP_15+ %d × LFPR %.1f%%) — GASTAT 2024",
        GASTAT_ANCHORS["total_workforce"],
        _POP_15_PLUS,
        _LFPR_Q4_2024 * 100,
    )
    logger.info("=" * 60)

    components = load_all_components()

    if not components:
        logger.error("No sub-indicators available for composite index")
        return pd.DataFrame()

    weights = compute_weights(components)

    dates = set()
    for key, val in components.items():
        if isinstance(val, pd.DataFrame) and "date" in val.columns:
            dates.update(val["date"].dropna().tolist())

    if not dates:
        dates = [pd.Timestamp.now()]

    dates = sorted(pd.to_datetime(list(dates), errors='coerce').dropna())

    all_index_values = []

    city_spatial = {}
    if "spatial_df" in components:
        sdf = components["spatial_df"]
        for _, row in sdf.iterrows():
            city_ar = row.get("city_ar", "")
            score = row.get("activity_score", 50)
            if city_ar:
                city_spatial[city_ar] = score

    results = []
    for date in dates:
        r_score, t_score, s_score, soc_score, sp_score = 50, 50, 50, 50, 50

        if "reviews" in components:
            df = components["reviews"]
            mask = df["date"] == date
            if mask.any():
                r_score = df.loc[mask, "reviews_score"].values[0]

        if "trends" in components:
            df = components["trends"]
            mask = df["date"] == date
            if mask.any():
                t_score = df.loc[mask, "trends_score"].values[0]

        if "sentiment" in components:
            df = components["sentiment"]
            mask = df["date"] == date
            if mask.any():
                s_score = df.loc[mask, "sentiment_score"].values[0]

        if "social" in components:
            sdf = components["social"]
            mask = sdf["date"].dt.to_period("M") == pd.Timestamp(date).to_period("M")
            if mask.any():
                soc_score = sdf.loc[mask, "social_score"].values[0]

        if "spatial_avg" in components:
            sp_score = components["spatial_avg"]

        fc_score = 50.0
        if "forecast_signal" in components:
            fdf = components["forecast_signal"]
            if "date" in fdf.columns:
                mask = fdf["date"].dt.to_period("M") == pd.Timestamp(date).to_period("M")
                if mask.any():
                    fc_score = float(fdf.loc[mask, "score"].values[0])
            elif len(fdf) > 0:
                fc_score = float(fdf["score"].iloc[0])

        score_map = {
            "reviews": r_score, "trends": t_score,
            "sentiment": s_score, "social": soc_score,
            "spatial": sp_score, "forecast_signal": fc_score,
        }
        active = {k: v for k, v in weights.items() if k in score_map}
        w_sum = sum(active.values())
        index_value = float(
            sum(score_map[k] * v for k, v in active.items()) / w_sum
        ) if w_sum > 0 else 50.0
        all_index_values.append(index_value)

        estimated = estimate_workers(index_value)

        results.append({
            "date": date, "city": "الكل", "sector": "الكل",
            "index_value": round(index_value, 2),
            "reviews_component": round(r_score, 2),
            "trends_component": round(t_score, 2),
            "sentiment_component": round(s_score, 2),
            "social_component": round(soc_score, 2),
            "spatial_component": round(sp_score, 2),
            "confidence_lower": 0, "confidence_upper": 0,
            "estimated_workers": estimated,
            "data_scope": "national",
        })

        for city_ar, city_sp_score in city_spatial.items():
            city_score_map = {**score_map, "spatial": city_sp_score}
            city_index = float(
                sum(city_score_map[k] * v for k, v in active.items()) / w_sum
            ) if w_sum > 0 else 50.0
            city_estimated = estimate_workers(city_index)
            results.append({
                "date": date, "city": city_ar, "sector": "الكل",
                "index_value": round(city_index, 2),
                "reviews_component": round(r_score, 2),
                "trends_component": round(t_score, 2),
                "sentiment_component": round(s_score, 2),
                "social_component": round(soc_score, 2),
                "spatial_component": round(city_sp_score, 2),
                "confidence_lower": 0, "confidence_upper": 0,
                "estimated_workers": city_estimated,
                "data_scope": "spatial_only",
            })

    national_cis = {}
    if all_index_values:
        window_size = min(6, len(all_index_values))
        for i, idx_val in enumerate(all_index_values):
            window_start = max(0, i - window_size + 1)
            window_vals = np.array(all_index_values[window_start:i + 1])
            lower, upper = bootstrap_confidence(window_vals)
            national_cis[i] = (lower, upper)

    date_idx_map = {d: i for i, d in enumerate(dates)}
    for r in results:
        if r.get("data_scope") == "national":
            d_idx = date_idx_map.get(r["date"])
            if d_idx is not None and d_idx in national_cis:
                r["confidence_lower"] = national_cis[d_idx][0]
                r["confidence_upper"] = national_cis[d_idx][1]

    national_ci_by_date = {}
    for r in results:
        if r.get("data_scope") == "national" and r["confidence_lower"] != 0:
            national_ci_by_date[str(r["date"])] = (r["confidence_lower"], r["confidence_upper"])
    for r in results:
        if r.get("data_scope") == "spatial_only":
            key = str(r["date"])
            if key in national_ci_by_date:
                r["confidence_lower"] = national_ci_by_date[key][0]
                r["confidence_upper"] = national_ci_by_date[key][1]

    results_df = pd.DataFrame(results)

    output_path = os.path.join("data", "processed", "composite_index.csv")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    results_df.to_csv(output_path, index=False, encoding="utf-8-sig")

    try:
        from src.database.db_manager import DatabaseManager
        db = DatabaseManager()
        db.insert_composite_index(results)
        logger.info("Saved composite index to database")
    except Exception as e:
        logger.warning("Could not save to database: %s", e)

    if not results_df.empty:
        national = results_df[results_df["city"] == "الكل"]
        latest = national.iloc[-1] if not national.empty else results_df.iloc[-1]
        logger.info("Latest composite index (national):")
        logger.info("  Date:              %s", latest["date"])
        logger.info("  Value:             %.2f", latest["index_value"])
        logger.info("  CI:                [%.2f - %.2f]", latest["confidence_lower"], latest["confidence_upper"])
        logger.info("  Estimated workers: %d", latest["estimated_workers"])
        logger.info("  N_total used:      %d (derived)", GASTAT_ANCHORS["total_workforce"])

    logger.info("Saved composite index: %s", output_path)
    return results_df


GASTAT_2023_Q4_TRANSPORT_DELIVERY_FORMAL = 175_000


def compute_gap_analysis() -> pd.DataFrame:
    logger.info("Computing gap analysis")

    official_paths = [
        os.path.join("data", "raw", "official_raw.csv"),
        os.path.join("data", "sample", "sample_official.csv"),
    ]

    official_df = None
    for path in official_paths:
        if os.path.exists(path):
            try:
                official_df = pd.read_csv(path, encoding="utf-8-sig")
                break
            except Exception:
                try:
                    official_df = pd.read_csv(path, encoding="utf-8")
                    break
                except Exception:
                    continue

    composite_path = os.path.join("data", "processed", "composite_index.csv")
    if not os.path.exists(composite_path):
        logger.warning("Composite index not available")
        return pd.DataFrame()

    composite_df = pd.read_csv(composite_path, encoding="utf-8-sig")

    gaps = []
    if official_df is not None and not official_df.empty:
        transport_mask = official_df["metric_name"].str.contains("النقل", na=False)
        food_mask = official_df["metric_name"].str.contains("الإقامة|الطعام", na=False)

        for _, row in composite_df.iterrows():
            estimated = row.get("estimated_workers", 0)
            official_transport = official_df.loc[transport_mask, "value"].iloc[-1] if transport_mask.any() else 1_000_000
            official_food = official_df.loc[food_mask, "value"].iloc[-1] if food_mask.any() else 750_000
            official_total = official_transport + official_food
            gap = estimated - int(official_total * 0.1)
            gap_pct = (gap / (official_total * 0.1) * 100) if official_total > 0 else 0
            gaps.append({
                "date": row["date"],
                "estimated_workers": estimated,
                "official_formal_workers": int(official_total * 0.1),
                "gap": int(gap),
                "gap_percentage": round(gap_pct, 1),
                "interpretation": "فائض رقمي" if gap > 0 else "عجز رقمي",
            })

    if not gaps:
        for _, row in composite_df.iterrows():
            est = row.get("estimated_workers", 0)
            official_est = GASTAT_2023_Q4_TRANSPORT_DELIVERY_FORMAL
            gaps.append({
                "date": row["date"],
                "estimated_workers": est,
                "official_formal_workers": official_est,
                "gap": est - official_est,
                "gap_percentage": round(
                    (est - official_est) / official_est * 100, 1
                ) if official_est > 0 else 0,
                "interpretation": "فائض رقمي" if est > official_est else "عجز رقمي",
            })

    gaps_df = pd.DataFrame(gaps)
    gaps_path = os.path.join("data", "processed", "gap_analysis.csv")
    os.makedirs(os.path.dirname(gaps_path), exist_ok=True)
    gaps_df.to_csv(gaps_path, index=False, encoding="utf-8-sig")
    logger.info("Saved gap analysis: %s", gaps_path)

    return gaps_df


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%H:%M:%S"
    )
    compute_composite_index()
    compute_gap_analysis()
    logger.info("All models completed")
