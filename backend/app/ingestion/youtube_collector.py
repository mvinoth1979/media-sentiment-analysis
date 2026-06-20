import hashlib
import logging
import re
import unicodedata
from datetime import datetime, timezone

_LOW_SIGNAL_WORDS = {
    "nice", "good", "great", "super", "wow", "ok", "okay", "yes", "no",
    "lol", "haha", "hehe", "thanks", "thank", "cool", "awesome", "amazing",
    "best", "love", "like", "same", "true", "facts", "real", "bro", "sir",
    "ma", "mam", "👍", "❤️", "🔥", "💯", "😍", "🙏", "👏", "😊", "💪",
}

def _is_low_signal(text: str) -> bool:
    stripped = text.strip()
    if len(stripped) < 8:
        return True
    # strip emojis/punctuation and check if only low-signal words remain
    clean = "".join(
        c for c in stripped.lower()
        if unicodedata.category(c) not in ("So", "Cn") and c.isalpha() or c == " "
    ).strip()
    if not clean:
        return True  # pure emoji comment
    words = set(clean.split())
    return bool(words) and words.issubset(_LOW_SIGNAL_WORDS)

import feedparser

from app.config import settings
from app.ingestion.youtube_quota import quota_manager

log = logging.getLogger(__name__)

_CHANNEL_RSS_URL = "https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
_VIDEO_URL = "https://www.youtube.com/watch?v={video_id}"
_COMMENT_URL = "https://www.youtube.com/watch?v={video_id}&lc={comment_id}"


def _content_hash(prefix: str, unique_id: str) -> str:
    return hashlib.sha256(f"{prefix}::{unique_id}".encode()).hexdigest()


def _channel_credibility(subscriber_count: int) -> float:
    if subscriber_count >= 1_000_000:
        return 0.75
    if subscriber_count >= 100_000:
        return 0.65
    return 0.50


def _parse_iso_duration(duration: str) -> int:
    """Convert ISO 8601 duration (e.g. PT14M35S) to total seconds."""
    m = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", duration or "")
    if not m:
        return 0
    h, mins, s = (int(x or 0) for x in m.groups())
    return h * 3600 + mins * 60 + s


