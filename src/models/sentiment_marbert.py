import logging
import os
import sys
from typing import List, Dict, Any
import streamlit as st
import pandas as pd
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

logger = logging.getLogger(__name__)

POSITIVE_WORDS = [
    "ممتاز", "رائع", "جميل", "أفضل", "سريع", "محترم", "سهل", "جيد",
    "ممتازة", "رائعة", "جيدة", "حلو", "حلوه", "زين", "زينة", "عظيم",
    "مناسب", "مناسبة", "نظيف", "مريح",
    "great", "excellent", "amazing", "fast", "best", "good", "love",
    "wonderful", "fantastic", "perfect", "awesome", "outstanding",
]

NEGATIVE_WORDS = [
    "سيء", "سيئ", "بطيء", "مرتفع", "غالي", "غالية", "تعلق", "يعلق",
    "فشل", "مشكلة", "مشاكل", "سرقة", "نصب", "كذب",
    "bad", "slow", "expensive", "crash", "crashes", "worst",
    "terrible", "horrible", "late", "cold", "lost", "poor",
    "يلغي", "ملغي", "تأخر", "أبطأ", "حادث", "رفض",
]

_model = None
_tokenizer = None
_model_status: str = "unloaded"


def get_model_status() -> str:
    return _model_status

@st.cache_resource
def load_marbert():
    global _model, _tokenizer

    if _model is not None:
        return _model, _tokenizer

    try:
        from transformers import AutoTokenizer, AutoModelForSequenceClassification
        import torch
        import yaml

        config_model = None
        try:
            config_path = os.path.join("config", "settings.yaml")
            with open(config_path, "r", encoding="utf-8") as f:
                cfg = yaml.safe_load(f)
            config_model = cfg.get("models", {}).get("sentiment", {}).get("model_name")
        except Exception:
            pass

        model_candidates = [
            "CAMeL-Lab/bert-base-arabic-camelbert-da-sentiment",
            "aubmindlab/bert-base-arabertv02-twitter",
            "UBC-NLP/MARBERT",
        ]
        if config_model and config_model not in model_candidates:
            model_candidates.insert(0, config_model)

        for model_name in model_candidates:
            try:
                logger.info("Loading model: %s...", model_name)
                _tokenizer = AutoTokenizer.from_pretrained(model_name)
                _model = AutoModelForSequenceClassification.from_pretrained(
                    model_name,
                    low_cpu_mem_usage=False,
                )
                _model = _model.to(torch.device("cpu"))
                _model.eval()
                num_labels = _model.config.num_labels
                _model_status = "transformer"
                logger.info("Loaded %s successfully (labels=%d)", model_name, num_labels)
                return _model, _tokenizer
            except Exception as e:
                logger.warning("Could not load %s: %s", model_name, e)
                _model = None
                _tokenizer = None
                continue

        return None, None

    except Exception as e:
        logger.warning("Failed to load any sentiment model: %s", e)
        return None, None


def _normalize_label(raw_label: str) -> str:
    label = str(raw_label).strip().lower()
    if label in {"positive", "pos", "1", "إيجابي", "ايجابي"}:
        return "إيجابي"
    if label in {"negative", "neg", "0", "سلبي"}:
        return "سلبي"
    if label in {"neutral", "neu", "mixed", "محايد"}:
        return "محايد"
    return "محايد"


def analyze_with_arabic_sentiment(texts: List[str], batch_size: int = 16) -> List[Dict[str, Any]]:
    global _model, _tokenizer, _model_status

    model, tokenizer = load_marbert()

    if model is None or tokenizer is None:
        _model_status = "lexicon"
        logger.warning("Arabic sentiment transformer failed to load — lexicon fallback active.")
        return analyze_with_lexicon(texts)

    _model_status = "camelbert"
    results = []

    try:
        import torch

        device = torch.device("cpu")

        for i in range(0, len(texts), batch_size):
            batch = texts[i: i + batch_size]
            try:
                inputs = tokenizer(
                    batch,
                    return_tensors="pt",
                    truncation=True,
                    max_length=128,
                    padding=True,
                )
                inputs = {k: v.to(device) for k, v in inputs.items()}

                with torch.no_grad():
                    outputs = model(**inputs)

                probs = torch.softmax(outputs.logits, dim=-1)

                raw_id2label = model.config.id2label or {}
                label_map = {
                    int(k): _normalize_label(v)
                    for k, v in raw_id2label.items()
                }

                for j, prob in enumerate(probs):
                    pred_idx = int(torch.argmax(prob).item())
                    sentiment = label_map.get(pred_idx, "محايد")
                    confidence = float(prob[pred_idx].item())
                    results.append({
                        "text": batch[j],
                        "sentiment": sentiment,
                        "confidence": round(confidence, 4),
                        "model": "camelbert",
                    })
            except Exception as batch_e:
                logger.warning("Transformer inference failed for batch (%s) — falling back to lexicon", batch_e)
                results.extend(analyze_with_lexicon(batch))

    except Exception as e:
        logger.warning("Transformer inference failed (%s) — falling back to lexicon", e)
        _model_status = "lexicon"
        return analyze_with_lexicon(texts)

    return results


