import json
import boto3
from datetime import datetime, timezone
from app.config import settings


def _client():
    return boto3.client(
        "s3",
        endpoint_url=f"https://{settings.r2_account_id}.r2.cloudflarestorage.com",
        aws_access_key_id=settings.r2_access_key_id,
        aws_secret_access_key=settings.r2_secret_access_key,
        region_name="auto",
    )


def archive_article(article: dict) -> str:
    ts = datetime.now(timezone.utc)
    key = f"{article['brand_id']}/{ts.strftime('%Y/%m/%d')}/{article['content_hash']}.json"
    _client().put_object(
        Bucket=settings.r2_bucket_name,
        Key=key,
        Body=json.dumps(article, ensure_ascii=False),
        ContentType="application/json",
    )
    return key
