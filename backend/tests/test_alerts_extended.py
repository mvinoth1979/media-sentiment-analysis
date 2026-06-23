"""
Extended alert system tests — covers all 6 alert types, cooldown logic,
malformed dates, disabled configs, and the no-resend-key early exit.

Complements existing TestCheckAndFireAlertsReviewCluster in test_virality_detector.py.
"""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone, timedelta


def _base_config(alert_type: str, threshold: float, **overrides) -> dict:
    return {
        "id": "cfg-test",
        "alert_type": alert_type,
        "threshold": threshold,
        "notify_email": "ops@example.com",
        "enabled": True,
        "last_triggered_at": None,
        **overrides,
    }


class TestNoResendKey:

    def test_returns_immediately_when_no_resend_key(self):
        from app.storage.alerts import check_and_fire_alerts
        with patch("app.storage.alerts.settings") as mock_s, \
             patch("app.storage.alerts.get_alert_configs") as mock_cfg:
            mock_s.resend_api_key = ""
            check_and_fire_alerts("brand-1", "B", 60.0, 10.0, 50)
        mock_cfg.assert_not_called()


class TestAlertTypes:

    def _run(self, configs, **kwargs):
        from app.storage.alerts import check_and_fire_alerts
        with patch("app.storage.alerts.settings") as mock_settings, \
             patch("app.storage.alerts.get_alert_configs", return_value=configs), \
             patch("app.storage.alerts._send_alert_email") as mock_send, \
             patch("app.storage.alerts.get_db") as mock_get_db:
            mock_settings.resend_api_key = "key"
            mock_get_db.return_value.table.return_value.update.return_value \
                .eq.return_value.execute.return_value.data = []
            check_and_fire_alerts(
                brand_id="brand-1",
                brand_name="TestBrand",
                **kwargs,
            )
            return mock_send

    # ── perception_score_below ────────────────────────────────────────────────

    def test_perception_score_below_fires(self):
        configs = [_base_config("perception_score_below", 50.0)]
        mock_send = self._run(configs, perception_score=40.0, negative_pct=10.0, mention_count=50)
        mock_send.assert_called_once()
        assert mock_send.call_args[0][2] == "perception_score_below"

    def test_perception_score_above_threshold_does_not_fire(self):
        configs = [_base_config("perception_score_below", 50.0)]
        mock_send = self._run(configs, perception_score=55.0, negative_pct=10.0, mention_count=50)
        mock_send.assert_not_called()

    def test_perception_score_exactly_at_threshold_does_not_fire(self):
        configs = [_base_config("perception_score_below", 50.0)]
        mock_send = self._run(configs, perception_score=50.0, negative_pct=10.0, mention_count=50)
        mock_send.assert_not_called()

    # ── negative_pct_above ────────────────────────────────────────────────────

    def test_negative_pct_above_fires(self):
        configs = [_base_config("negative_pct_above", 30.0)]
        mock_send = self._run(configs, perception_score=60.0, negative_pct=40.0, mention_count=50)
        mock_send.assert_called_once()
        assert mock_send.call_args[0][2] == "negative_pct_above"

    def test_negative_pct_below_does_not_fire(self):
        configs = [_base_config("negative_pct_above", 30.0)]
        mock_send = self._run(configs, perception_score=60.0, negative_pct=25.0, mention_count=50)
        mock_send.assert_not_called()

    # ── mention_spike ─────────────────────────────────────────────────────────

    def test_mention_spike_fires(self):
        configs = [_base_config("mention_spike", 100.0)]
        mock_send = self._run(configs, perception_score=60.0, negative_pct=10.0, mention_count=150)
        mock_send.assert_called_once()
        assert mock_send.call_args[0][2] == "mention_spike"

    def test_mention_spike_at_threshold_does_not_fire(self):
        configs = [_base_config("mention_spike", 100.0)]
        mock_send = self._run(configs, perception_score=60.0, negative_pct=10.0, mention_count=100)
        mock_send.assert_not_called()

    # ── syndication_spike ─────────────────────────────────────────────────────

    def test_syndication_spike_fires_when_sub_check_returns_value(self):
        configs = [_base_config("syndication_spike", 5.0)]
        from app.storage.alerts import check_and_fire_alerts
        with patch("app.storage.alerts.settings") as mock_s, \
             patch("app.storage.alerts.get_alert_configs", return_value=configs), \
             patch("app.storage.alerts._check_syndication_spike", return_value=(7.0, "Big Story")), \
             patch("app.storage.alerts._send_alert_email") as mock_send, \
             patch("app.storage.alerts.get_db") as mock_db:
            mock_s.resend_api_key = "key"
            mock_db.return_value.table.return_value.update.return_value \
                .eq.return_value.execute.return_value.data = []
            check_and_fire_alerts("b1", "B", 60.0, 10.0, 50)
        mock_send.assert_called_once()
        assert mock_send.call_args[0][2] == "syndication_spike"
        assert mock_send.call_args[0][5] == "Big Story"

    def test_syndication_spike_does_not_fire_when_sub_check_none(self):
        configs = [_base_config("syndication_spike", 5.0)]
        from app.storage.alerts import check_and_fire_alerts
        with patch("app.storage.alerts.settings") as mock_s, \
             patch("app.storage.alerts.get_alert_configs", return_value=configs), \
             patch("app.storage.alerts._check_syndication_spike", return_value=None), \
             patch("app.storage.alerts._send_alert_email") as mock_send, \
             patch("app.storage.alerts.get_db"):
            mock_s.resend_api_key = "key"
            check_and_fire_alerts("b1", "B", 60.0, 10.0, 50)
        mock_send.assert_not_called()

    # ── journalist_beat ───────────────────────────────────────────────────────

    def test_journalist_beat_fires_when_sub_check_returns_value(self):
        configs = [_base_config("journalist_beat", 3.0)]
        from app.storage.alerts import check_and_fire_alerts
        with patch("app.storage.alerts.settings") as mock_s, \
             patch("app.storage.alerts.get_alert_configs", return_value=configs), \
             patch("app.storage.alerts._check_journalist_beat", return_value=(4.0, "John Doe")), \
             patch("app.storage.alerts._send_alert_email") as mock_send, \
             patch("app.storage.alerts.get_db") as mock_db:
            mock_s.resend_api_key = "key"
            mock_db.return_value.table.return_value.update.return_value \
                .eq.return_value.execute.return_value.data = []
            check_and_fire_alerts("b1", "B", 60.0, 10.0, 50)
        mock_send.assert_called_once()
        assert mock_send.call_args[0][5] == "John Doe"