def analyze_with_lexicon(texts: List[str]) -> List[Dict[str, Any]]:
    logger.info("Using lexicon-based sentiment analysis")
    results = []

    for text in texts:
        text_str = str(text).lower()
        pos_count = sum(1 for w in POSITIVE_WORDS if w in text_str)
        neg_count = sum(1 for w in NEGATIVE_WORDS if w in text_str)

        total = pos_count + neg_count
        if total == 0:
            sentiment = "محايد"
            confidence = 0.5
        elif pos_count > neg_count:
            sentiment = "إيجابي"
            confidence = min(0.9, 0.5 + (pos_count - neg_count) / (total + 1) * 0.4)
        elif neg_count > pos_count:
            sentiment = "سلبي"
            confidence = min(0.9, 0.5 + (neg_count - pos_count) / (total + 1) * 0.4)
        else:
            sentiment = "محايد"
            confidence = 0.4

        results.append({
            "text": str(text),
            "sentiment": sentiment,
            "confidence": round(confidence, 4),
            "model": "lexicon",
        })

    return results


def analyze_reviews_sentiment(input_path: str = None, output_path: str = None) -> pd.DataFrame:
    if input_path is None:
        for path in [
            os.path.join("data", "processed", "reviews_normalized.csv"),
            os.path.join("data", "processed", "reviews_cleaned.csv"),
            os.path.join("data", "raw", "reviews_raw.csv"),
            os.path.join("data", "sample", "sample_reviews.csv"),
        ]:
            if os.path.exists(path):
                input_path = path
                break

    if output_path is None:
        output_path = os.path.join("data", "processed", "sentiment_results.csv")

    if not input_path or not os.path.exists(input_path):
        logger.error("Review file not found")
        return pd.DataFrame()

    logger.info("=" * 60)
    logger.info("Starting sentiment analysis")
    logger.info("=" * 60)

    try:
        df = pd.read_csv(input_path, encoding="utf-8-sig")
    except UnicodeDecodeError:
        df = pd.read_csv(input_path, encoding="utf-8")

    if "text" not in df.columns:
        logger.error("Column 'text' not found")
        return pd.DataFrame()

    texts = df["text"].fillna("").tolist()
    logger.info("Analyzing %d texts...", len(texts))

    results = analyze_with_arabic_sentiment(texts)
    results_df = pd.DataFrame(results)

    for col in ["app_name", "sector", "date", "rating"]:
        if col in df.columns:
            results_df[col] = df[col].values[: len(results_df)]

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    results_df.to_csv(output_path, index=False, encoding="utf-8-sig")

    pos = (results_df["sentiment"] == "إيجابي").sum()
    neg = (results_df["sentiment"] == "سلبي").sum()
    neu = (results_df["sentiment"] == "محايد").sum()
    model_used = results_df["model"].iloc[0] if len(results_df) > 0 else "unknown"

    total = len(results_df)
    pos_pct = round(pos / total * 100, 1) if total > 0 else 0.0
    neu_pct = round(neu / total * 100, 1) if total > 0 else 0.0
    neg_pct = round(neg / total * 100, 1) if total > 0 else 0.0

    logger.info("\nSentiment results (%s):", model_used)
    logger.info("  Positive: %s (%s%%)", pos, pos_pct)
    logger.info("  Neutral:  %s (%s%%)", neu, neu_pct)
    logger.info("  Negative: %s (%s%%)", neg, neg_pct)
    logger.info("Saved results: %s", output_path)

    return results_df


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%H:%M:%S",
    )
    result = analyze_reviews_sentiment()
    print(f"\nTotal reviews analyzed: {len(result)}")
