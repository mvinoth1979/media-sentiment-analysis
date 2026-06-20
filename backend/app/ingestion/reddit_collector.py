import hashlib
import logging
from datetime import datetime, timezone

from app.config import settings

log = logging.getLogger(__name__)

_DEFAULT_SUBREDDITS = [
    "india", "IndianStockMarket", "indiabusiness", "IndiaInvestments", "LegalAdviceIndia"
]


def _get_reddit_client():
    try:
        import praw
    except ImportError:
        raise RuntimeError(
            "praw is not installed. Add praw>=7.7 to requirements.txt and redeploy."
        )
    return praw.Reddit(
        client_id=settings.reddit_client_id,
        client_secret=settings.reddit_client_secret,
        user_agent=settings.reddit_user_agent or "MediaSense:v1.0 (by /u/mediasense)",
    )


def _reddit_hash(reddit_id: str) -> str:
    """Reddit post/comment IDs are already unique — hash for consistent column format."""
    return hashlib.sha256(f"reddit:{reddit_id}".encode()).hexdigest()[:32]


def _content_hash(prefix: str, unique_id: str) -> str:
    return hashlib.sha256(f"{prefix}::{unique_id}".encode()).hexdigest()


def collect_reddit_for_brand(brand: dict, config: dict) -> list[dict]:
    """Collect Reddit posts + top comments for brand keywords across configured subreddits.

    Sub-caps: 10 posts per subreddit/keyword pair, 5 top comments per post.
    Gracefully skips if credentials are not configured.
    """
    if not (settings.reddit_client_id and settings.reddit_client_secret):
        log.info("Reddit credentials not set — skipping Reddit collection")
        return []

    brand_id = brand["id"]
    keywords = config.get("keywords", [])[:3]
    subreddits = config.get("reddit_subreddits") or _DEFAULT_SUBREDDITS
    subreddits = subreddits[:5]

    if not keywords:
        return []

    try:
        reddit = _get_reddit_client()
    except Exception as e:
        log.error("Reddit client init failed: %s", e)
        return []

    articles: list[dict] = []
    seen_urls: set[str] = set()

    for subreddit_name in subreddits:
        for keyword in keywords:
            try:
                sub = reddit.subreddit(subreddit_name)
                for post in sub.search(keyword, sort="new", limit=10, time_filter="week"):
                    post_url = f"https://www.reddit.com{post.permalink}"
                    if post_url in seen_urls:
                        continue
                    seen_urls.add(post_url)

                    title = post.title or ""
                    body = (post.selftext or "")[:2000]

                    articles.append({
                        "brand_id": brand_id,
                        "content_hash": _content_hash("reddit_post", post_url),
                        "story_hash": _reddit_hash(post.id),
                        "portal_id": f"reddit_{post.subreddit.display_name.lower()}",
                        "portal_name": f"r/{post.subreddit.display_name}",
                        "url": post_url,
                        "title": title,
                        "body": body,
                        "author": str(post.author) if post.author else "",
                        "published_at": datetime.fromtimestamp(
                            post.created_utc, tz=timezone.utc
                        ).isoformat(),
                        "language": "en",
                        "source_type": "reddit_post",
                        "source_credibility": 0.65,
                        "is_regulatory_source": False,
                        "reach_metadata": {
                            "upvotes": post.score,
                            "upvote_ratio": round(post.upvote_ratio, 3),
                            "comment_count": post.num_comments,
                            "subreddit": post.subreddit.display_name,
                        },
                    })

                    # Top 5 comments with meaningful content
                    try:
                        post.comments.replace_more(limit=0)
                        for comment in list(post.comments)[:5]:
                            if not comment.body or len(comment.body.split()) < 5:
                                continue
                            comment_url = f"{post_url}{comment.id}/"
                            if comment_url in seen_urls:
                                continue
                            seen_urls.add(comment_url)
                            articles.append({
                                "brand_id": brand_id,
                                "content_hash": _content_hash("reddit_comment", comment_url),
                                "story_hash": _reddit_hash(comment.id),
                                "portal_id": f"reddit_{post.subreddit.display_name.lower()}",
                                "portal_name": f"r/{post.subreddit.display_name}",
                                "url": comment_url,
                                "title": f"Re: {title}"[:200],
                                "body": comment.body[:1500],
                                "author": str(comment.author) if comment.author else "",
                                "published_at": datetime.fromtimestamp(
                                    comment.created_utc, tz=timezone.utc
                                ).isoformat(),
                                "language": "en",
                                "source_type": "reddit_comment",
                                "source_credibility": 0.5,
                                "is_regulatory_source": False,
                                "reach_metadata": {
                                    "upvotes": comment.score,
                                    "parent_post_id": post.id,
                                    "subreddit": post.subreddit.display_name,
                                },
                            })
                    except Exception as e:
                        log.debug("Comment fetch failed for post %s: %s", post.id, e)

            except Exception as e:
                log.warning(
                    "Reddit search failed for r/%s + '%s': %s", subreddit_name, keyword, e
                )

    log.info("Brand %s: Reddit collected %d items", brand_id[:8], len(articles))
    return articles