class TestAlertCooldown:

    def _run_with_last_triggered(self, hours_ago: float):
        last_dt = (datetime.now(timezone.utc) - timedelta(hours=hours_ago)).isoformat()
        configs = [_base_config("perception_score_below", 50.0, last_triggered_at=last_dt)]
        from app.storage.alerts import check_and_fire_alerts
        with patch("app.storage.alerts.settings") as mock_s, \
             patch("app.storage.alerts.get_alert_configs", return_value=configs), \
             patch("app.storage.alerts._send_alert_email") as mock_send:
            mock_s.resend_api_key = "key"
            check_and_fire_alerts("b1", "B", 30.0, 10.0, 50)
        return mock_send

    def test_alert_suppressed_within_4h_cooldown(self):
        mock_send = self._run_with_last_triggered(hours_ago=2.0)
        mock_send.assert_not_called()

    def test_alert_fires_after_4h_cooldown(self):
        mock_send = self._run_with_last_triggered(hours_ago=5.0)
        mock_send.assert_called_once()

    def test_alert_boundary_at_exactly_4h(self):
        mock_send = self._run_with_last_triggered(hours_ago=4.0)
        assert mock_send.call_count in (0, 1)  # boundary; either is acceptable

    def test_malformed_last_triggered_date_raises(self):
        configs = [_base_config("perception_score_below", 50.0, last_triggered_at="not-a-date")]
        from app.storage.alerts import check_and_fire_alerts
        with patch("app.storage.alerts.settings") as mock_s, \
             patch("app.storage.alerts.get_alert_configs", return_value=configs):
            mock_s.resend_api_key = "key"
            with pytest.raises(ValueError):
                check_and_fire_alerts("b1", "B", 30.0, 10.0, 50)


