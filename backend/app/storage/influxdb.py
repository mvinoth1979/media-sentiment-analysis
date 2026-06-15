from datetime import datetime, timezone
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
from app.config import settings


def _client():
    return InfluxDBClient(
        url=settings.influxdb_url,
        token=settings.influxdb_token,
        org=settings.influxdb_org,
    )


def write_sentiment_point(brand_id: str, perception_score: float,
                           counts: dict, timestamp: datetime | None = None):
    ts = timestamp or datetime.now(timezone.utc)
    point = (
        Point("brand_sentiment")
        .tag("brand_id", brand_id)
        .field("perception_score", perception_score)
        .field("positive_count", counts.get("positive", 0))
        .field("negative_count", counts.get("negative", 0))
        .field("neutral_count",  counts.get("neutral", 0))
        .field("total_count",    counts.get("total", 0))
        .time(ts)
    )
    with _client() as c:
        c.write_api(write_options=SYNCHRONOUS).write(
            bucket=settings.influxdb_bucket, record=point
        )


def query_sentiment_trend(brand_id: str, days: int = 7) -> list[dict]:
    flux = f'''
from(bucket: "{settings.influxdb_bucket}")
  |> range(start: -{days}d)
  |> filter(fn: (r) => r._measurement == "brand_sentiment")
  |> filter(fn: (r) => r.brand_id == "{brand_id}")
  |> filter(fn: (r) => r._field == "perception_score")
  |> aggregateWindow(every: 1h, fn: mean, createEmpty: false)
  |> yield(name: "mean")
'''
    with _client() as c:
        tables = c.query_api().query(flux, org=settings.influxdb_org)
        return [
            {"time": record.get_time().isoformat(), "value": record.get_value()}
            for table in tables for record in table.records
        ]
