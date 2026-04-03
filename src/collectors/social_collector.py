from __future__ import annotations

import asyncio
import logging
import os
import sys
import time
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional

import pandas as pd

try:
    from src.models.sentiment_marbert import analyze_with_arabic_sentiment as _marbert_analyze
except Exception:
    _marbert_analyze = None

try:
    from ntscraper import Nitter as _Nitter
except ImportError:
    _Nitter = None

try:
    from dotenv import load_dotenv
    _PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    _ENV_FILE = os.path.join(_PROJECT_ROOT, ".env")
    load_dotenv(dotenv_path=_ENV_FILE, override=False)
except ImportError:
    pass

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

logger = logging.getLogger(__name__)

CHANNEL_SECTOR_MAP: Dict[str, str] = {
    "CreemUber": "نقل",
    "Captains_saudi": "نقل",
    "uberjeeny": "نقل",
    "KSA_Uber_Group": "نقل",
    "qwfffgh": "توصيل",
    "KeeTarider": "توصيل",
    "Bolt_Bo": "توصيل",
    "mnadabaldahh": "توصيل",
    "jad_app": "توصيل",
    "WxPz6Bi4FPxiNmE0": "عام",
    "qw2023o": "عام",
    "captainscounci": "عام",
}

TWITTER_HASHTAGS: List[str] = ["#هنقرستيشن", "#أوبر", "#جاهز"]
HASHTAG_SECTOR_MAP: Dict[str, str] = {
    "#هنقرستيشن": "توصيل",
    "#أوبر": "نقل",
    "#جاهز": "توصيل",
}

LOOKBACK_DAYS: int = 30
MAX_TWEETS_PER_HASHTAG: int = 100
CHANNEL_DELAY_SEC: float = 2.0
TELEGRAM_SAFETY_LIMIT: int = 2000

OUTPUT_PATH: str = os.path.join("data", "raw", "social_raw.csv")


def _load_session_string() -> str:
    session = os.getenv("TELEGRAM_SESSION_STRING", "").strip()
    if session:
        return session
    try:
        import streamlit as _st
        session = (_st.secrets.get("TELEGRAM_SESSION_STRING") or "").strip()
        if session:
            return session
    except Exception:
        pass
    session_file = os.path.join("data", "raw", "string_session.txt")
    if os.path.exists(session_file):
        try:
            with open(session_file, "r", encoding="utf-8") as f:
                session = f.read().strip()
            if session:
                return session
        except Exception as e:
            logger.warning("Failed to read session file %s: %s", session_file, e)
    return ""


async def _collect_telegram_channel(
    client,
    channel_username: str,
    sector: str,
    since: datetime,
) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    cutoff = since.replace(tzinfo=timezone.utc)
    try:
        entity = await client.get_entity(channel_username)
        async for message in client.iter_messages(
            entity,
            limit=TELEGRAM_SAFETY_LIMIT,
            offset_date=datetime.now(tz=timezone.utc),
            reverse=False,
        ):
            if message.date is None:
                continue
            msg_date = message.date
            if msg_date.tzinfo is None:
                msg_date = msg_date.replace(tzinfo=timezone.utc)
            if msg_date < cutoff:
                break
            if not message.text:
                continue
            records.append({
                "platform": "Telegram",
                "channel_or_tag": channel_username,
                "sector": sector,
                "text": message.text,
                "date": msg_date.strftime("%Y-%m-%d"),
                "message_id": str(message.id),
            })
        logger.info("Telegram %s (%s): %d messages", channel_username, sector, len(records))
    except Exception as exc:
        logger.warning("Telegram channel %s failed: %s", channel_username, exc)
    return records


async def collect_telegram(
    since: Optional[datetime] = None,
    api_id: int = 0,
    api_hash: str = "",
) -> List[Dict[str, Any]]:
    try:
        from telethon import TelegramClient
        from telethon.sessions import StringSession
    except ImportError:
        logger.error("telethon not installed")
        return []

    if not api_id or not api_hash:
        logger.error("Telegram credentials missing")
        return []

    session_string = _load_session_string()
    if not session_string:
        logger.error("No TELEGRAM_SESSION_STRING found — skipping Telegram collection")
        return []

    if since is None:
        since = datetime.now(tz=timezone.utc) - timedelta(days=LOOKBACK_DAYS)

    all_records: List[Dict[str, Any]] = []
    client = TelegramClient(StringSession(session_string), api_id, api_hash)
    try:
        await client.start()
        for channel, sector in CHANNEL_SECTOR_MAP.items():
            try:
                records = await _collect_telegram_channel(client, channel, sector, since)
                all_records.extend(records)
            except Exception as exc:
                if "FloodWait" in type(exc).__name__:
                    wait_sec = getattr(exc, "seconds", 60)
                    logger.warning("FloodWait on %s: sleeping %ds", channel, wait_sec)
                    await asyncio.sleep(wait_sec)
                else:
                    logger.warning("Skipping channel %s: %s", channel, exc)
            await asyncio.sleep(CHANNEL_DELAY_SEC)
    finally:
        await client.disconnect()

    logger.info("Telegram total: %d messages", len(all_records))
    return all_records


