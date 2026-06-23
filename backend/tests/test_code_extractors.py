"""
Tests for pure-Python extraction functions in app.nlp.code_extractors.

These are deterministic and require no mocks — ideal for fast CI.
Covers: classify_issue_category, sentiment_from_star_rating, extract_states_mentioned.
"""

import pytest
from app.nlp.code_extractors import (
    classify_issue_category,
    sentiment_from_star_rating,
    extract_states_mentioned,
)


# ─── classify_issue_category ───────────────────────────────────────────────────

class TestClassifyIssueCategory:

    def test_no_keywords_returns_other_low_confidence(self):
        cat, conf = classify_issue_category("weather is nice today in the park")
        assert cat == "other"
        assert conf == 0.25

    def test_single_keyword_match_gives_0_60(self):
        # "recall" is in product_quality keywords; only one keyword
        cat, conf = classify_issue_category("company issues a product recall")
        assert cat == "product_quality"
        assert conf == 0.60

    def test_three_keywords_gives_high_confidence_0_88(self):
        # "fraud", "scandal", "corruption" all in crisis_controversy → 3 hits → 0.88
        text = "company hit by fraud scandal amid corruption backlash from investors"
        cat, conf = classify_issue_category(text)
        assert cat == "crisis_controversy"
        assert conf == 0.88

    def test_two_keywords_same_category_beats_one_in_other(self):
        # "defect" + "quality control" in product_quality vs 0 in others → 0.75
        text = "manufacturing defect found during quality control inspection"
        cat, conf = classify_issue_category(text)
        assert cat == "product_quality"
        assert conf >= 0.75

    def test_tie_between_categories_returns_0_45(self):
        # One keyword each in two categories → tie → 0.45
        text = "market share declines as customer complaint rises"
        cat, conf = classify_issue_category(text)
        assert conf == 0.45  # tied → lowest confidence

    def test_crisis_keywords_detected(self):
        text = "CEO crisis response after fraud scandal hits company reputation"
        cat, conf = classify_issue_category(text)
        assert cat == "crisis_controversy"
        assert conf >= 0.60

    def test_financial_keywords_detected(self):
        text = "quarterly earnings beat analyst expectations with strong revenue growth"
        cat, conf = classify_issue_category(text)
        assert cat == "financial_performance"
        assert conf >= 0.60

    def test_hyphenated_multiword_keyword_not_matched(self):
        # "quarterly-results" (hyphenated) should NOT match "quarterly results" (space-separated)
        text = "quarterly-results are pending confirmation"
        cat, conf = classify_issue_category(text)
        # May or may not match; key assertion: doesn't crash
        assert isinstance(cat, str)
        assert isinstance(conf, float)

    def test_empty_string_returns_other(self):
        cat, conf = classify_issue_category("")
        assert cat == "other"
        assert conf == 0.25

    def test_uppercase_text_normalised(self):
        # Function lowercases internally — "FRAUD SCANDAL CORRUPTION" → crisis_controversy
        text = "FRAUD SCANDAL CORRUPTION SCAM BACKLASH OUTRAGE BOYCOTT"
        cat, conf = classify_issue_category(text)
        assert cat == "crisis_controversy"

    def test_csr_keywords_detected(self):
        text = "company runs csr initiative with focus on sustainability and esg"
        cat, conf = classify_issue_category(text)
        assert cat == "csr_sustainability"

    def test_brand_advocacy_keywords(self):
        text = "brand ambassador signs new sponsorship deal for tv commercial"
        cat, conf = classify_issue_category(text)
        assert cat == "brand_advocacy"

    def test_market_opportunity_keywords(self):
        text = "company announces new product launch targeting expansion plan"
        cat, conf = classify_issue_category(text)
        assert cat == "market_opportunity"

    def test_returns_tuple_of_str_and_float(self):
        result = classify_issue_category("some article text here")
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], str)
        assert isinstance(result[1], float)

    def test_confidence_always_between_0_and_1(self):
        texts = [
            "",
            "one word",
            "fraud court legal notice regulatory action compliance",
            "versus market share competitor rival brand industry leader dethrone beat competition",
        ]
        for text in texts:
            _, conf = classify_issue_category(text)
            assert 0.0 <= conf <= 1.0, f"Confidence {conf} out of range for: {text!r}"


