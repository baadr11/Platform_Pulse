import os
import time
import logging

import pandas as pd
import streamlit as st

logger = logging.getLogger(__name__)


def _data_is_stale(path: str, max_age_hours: int = 6) -> bool:
    if not os.path.exists(path):
        return True
    return (time.time() - os.path.getmtime(path)) > max_age_hours * 3600


def _load_raw_or_sample(raw_path: str, sample_path: str) -> pd.DataFrame:
    for path in [raw_path, sample_path]:
        if os.path.exists(path):
            try:
                df = pd.read_csv(path, encoding="utf-8-sig")
                if not df.empty:
                    return df
            except Exception as e:
                logger.warning("Failed to read %s: %s", path, e)
    return pd.DataFrame()


@st.cache_data(ttl=21600, show_spinner=False)
def run_live_collection_cached():
    os.makedirs("data/raw", exist_ok=True)
    os.makedirs("data/processed", exist_ok=True)
    os.makedirs("data/sample", exist_ok=True)

    composite_path = os.path.join("data", "processed", "composite_index.csv")

    if not _data_is_stale(composite_path, max_age_hours=6):
        return {"status": "fresh", "source": "live"}

    sources = {
        "reviews": ("data/raw/reviews_raw.csv",  "data/sample/sample_reviews.csv"),
        "trends":  ("data/raw/trends_raw.csv",   "data/sample/sample_trends.csv"),
        "social":  ("data/raw/social_raw.csv",   "data/sample/sample_social.csv"),
        "spatial": ("data/raw/spatial_raw.csv",  "data/sample/sample_spatial.csv"),
    }

    for name, (raw_path, sample_path) in sources.items():
        df = _load_raw_or_sample(raw_path, sample_path)
        if not df.empty:
            df.to_csv(raw_path, index=False, encoding="utf-8-sig")

    try:
        from src.models.composite_index import compute_composite_index, compute_gap_analysis
        compute_composite_index()
        compute_gap_analysis()
        if os.path.exists(composite_path):
            return {"status": "collected", "source": "sample+raw"}
    except Exception as e:
        logger.error("compute_composite_index failed: %s", e)

    return {"status": "sample", "source": "sample"}
