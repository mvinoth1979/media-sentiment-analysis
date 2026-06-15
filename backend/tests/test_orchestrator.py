from unittest.mock import patch
from app.pipeline.orchestrator import run_brand_pipeline
from app.nlp.schemas import NLPResult


def _nlp_result():
    return NLPResult(0.7, "positive", ["Amul"], ["pricing"], ["good"],
                     "gemini-2.0-flash", 0.9)


def test_pipeline_processes_new_articles():
    brand = {"id": "b1", "name": "Amul"}
    config = {"keywords": ["Amul"], "languages": ["en"], "portal_ids": []}

    mock_articles = [{"content_hash": "h1", "brand_id": "b1",
                      "title": "Amul wins", "body": "great product",
                      "portal_id": "the_hindu", "language": "en",
                      "source_credibility": 0.9, "reach_score": 5000}]

    with patch("app.pipeline.orchestrator.get_portals_for_languages", return_value=[
                {"id": "the_hindu", "name": "The Hindu", "rss_url": "u",
                 "language": "en", "credibility": 0.9}]), \
         patch("app.pipeline.orchestrator.collect_portal", return_value=mock_articles), \
         patch("app.pipeline.orchestrator.filter_new_articles", return_value=mock_articles), \
         patch("app.pipeline.orchestrator.analyse_article", return_value=_nlp_result()), \
         patch("app.pipeline.orchestrator.archive_article", return_value="key"), \
         patch("app.pipeline.orchestrator.save_article", return_value="article-id"), \
         patch("app.pipeline.orchestrator.write_sentiment_point") as mock_influx:
        stats = run_brand_pipeline(brand, config)

    assert stats["processed"] == 1
    assert stats["errors"] == 0
    mock_influx.assert_called_once()


def test_pipeline_skips_when_no_new_articles():
    brand = {"id": "b1", "name": "Amul"}
    config = {"keywords": ["Amul"], "languages": ["en"], "portal_ids": []}

    with patch("app.pipeline.orchestrator.get_portals_for_languages", return_value=[
                {"id": "the_hindu", "name": "The Hindu", "rss_url": "u",
                 "language": "en", "credibility": 0.9}]), \
         patch("app.pipeline.orchestrator.collect_portal", return_value=[]), \
         patch("app.pipeline.orchestrator.filter_new_articles", return_value=[]), \
         patch("app.pipeline.orchestrator.write_sentiment_point") as mock_influx:
        stats = run_brand_pipeline(brand, config)

    assert stats["processed"] == 0
    mock_influx.assert_not_called()


def test_pipeline_counts_portal_errors():
    brand = {"id": "b1", "name": "Amul"}
    config = {"keywords": ["Amul"], "languages": ["en"]}

    with patch("app.pipeline.orchestrator.get_portals_for_languages", return_value=[
                {"id": "the_hindu", "name": "The Hindu", "rss_url": "u",
                 "language": "en", "credibility": 0.9}]), \
         patch("app.pipeline.orchestrator.collect_portal",
               side_effect=Exception("Network error")), \
         patch("app.pipeline.orchestrator.filter_new_articles", return_value=[]), \
         patch("app.pipeline.orchestrator.write_sentiment_point") as mock_influx:
        stats = run_brand_pipeline(brand, config)

    assert stats["errors"] == 1
    assert stats["collected"] == 0
    mock_influx.assert_not_called()


def test_pipeline_nlp_none_increments_errors():
    brand = {"id": "b1", "name": "Amul"}
    config = {"keywords": ["Amul"], "languages": ["en"]}

    mock_articles = [{"content_hash": "h1", "brand_id": "b1",
                      "title": "Amul news", "body": "text",
                      "portal_id": "the_hindu", "language": "en",
                      "source_credibility": 0.9, "reach_score": 0}]

    with patch("app.pipeline.orchestrator.get_portals_for_languages", return_value=[
                {"id": "the_hindu", "name": "The Hindu", "rss_url": "u",
                 "language": "en", "credibility": 0.9}]), \
         patch("app.pipeline.orchestrator.collect_portal", return_value=mock_articles), \
         patch("app.pipeline.orchestrator.filter_new_articles", return_value=mock_articles), \
         patch("app.pipeline.orchestrator.analyse_article", return_value=None), \
         patch("app.pipeline.orchestrator.write_sentiment_point") as mock_influx:
        stats = run_brand_pipeline(brand, config)

    assert stats["processed"] == 0
    assert stats["errors"] == 1
    mock_influx.assert_not_called()


def test_pipeline_article_exception_increments_errors():
    brand = {"id": "b1", "name": "Amul"}
    config = {"keywords": ["Amul"], "languages": ["en"]}

    mock_articles = [{"content_hash": "h1", "brand_id": "b1",
                      "title": "Amul news", "body": "text",
                      "portal_id": "the_hindu", "language": "en",
                      "source_credibility": 0.9, "reach_score": 0}]

    with patch("app.pipeline.orchestrator.get_portals_for_languages", return_value=[
                {"id": "the_hindu", "name": "The Hindu", "rss_url": "u",
                 "language": "en", "credibility": 0.9}]), \
         patch("app.pipeline.orchestrator.collect_portal", return_value=mock_articles), \
         patch("app.pipeline.orchestrator.filter_new_articles", return_value=mock_articles), \
         patch("app.pipeline.orchestrator.analyse_article", return_value=_nlp_result()), \
         patch("app.pipeline.orchestrator.archive_article", side_effect=Exception("R2 error")), \
         patch("app.pipeline.orchestrator.write_sentiment_point") as mock_influx:
        stats = run_brand_pipeline(brand, config)

    assert stats["processed"] == 0
    assert stats["errors"] == 1
    mock_influx.assert_not_called()
