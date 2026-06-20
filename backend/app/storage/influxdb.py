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


def query_sentiment_counts_trend(brand_id: str, days: int = 30) -> list[dict]:
    """
    Returns daily positive/negative/neutral counts via Flux pivot().
    pivot() collapses 3 field-rows per timestamp into one wide row — single round-trip.
    """
    flux = f'''
from(bucket: "{settings.influxdb_bucket}")
  |> range(start: -{days}d)
  |> filter(fn: (r) => r._measurement == "brand_sentiment")
  |> filter(fn: (r) => r.brand_id == "{brand_id}")
  |> filter(fn: (r) => r._field == "positive_count" or
                        r._field == "negative_count" or
                        r._field == "neutral_count")
  |> aggregateWindow(every: 1d, fn: sum, createEmpty: false)
  |> pivot(rowKey: ["_time"], columnKey: ["_field"], valueColumn: "_value")
  |> yield(name: "daily")
'''
    try:
        with _client() as c:
            tables = c.query_api().query(flux, org=settings.influxdb_org)
            results = []
            for table in tables:
                for record in table.records:
                    results.append({
                        "time":     record.get_time().isoformat(),
                        "positive": int(record.values.get("positive_count") or 0),
                        "negative": int(record.values.get("negative_count") or 0),
                        "neutral":  int(record.values.get("neutral_count")  or 0),
                    })
            return sorted(results, key=lambda r: r["time"])
    except Exception:
        return []


def query_sentiment_counts_trend_range(
    brand_id: str,
    date_from: str,
    date_to: str,
    window: str = "1d",
) -> list[dict]:
    """Explicit date-range variant; window is a Flux duration string e.g. '1d', '1h'."""
    flux = f'''
from(bucket: "{settings.influxdb_bucket}")
  |> range(start: {date_from}, stop: {date_to})
  |> filter(fn: (r) => r._measurement == "brand_sentiment")
  |> filter(fn: (r) => r.brand_id == "{brand_id}")
  |> filter(fn: (r) => r._field == "positive_count" or
                        r._field == "negative_count" or
                        r._field == "neutral_count")
  |> aggregateWindow(every: {window}, fn: sum, createEmpty: false)
  |> pivot(rowKey: ["_time"], columnKey: ["_field"], valueColumn: "_value")
  |> yield(name: "range")
'''
    try:
        with _client() as c:
            tables = c.query_api().query(flux, org=settings.influxdb_org)
            results = []
            for table in tables:
                for record in table.records:
                    results.append({
                        "time":     record.get_time().isoformat(),
                        "positive": int(record.values.get("positive_count") or 0),
                        "negative": int(record.values.get("negative_count") or 0),
                        "neutral":  int(record.values.get("neutral_count")  or 0),
                    })
            return sorted(results, key=lambda r: r["time"])
    except Exception:
        return []


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