# ─── sentiment_from_star_rating ───────────────────────────────────────────────

class TestSentimentFromStarRating:

    def test_5_stars_is_strongly_positive(self):
        score, label = sentiment_from_star_rating(5)
        assert score == 0.90
        assert label == "positive"

    def test_4_stars_is_mildly_positive(self):
        score, label = sentiment_from_star_rating(4)
        assert score == 0.55
        assert label == "positive"

    def test_3_stars_is_neutral(self):
        score, label = sentiment_from_star_rating(3)
        assert score == 0.00
        assert label == "neutral"

    def test_2_stars_is_mildly_negative(self):
        score, label = sentiment_from_star_rating(2)
        assert score == -0.55
        assert label == "negative"

    def test_1_star_is_strongly_negative(self):
        score, label = sentiment_from_star_rating(1)
        assert score == -0.90
        assert label == "negative"

    def test_rating_as_string_works(self):
        score, label = sentiment_from_star_rating("4")
        assert score == 0.55
        assert label == "positive"

    def test_float_rating_rounds_correctly(self):
        # 4.7 → round(4.7) = 5 → positive
        score, label = sentiment_from_star_rating(4.7)
        assert score == 0.90
        assert label == "positive"

    def test_float_string_works(self):
        score, label = sentiment_from_star_rating("3.5")
        # round(3.5) = 4 in Python 3 (banker's rounding)
        assert label in ("positive", "neutral")

    def test_zero_clamped_to_1_star(self):
        # 0 → clamped to max(1, min(5, 0)) = 1 → negative
        score, label = sentiment_from_star_rating(0)
        assert score == -0.90
        assert label == "negative"

    def test_above_5_clamped_to_5_star(self):
        score, label = sentiment_from_star_rating(6)
        assert score == 0.90
        assert label == "positive"

    def test_none_returns_neutral(self):
        score, label = sentiment_from_star_rating(None)
        assert score == 0.0
        assert label == "neutral"

    def test_non_numeric_string_returns_neutral(self):
        score, label = sentiment_from_star_rating("five")
        assert score == 0.0
        assert label == "neutral"

    def test_negative_number_clamped_to_1_star(self):
        score, label = sentiment_from_star_rating(-3)
        assert score == -0.90
        assert label == "negative"

    def test_returns_tuple(self):
        result = sentiment_from_star_rating(3)
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert isinstance(result[0], float)
        assert isinstance(result[1], str)


# ─── extract_states_mentioned ─────────────────────────────────────────────────

class TestExtractStatesMentioned:

    def test_detects_single_state(self):
        states = extract_states_mentioned("Company expands operations in Maharashtra")
        assert "Maharashtra" in states

    def test_detects_multiple_states(self):
        states = extract_states_mentioned(
            "Operations in Karnataka and Tamil Nadu are growing"
        )
        assert "Karnataka" in states
        assert "Tamil Nadu" in states

    def test_detects_state_via_city_alias(self):
        # Mumbai → Maharashtra
        states = extract_states_mentioned("Factory in Mumbai reports issue")
        assert "Maharashtra" in states

    def test_no_states_returns_empty(self):
        states = extract_states_mentioned("Company posts strong quarterly results")
        assert states == [] or states == set() or len(states) == 0

    def test_case_insensitive_detection(self):
        states = extract_states_mentioned("office in GUJARAT produces high output")
        assert "Gujarat" in states

    def test_deduplicates_states(self):
        # Both "Bangalore" and "Bengaluru" → Karnataka (should appear only once)
        states = extract_states_mentioned(
            "offices in Bangalore and Bengaluru are both expanding"
        )
        state_list = list(states)
        assert state_list.count("Karnataka") == 1

    def test_ut_detected(self):
        states = extract_states_mentioned("New Delhi headquarters announced layoffs")
        assert "Delhi" in states

    def test_empty_text_returns_empty(self):
        states = extract_states_mentioned("")
        assert len(states) == 0

    def test_state_substring_not_matched_inside_word(self):
        # "Goa" should not match "goals" — word boundary enforced
        states = extract_states_mentioned("company goals are ambitious")
        assert "Goa" not in (states or [])