def collect_twitter(since: Optional[datetime] = None) -> List[Dict[str, Any]]:
    SAMPLE_PATH = os.path.join("data", "sample", "twitter_sample.csv")

    if since is None:
        since = datetime.now() - timedelta(days=LOOKBACK_DAYS)

    cached_records: List[Dict[str, Any]] = []
    if os.path.exists(SAMPLE_PATH):
        try:
            sample_df = pd.read_csv(SAMPLE_PATH, parse_dates=["date"])
            cached_records = sample_df.to_dict("records")
            for r in cached_records:
                r["_cached"] = True
            logger.info("Twitter cached baseline: %d records", len(cached_records))
        except Exception as e:
            logger.warning("Twitter cached load failed: %s", e)

    if _Nitter is None:
        logger.warning("ntscraper not installed — using cached Twitter data only")
        return cached_records

    live_records: List[Dict[str, Any]] = []
    try:
        scraper = _Nitter(log_level=1, skip_instance_check=False)
        since_str = since.strftime("%Y-%m-%d")
        for hashtag in TWITTER_HASHTAGS:
            sector = HASHTAG_SECTOR_MAP.get(hashtag, "عام")
            query = hashtag.lstrip("#")
            try:
                results = scraper.get_tweets(
                    query, mode="hashtag", number=MAX_TWEETS_PER_HASHTAG, since=since_str,
                )
                tweets = results.get("tweets", []) if isinstance(results, dict) else []
                for tweet in tweets:
                    try:
                        text = tweet.get("text", "")
                        if not text:
                            continue
                        date_raw = tweet.get("date", "")
                        parsed_date = pd.to_datetime(date_raw, dayfirst=False, errors="coerce")
                        date_str = parsed_date.strftime("%Y-%m-%d") if pd.notna(parsed_date) else str(since.date())
                        live_records.append({
                            "platform": "Twitter/X",
                            "channel_or_tag": hashtag,
                            "sector": sector,
                            "text": text,
                            "date": date_str,
                            "message_id": tweet.get("tweet_id", ""),
                        })
                    except Exception:
                        continue
                logger.info("Twitter live %s: %d tweets", hashtag, len(tweets))
            except Exception as exc:
                logger.warning("Twitter hashtag %s failed: %s", hashtag, exc)
            time.sleep(3)
    except Exception as e:
        logger.warning("Twitter live scrape failed: %s — using cached data", e)
        return cached_records

    return live_records if live_records else cached_records


def _is_valid_telegram_id(raw_id) -> bool:
    if raw_id is None:
        return False
    try:
        return int(str(raw_id).strip()) > 0
    except (ValueError, TypeError):
        return False


def _compute_polarity_marbert(texts: List[str]) -> List[float]:
    if _marbert_analyze is None:
        logger.warning("MARBERT not available — using lexicon fallback")
        return _compute_polarity_lexicon(texts)
    try:
        results = _marbert_analyze(texts)
        sentiment_map = {"إيجابي": 1.0, "محايد": 0.5, "سلبي": 0.0}
        return [sentiment_map.get(r.get("sentiment", "محايد"), 0.5) for r in results]
    except Exception as e:
        logger.warning("MARBERT inference failed (%s) — falling back to lexicon", e)
        return _compute_polarity_lexicon(texts)


def _compute_polarity_lexicon(texts: List[str]) -> List[float]:
    positive_kw = [
        "ممتاز", "رائع", "سريع", "شكرا", "ممنون", "مميز", "خدمة", "جيد",
        "يستاهل", "احترافي", "نظيف", "ارخص", "افضل",
        "excellent", "great", "fast", "good", "thanks",
    ]
    negative_kw = [
        "سيء", "ردي", "احتيال", "غلط", "متأخر", "غالي", "مشكلة", "خطأ",
        "تاخر", "ايقاف", "حادث", "رفض",
        "bad", "fraud", "slow", "expensive", "problem", "late", "cancelled",
    ]
    scores = []
    for text in texts:
        t = str(text).lower()
        pos = sum(1 for w in positive_kw if w in t)
        neg = sum(1 for w in negative_kw if w in t)
        if pos + neg == 0:
            scores.append(0.5)
        else:
            scores.append(pos / (pos + neg))
    return scores