def _parse_yt_datetime(raw: str) -> str:
    for fmt in ("%Y-%m-%dT%H:%M:%S+00:00", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S%z"):
        try:
            return datetime.strptime(raw, fmt).replace(tzinfo=timezone.utc).isoformat()
        except ValueError:
            continue
    return datetime.now(timezone.utc).isoformat()


def _build_client():
    # Lazy import — keeps the module loadable even if package is not yet installed,
    # so a missing dependency never crashes the whole FastAPI app on startup.
    try:
        from googleapiclient.discovery import build
    except ImportError:
        raise RuntimeError(
            "google-api-python-client is not installed. "
            "Add it to requirements.txt and redeploy."
        )
    return build("youtube", "v3", developerKey=settings.youtube_api_key, cache_discovery=False)


def _is_quota_error(e: Exception) -> bool:
    """True when the YouTube API returned HTTP 403 (quota exceeded or forbidden)."""
    try:
        from googleapiclient.errors import HttpError
        return isinstance(e, HttpError) and e.resp.status == 403
    except ImportError:
        return False


def get_channel_rss_videos(channel_id: str, brand_id: str) -> list[dict]:
    """
    Free — no API quota. Uses YouTube's public channel RSS feed.
    Returns up to 15 latest uploads. Parsed with feedparser (already a dependency).
    """
    url = _CHANNEL_RSS_URL.format(channel_id=channel_id)
    try:
        feed = feedparser.parse(url)
    except Exception as e:
        log.error("YouTube channel RSS failed for %s: %s", channel_id, e)
        return []

    channel_name = feed.feed.get("title", "YouTube Channel")
    articles = []
    for entry in feed.entries:
        video_url = entry.get("link", "")
        if not video_url:
            continue
        video_id = entry.get("yt_videoid", "")
        title = entry.get("title", "")
        body = entry.get("summary", "") or ""
        articles.append({
            "brand_id": brand_id,
            "content_hash": _content_hash("youtube_video", video_url),
            "portal_id": "youtube_channel",
            "portal_name": channel_name,
            "url": video_url,
            "title": title,
            "body": body,
            "author": channel_name,
            "published_at": _parse_yt_datetime(entry.get("published", "")),
            "language": "en",
            "source_credibility": 0.70,
            "source_type": "youtube_video",
            "external_id": video_id,
            "reach_score": 0,
            "reach_metadata": {},
        })

    return articles


def search_brand_videos(keywords: list[str], language: str,
                        brand_id: str, max_results: int = 10) -> list[dict]:
    """
    100 units per search call + 1 unit per video detail batch + 1 unit per channel lookup.
    Searches YouTube for videos matching brand keywords, enriches with statistics.
    Skips Shorts (<= 61 seconds). Returns article dicts with source_type='youtube_video'.
    """
    if not settings.youtube_api_key:
        log.warning("YOUTUBE_API_KEY not configured — skipping YouTube search")
        return []
    if not quota_manager.can_search():
        log.warning("YouTube quota exhausted — skipping search for brand %s", brand_id[:8])
        return []

    query = " ".join(keywords[:3])
    try:
        yt = _build_client()
        search_resp = yt.search().list(
            q=query,
            type="video",
            part="snippet",
            maxResults=max_results,
            relevanceLanguage=language,
            regionCode="IN",
        ).execute()
        quota_manager.record_search()
    except Exception as e:
        if _is_quota_error(e):
            quota_manager.trip()
        log.error("YouTube search.list failed: %s", e)
        return []

    video_ids = [
        item["id"]["videoId"]
        for item in search_resp.get("items", [])
        if "videoId" in item.get("id", {})
    ]
    if not video_ids:
        return []

    # Batch fetch statistics + content details (1 unit for the whole batch)
    if not quota_manager.can_fetch():
        log.warning("YouTube quota exhausted before video detail fetch")
        return []
    try:
        detail_resp = yt.videos().list(
            id=",".join(video_ids),
            part="snippet,statistics,contentDetails",
        ).execute()
        quota_manager.record_fetch()
    except Exception as e:
        if _is_quota_error(e):
            quota_manager.trip()
        log.error("YouTube videos.list failed: %s", e)
        return []

    articles = []
    for item in detail_resp.get("items", []):
        video_id = item["id"]
        snippet = item.get("snippet", {})
        stats = item.get("statistics", {})
        content = item.get("contentDetails", {})

        duration_s = _parse_iso_duration(content.get("duration", ""))
        # Skip YouTube Shorts — different engagement pattern, deferred to Phase 2.1
        if 0 < duration_s <= 61:
            continue

        view_count = int(stats.get("viewCount", 0))
        like_count = int(stats.get("likeCount", 0))
        comment_count = int(stats.get("commentCount", 0))

        # Fetch channel subscriber count for credibility tier (1 unit per channel)
        sub_count = 0
        channel_id = snippet.get("channelId", "")
        if channel_id and quota_manager.can_fetch():
            try:
                ch_resp = yt.channels().list(id=channel_id, part="statistics").execute()
                quota_manager.record_fetch()
                if ch_resp.get("items"):
                    sub_count = int(ch_resp["items"][0]["statistics"].get("subscriberCount", 0))
            except Exception:
                pass   # credibility defaults to 0.50

        video_url = _VIDEO_URL.format(video_id=video_id)
        reach_metadata = {
            "view_count": view_count,
            "like_count": like_count,
            "comment_count": comment_count,
            "channel_subscriber_count": sub_count,
            "video_duration_seconds": duration_s,
        }

        articles.append({
            "brand_id": brand_id,
            "content_hash": _content_hash("youtube_video", video_url),
            "portal_id": "youtube_search",
            "portal_name": "YouTube",
            "url": video_url,
            "title": snippet.get("title", ""),
            "body": snippet.get("description", ""),
            "author": snippet.get("channelTitle", ""),
            "published_at": _parse_yt_datetime(snippet.get("publishedAt", "")),
            "language": language,
            "source_credibility": _channel_credibility(sub_count),
            "source_type": "youtube_video",
            "external_id": video_id,
            "reach_score": min(view_count // 10_000, 100),
            "reach_metadata": reach_metadata,
            "_comment_count": comment_count,   # internal gate — stripped before save
        })

    return articles


def get_video_comments(video_id: str, brand_id: str,
                       max_comments: int = 20) -> list[dict]:
    """
    1 unit per call. Fetches top comments sorted by relevance.
    Each comment becomes a separate article with source_type='youtube_comment'.
    Comments with fewer than 5 characters are skipped.
    """
    if not quota_manager.can_fetch():
        return []
    try:
        yt = _build_client()
        resp = yt.commentThreads().list(
            videoId=video_id,
            part="snippet",
            maxResults=min(max_comments, 100),
            order="relevance",
            textFormat="plainText",
        ).execute()
        quota_manager.record_fetch()
    except Exception as e:
        if _is_quota_error(e):
            reason = str(e)
            if "disabled" in reason or "commentsDisabled" in reason:
                log.debug("Comments disabled for video %s", video_id)
            else:
                quota_manager.trip()
        log.error("YouTube commentThreads.list failed for %s: %s", video_id, e)
        return []

    articles = []
    for item in resp.get("items", []):
        top = item["snippet"]["topLevelComment"]["snippet"]
        comment_id = item["id"]
        text = top.get("textDisplay", "").strip()
        if len(text) < 5:
            continue

        if _is_low_signal(text):
            continue

        like_count = int(top.get("likeCount", 0))
        comment_url = _COMMENT_URL.format(video_id=video_id, comment_id=comment_id)

        articles.append({
            "brand_id": brand_id,
            "content_hash": _content_hash("youtube_comment", comment_url),
            "portal_id": "youtube_comment",
            "portal_name": "YouTube Comments",
            "url": comment_url,
            "title": text[:120],
            "body": text,              # full text for NLP — stripped by save_article before DB insert
            "author": top.get("authorDisplayName", ""),
            "published_at": _parse_yt_datetime(top.get("publishedAt", "")),
            "language": "en",          # langdetect in NLP router will override for non-EN
            "source_credibility": 0.45,
            "source_type": "youtube_comment",
            "external_id": comment_id,
            "reach_score": min(like_count, 100),
            "reach_metadata": {"like_count": like_count},
        })

    return articles


def collect_youtube_for_brand(brand: dict, config: dict) -> list[dict]:
    """
    Top-level function called by orchestrator.py.
    Runs channel RSS (free) + keyword search + comments for one brand.
    Sub-caps: 10 videos, 50 comments — YouTube cannot crowd out news articles.
    Strips internal _comment_count field before returning.
    """
    brand_id = brand["id"]
    keywords = config.get("keywords", [])
    channel_ids = config.get("youtube_channel_ids") or []
    results: list[dict] = []

    # Step 1 — brand's own channel uploads (free, no quota)
    for channel_id in channel_ids:
        results.extend(get_channel_rss_videos(channel_id, brand_id))

    # Step 2 — keyword search across YouTube (100 units)
    videos = search_brand_videos(keywords, "en", brand_id, max_results=10)
    videos = videos[:10]
    results.extend(videos)

    # Step 3 — comments on matched videos (1 unit each, cap 50 total)
    comment_cap = 50
    comments_collected = 0
    for video in videos:
        if comments_collected >= comment_cap:
            break
        if video.get("_comment_count", 0) == 0:
            continue
        remaining = comment_cap - comments_collected
        comments = get_video_comments(
            video["external_id"], brand_id, max_comments=min(20, remaining)
        )
        results.extend(comments)
        comments_collected += len(comments)

    for r in results:
        r.pop("_comment_count", None)

    log.info("YouTube collected %d items (quota used: %d units) for brand %s",
             len(results), quota_manager.units_used, brand_id[:8])
    return results
