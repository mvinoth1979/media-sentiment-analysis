import hashlib
import logging
import time
from datetime import datetime, timezone

import httpx

from app.config import settings

log = logging.getLogger(__name__)

_DEFAULT_SUBREDDITS = [
    "india", "IndianStockMarket", "indiabusiness", "IndiaInvestments", "LegalAdviceIndia"
]

_OAUTH_BASE = "https://oauth.reddit.com"
_TOKEN_URL  = "https://www.reddit.com/api/v1/access_token"
_TIMEOUT    = 12.0

# Module-level token cache — avoids a round-trip on every collection run
_token_cache: dict = {"token": None, "expires_at": 0.0}


def _get_headers() -> dict | None:
    """Return OAuth Authorization headers, refreshing the token when needed.

    Returns None if Reddit credentials are not configured.
    """
    client_id     = settings.reddit_client_id
    client_secret = settings.reddit_client_secret
    user_agent    = settings.reddit_user_agent or "MediaSense:v1.0"

    if not client_id or not client_secret:
        log.warning(
            "REDDIT_CLIENT_ID / REDDIT_CLIENT_SECRET not set — Reddit collection disabled. "
            "Create a script app at reddit.com/prefs/apps and add the credentials to Railway env vars."
        )
        return None

    now = time.time()
    if _token_cache["token"] and now < _token_cache["expires_at"] - 60:
        return {
            "Authorization": f"Bearer {_token_cache['token']}",
            "User-Agent": user_agent,
        }

    try:
        resp = httpx.post(
            _TOKEN_URL,
            data={"grant_type": "client_credentials"},
            auth=(client_id, client_secret),
            headers={"User-Agent": user_agent},
            timeout=_TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()
        _token_cache["token"]      = data["access_token"]
        _token_cache["expires_at"] = now + data.get("expires_in", 3600)
        log.info("Reddit OAuth token refreshed (expires in %ds)", data.get("expires_in", 3600))
        return {
            "Authorization": f"Bearer {_token_cache['token']}",
            "User-Agent": user_agent,
        }
    except Exception as e:
        log.warning("Reddit OAuth token fetch failed: %s", e)
        return None


def _reddit_hash(reddit_id: str) -> str:
    return hashlib.sha256(f"reddit:{reddit_id}".encode()).hexdigest()[:32]


def _content_hash(prefix: str, unique_id: str) -> str:
    return hashlib.sha256(f"{prefix}::{unique_id}".encode()).hexdigest()


def _search_posts(subreddit: str, keyword: str, headers: dict) -> list[dict]:
    """Search a subreddit for posts matching keyword via OAuth API."""
    url    = f"{_OAUTH_BASE}/r/{subreddit}/search"
    params = {"q": keyword, "sort": "new", "limit": 10, "restrict_sr": "on", "t": "week"}
    try:
        resp = httpx.get(url, params=params, headers=headers, timeout=_TIMEOUT)
        resp.raise_for_status()
        return resp.json().get("data", {}).get("children", [])
    except Exception as e:
        log.warning("Reddit search failed for r/%s + '%s': %s", subreddit, keyword, e)
        return []


def _fetch_listing(subreddit: str, headers: dict, kind: str = "new", limit: int = 25) -> list[dict]:
    """Fetch new/hot listing for a subreddit via OAuth API."""
    url = f"{_OAUTH_BASE}/r/{subreddit}/{kind}"
    try:
        resp = httpx.get(url, params={"limit": limit}, headers=headers, timeout=_TIMEOUT)
        resp.raise_for_status()
        return resp.json().get("data", {}).get("children", [])
    except Exception as e:
        log.warning("Reddit listing /r/%s/%s failed: %s", subreddit, kind, e)
        return []


def _fetch_comments(subreddit: str, post_id: str, headers: dict) -> list[dict]:
    """Fetch top-level comments for a post via OAuth API."""
    url = f"{_OAUTH_BASE}/r/{subreddit}/comments/{post_id}"
    try:
        resp = httpx.get(url, headers=headers, timeout=_TIMEOUT)
        resp.raise_for_status()
        listing = resp.json()
        if isinstance(listing, list) and len(listing) > 1:
            return listing[1].get("data", {}).get("children", [])
    except Exception as e:
        log.debug("Comment fetch failed for post %s: %s", post_id, e)
    return []


def collect_reddit_for_brand(brand: dict, config: dict) -> list[dict]:
    """Collect Reddit posts + top comments for brand keywords across configured subreddits.

    Uses Reddit OAuth2 client-credentials — works from cloud server IPs.
    Sub-caps: 10 posts per subreddit/keyword pair, 5 comments per post.
    """
    headers = _get_headers()
    if headers is None:
        return []

    brand_id   = brand["id"]
    keywords   = config.get("keywords", [])[:3]
    subreddits = config.get("reddit_subreddits") or _DEFAULT_SUBREDDITS
    subreddits = subreddits[:5]

    if not keywords:
        return []

    articles: list[dict] = []
    seen_urls: set[str]  = set()
    post_base            = "https://www.reddit.com"

    for subreddit_name in subreddits:
        for keyword in keywords:
            children = _search_posts(subreddit_name, keyword, headers)
            if not children:
                children = _fetch_listing(subreddit_name, headers, "new")

            for child in children:
                post = child.get("data", {})
                post_id   = post.get("id", "")
                permalink = post.get("permalink", "")
                if not post_id or not permalink:
                    continue

                post_url = f"{post_base}{permalink}"
                if post_url in seen_urls:
                    continue
                seen_urls.add(post_url)

                title            = post.get("title", "")
                body             = (post.get("selftext") or "")[:2000]
                subreddit_display = post.get("subreddit", subreddit_name)

                articles.append({
                    "brand_id":          brand_id,
                    "content_hash":      _content_hash("reddit_post", post_url),
                    "story_hash":        _reddit_hash(post_id),
                    "portal_id":         f"reddit_{subreddit_display.lower()}",
                    "portal_name":       f"r/{subreddit_display}",
                    "url":               post_url,
                    "title":             title,
                    "body":              body,
                    "author":            post.get("author", ""),
                    "published_at":      datetime.fromtimestamp(
                        post.get("created_utc", 0), tz=timezone.utc
                    ).isoformat(),
                    "language":          "en",
                    "source_type":       "reddit_post",
                    "source_credibility": 0.65,
                    "is_regulatory_source": False,
                    "reach_metadata":    {
                        "upvotes":       post.get("score", 0),
                        "upvote_ratio":  round(post.get("upvote_ratio", 0.5), 3),
                        "comment_count": post.get("num_comments", 0),
                        "subreddit":     subreddit_display,
                    },
                })

                for comment_child in _fetch_comments(subreddit_display, post_id, headers)[:5]:
                    comment   = comment_child.get("data", {})
                    body_text = comment.get("body", "")
                    if not body_text or len(body_text.split()) < 5:
                        continue
                    comment_id  = comment.get("id", "")
                    comment_url = f"{post_url}{comment_id}/"
                    if comment_url in seen_urls:
                        continue
                    seen_urls.add(comment_url)

                    articles.append({
                        "brand_id":          brand_id,
                        "content_hash":      _content_hash("reddit_comment", comment_url),
                        "story_hash":        _reddit_hash(comment_id),
                        "portal_id":         f"reddit_{subreddit_display.lower()}",
                        "portal_name":       f"r/{subreddit_display}",
                        "url":               comment_url,
                        "title":             f"Re: {title}"[:200],
                        "body":              body_text[:1500],
                        "author":            comment.get("author", ""),
                        "published_at":      datetime.fromtimestamp(
                            comment.get("created_utc", 0), tz=timezone.utc
                        ).isoformat(),
                        "language":          "en",
                        "source_type":       "reddit_comment",
                        "source_credibility": 0.5,
                        "is_regulatory_source": False,
                        "reach_metadata":    {
                            "upvotes":        comment.get("score", 0),
                            "parent_post_id": post_id,
                            "subreddit":      subreddit_display,
                        },
                    })

    log.info("Brand %s: Reddit collected %d items", brand_id[:8], len(articles))
    return articles