def run_social_collector(since: Optional[datetime] = None) -> pd.DataFrame:
    logger.info("=" * 60)
    logger.info("Platform Pulse Social Collector starting")
    logger.info("=" * 60)

    raw_api_id = os.getenv("TELEGRAM_API_ID", "")
    raw_api_hash = os.getenv("TELEGRAM_API_HASH", "")

    placeholder_hashes = ("", "YOUR_TELEGRAM_API_HASH_HERE")
    if not _is_valid_telegram_id(raw_api_id) or not raw_api_hash or raw_api_hash.strip() in placeholder_hashes:
        logger.warning("Telegram credentials not set — Telegram collection skipped")
        telegram_api_id = 0
        telegram_api_hash = ""
    else:
        try:
            telegram_api_id = int(raw_api_id.strip())
        except ValueError:
            logger.error("TELEGRAM_API_ID must be an integer")
            telegram_api_id = 0
        telegram_api_hash = raw_api_hash.strip()

    if since is None:
        since = datetime.now(tz=timezone.utc) - timedelta(days=LOOKBACK_DAYS)

    telegram_records: List[Dict[str, Any]] = []
    if telegram_api_id and telegram_api_hash:
        try:
            import nest_asyncio
            nest_asyncio.apply()
            loop = asyncio.get_event_loop_policy().get_event_loop()
            if loop.is_running():
                telegram_records = loop.run_until_complete(
                    collect_telegram(since, telegram_api_id, telegram_api_hash)
                )
            else:
                telegram_records = asyncio.run(
                    collect_telegram(since, telegram_api_id, telegram_api_hash)
                )
        except ImportError:
            try:
                telegram_records = asyncio.run(
                    collect_telegram(since, telegram_api_id, telegram_api_hash)
                )
            except Exception as exc:
                logger.error("Telegram collection failed: %s", exc)
        except Exception as exc:
            logger.error("Telegram collection failed: %s", exc)

    twitter_records: List[Dict[str, Any]] = []
    try:
        twitter_records = collect_twitter(since)
    except Exception as exc:
        logger.error("Twitter collection failed: %s", exc)

    all_records = telegram_records + twitter_records

    if not all_records:
        logger.warning("No social records collected — returning empty DataFrame")
        return pd.DataFrame(columns=["platform", "channel_or_tag", "sector", "text", "date", "message_id"])

    df = pd.DataFrame(all_records)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"])
    df = df.drop_duplicates(subset=["platform", "message_id"], keep="first")
    df = df.sort_values("date", ascending=False).reset_index(drop=True)

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

    if os.path.exists(OUTPUT_PATH):
        existing = pd.read_csv(OUTPUT_PATH, encoding="utf-8-sig")
        existing["date"] = pd.to_datetime(existing["date"], errors="coerce")
        combined = pd.concat([existing, df], ignore_index=True)
        combined = combined.drop_duplicates(subset=["platform", "message_id"], keep="last")
        combined.to_csv(OUTPUT_PATH, index=False, encoding="utf-8-sig")
        logger.info("Appended %d new — %d total in %s", len(df), len(combined), OUTPUT_PATH)
        return combined

    df.to_csv(OUTPUT_PATH, index=False, encoding="utf-8-sig")
    logger.info("Saved %d records to %s", len(df), OUTPUT_PATH)
    return df


collect_all = run_social_collector


def aggregate_social_sentiment(df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
    sample_path = os.path.join("data", "sample", "sample_social.csv")
    twitter_path = os.path.join("data", "sample", "twitter_sample.csv")

    if df is None:
        frames = []
        for path in [OUTPUT_PATH, sample_path, twitter_path]:
            if os.path.exists(path):
                try:
                    tmp = pd.read_csv(path, encoding="utf-8-sig")
                    if not tmp.empty:
                        frames.append(tmp)
                except Exception:
                    continue
        if not frames:
            logger.warning("No social data found — returning empty frame")
            return pd.DataFrame(columns=["date", "sector", "social_score", "message_count"])
        df = pd.concat(frames, ignore_index=True)

    df = df.copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date", "text"])

    texts = df["text"].tolist()
    df["polarity"] = _compute_polarity_marbert(texts)

    df["month"] = df["date"].dt.to_period("M").dt.to_timestamp()
    agg = (
        df.groupby(["month", "sector"])
        .agg(mean_polarity=("polarity", "mean"), message_count=("text", "count"))
        .reset_index()
        .rename(columns={"month": "date"})
    )
    agg["social_score"] = (agg["mean_polarity"] * 100).round(2)
    return agg[["date", "sector", "social_score", "message_count"]]


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%H:%M:%S",
    )
    result_df = run_social_collector()
    print(f"\nCollection complete. Total records: {len(result_df)}")
