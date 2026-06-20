import hashlib
import logging
from datetime import datetime, timezone

import httpx

log = logging.getLogger(__name__)

_DEFAULT_SUBREDDITS = [
    "india", "IndianStockMarket", "indiabusiness", "IndiaInvestments", "LegalAdviceIndia"
]

_HEADERS = {"User-Agent": "MediaSense:v1.0 (media sentiment monitoring tool)"}
_BASE = "https://www.reddit.com"
_TIMEOUT = 10.0


def _reddit_hash(reddit_id: str) -> str:
    return hashlib.sha256(f"reddit:{reddit_id}".encode()).hexdigest()[:32]


def _content_hash(prefix: str, unique_id: str) -> str:
    return hashlib.sha256(f"{prefix}::{unique_id}".encode()).hexdigest()


def _search_posts(subreddit: str, keyword: str) -> list[dict]:
    """Search a subreddit for posts matching keyword (last 7 days, newest first)."""
    url = f"{_BASE}/r/{subreddit}/search.json"
    params = {
        "q": keyword,
        "sort": "new",
        "limit": 10,
        "restrict_sr": "on",
        "t": "week",
    }
    try:
        resp = httpx.get(url, params=params, headers=_HEADERS, timeout=_TIMEOUT)
        resp.raise_for_status()
        return resp.json().get("data", {}).get("children", [])
    except Exception as e:
        log.warning("Reddit search failed for r/%s + '%s': %s", subreddit, keyword, e)
        return []


def _fetch_comments(subreddit: str, post_id: str) -> list[dict]:
    """Fetch top-level comments for a post."""
    url = f"{_BASE}/r/{subreddit}/comments/{post_id}.json"
    try:
        resp = httpx.get(url, headers=_HEADERS, timeout=_TIMEOUT)
        resp.raise_for_status()
        listing = resp.json()
        if isinstance(listing, list) and len(listing) > 1:
            return listing[1].get("data", {}).get("children", [])
    except Exception as e:
        log.debug("Comment fetch failed for post %s: %s", post_id, e)
    return []


def collect_reddit_for_brand(brand: dict, config: dict) -> list[dict]:
    """Collect Reddit posts + top comments for brand keywords across configured subreddits.

    Uses the public Reddit JSON API — no OAuth credentials required.
    Sub-caps: 10 posts per subreddit/keyword pair, 5 comments per post.
    """
    brand_id = brand["id"]
    keywords = config.get("keywords", [])[:3]
    subreddits = config.get("reddit_subreddits") or _DEFAULT_SUBREDDITS
    subreddits = subreddits[:5]

    if not keywords:
        return []

    articles: list[dict] = []
    seen_urls: set[str] = set()

    for subreddit_name in subreddits:
        for keyword in keywords:
            children = _search_posts(subreddit_name, keyword)

            for child in children:
                post = child.get("data", {})
                post_id = post.get("id", "")
                permalink = post.get("permalink", "")
                if not post_id or not permalink:
                    continue

                post_url = f"{_BASE}{permalink}"
                if post_url in seen_urls:
                    continue
                seen_urls.add(post_url)

                title = post.get("title", "")
                body = (post.get("selftext") or "")[:2000]
                subreddit_display = post.get("subreddit", subreddit_name)

                articles.append({
                    "brand_id": brand_id,
                    "content_hash": _content_hash("reddit_post", post_url),
                    "story_hash": _reddit_hash(post_id),
                    "portal_id": f"reddit_{subreddit_display.lower()}",
                    "portal_name": f"r/{subreddit_display}",
                    "url": post_url,
                    "title": title,
                    "body": body,
                    "author": post.get("author", ""),
                    "published_at": datetime.fromtimestamp(
                        post.get("created_utc", 0), tz=timezone.utc
                    ).isoformat(),
                    "language": "en",
                    "source_type": "reddit_post",
                    "source_credibility": 0.65,
                    "is_regulatory_source": False,
                    "reach_metadata": {
                        "upvotes": post.get("score", 0),
                        "upvote_ratio": round(post.get("upvote_ratio", 0.5), 3),
                        "comment_count": post.get("num_comments", 0),
                        "subreddit": subreddit_display,
                    },
                })

                # Top 5 comments with meaningful content
                for comment_child in _fetch_comments(subreddit_display, post_id)[:5]:
                    comment = comment_child.get("data", {})
                    body_text = comment.get("body", "")
                    if not body_text or len(body_text.split()) < 5:
                        continue
                    comment_id = comment.get("id", "")
                    comment_url = f"{post_url}{comment_id}/"
                    if comment_url in seen_urls:
                        continue
                    seen_urls.add(comment_url)

                    articles.append({
                        "brand_id": brand_id,
                        "content_hash": _content_hash("reddit_comment", comment_url),
                        "story_hash": _reddit_hash(comment_id),
                        "portal_id": f"reddit_{subreddit_display.lower()}",
                        "portal_name": f"r/{subreddit_display}",
                        "url": comment_url,
                        "title": f"Re: {title}"[:200],
                        "body": body_text[:1500],
                        "author": comment.get("author", ""),
                        "published_at": datetime.fromtimestamp(
                            comment.get("created_utc", 0), tz=timezone.utc
                        ).isoformat(),
                        "language": "en",
                        "source_type": "reddit_comment",
                        "source_credibility": 0.5,
                        "is_regulatory_source": False,
                        "reach_metadata": {
                            "upvotes": comment.get("score", 0),
                            "parent_post_id": post_id,
                            "subreddit": subreddit_display,
                        },
                    })

    log.info("Brand %s: Reddit collected %d items", brand_id[:8], len(articles))
    return articles