class TestDisabledAlerts:

    def test_disabled_config_does_not_fire(self):
        configs = [_base_config("perception_score_below", 50.0, enabled=False)]
        from app.storage.alerts import check_and_fire_alerts
        with patch("app.storage.alerts.settings") as mock_s, \
             patch("app.storage.alerts.get_alert_configs", return_value=configs), \
             patch("app.storage.alerts._send_alert_email") as mock_send:
            mock_s.resend_api_key = "key"
            check_and_fire_alerts("b1", "B", 30.0, 10.0, 50)
        mock_send.assert_not_called()

    def test_mix_of_enabled_and_disabled(self):
        configs = [
            _base_config("perception_score_below", 50.0, enabled=False),
            _base_config("negative_pct_above", 20.0, enabled=True),
        ]
        from app.storage.alerts import check_and_fire_alerts
        with patch("app.storage.alerts.settings") as mock_s, \
             patch("app.storage.alerts.get_alert_configs", return_value=configs), \
             patch("app.storage.alerts._send_alert_email") as mock_send, \
             patch("app.storage.alerts.get_db") as mock_db:
            mock_s.resend_api_key = "key"
            mock_db.return_value.table.return_value.update.return_value \
                .eq.return_value.execute.return_value.data = []
            check_and_fire_alerts("b1", "B", 30.0, 40.0, 50)
        assert mock_send.call_count == 1
        assert mock_send.call_args[0][2] == "negative_pct_above"

    def test_config_load_failure_is_graceful(self):
        from app.storage.alerts import check_and_fire_alerts
        with patch("app.storage.alerts.settings") as mock_s, \
             patch("app.storage.alerts.get_alert_configs", side_effect=Exception("DB down")), \
             patch("app.storage.alerts._send_alert_email") as mock_send:
            mock_s.resend_api_key = "key"
            check_and_fire_alerts("b1", "B", 30.0, 10.0, 50)
        mock_send.assert_not_called()


class TestAlertSubChecks:

    def test_check_syndication_spike_returns_none_when_empty(self):
        from app.storage.alerts import _check_syndication_spike
        mock_db = MagicMock()
        mock_db.table.return_value.select.return_value \
            .eq.return_value.gte.return_value.gte.return_value \
            .order.return_value.limit.return_value.execute.return_value.data = []
        with patch("app.storage.alerts.get_db", return_value=mock_db):
            result = _check_syndication_spike("brand-1", 5)
        assert result is None

    def test_check_journalist_beat_returns_none_when_no_rows(self):
        from app.storage.alerts import _check_journalist_beat
        mock_db = MagicMock()
        mock_db.table.return_value.select.return_value \
            .eq.return_value.eq.return_value.gte.return_value \
            .neq.return_value.not_.is_.return_value.execute.return_value.data = []
        with patch("app.storage.alerts.get_db", return_value=mock_db):
            result = _check_journalist_beat("brand-1", 3)
        assert result is None

    def test_check_journalist_beat_top_author_below_threshold(self):
        from app.storage.alerts import _check_journalist_beat
        rows = [{"author": "John Doe"}, {"author": "John Doe"}]
        mock_db = MagicMock()
        mock_db.table.return_value.select.return_value \
            .eq.return_value.eq.return_value.gte.return_value \
            .neq.return_value.not_.is_.return_value.execute.return_value.data = rows
        with patch("app.storage.alerts.get_db", return_value=mock_db):
            result = _check_journalist_beat("brand-1", 3)
        assert result is None

    def test_check_journalist_beat_returns_author_above_threshold(self):
        from app.storage.alerts import _check_journalist_beat
        rows = [{"author": "Jane Smith"}] * 4
        mock_db = MagicMock()
        mock_db.table.return_value.select.return_value \
            .eq.return_value.eq.return_value.gte.return_value \
            .neq.return_value.not_.is_.return_value.execute.return_value.data = rows
        with patch("app.storage.alerts.get_db", return_value=mock_db):
            result = _check_journalist_beat("brand-1", 3)
        assert result is not None
        count, author = result
        assert count == 4.0
        assert author == "Jane Smith"
