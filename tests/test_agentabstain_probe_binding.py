from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "experiments" / "agentabstain" / "probe_binding.py"

spec = importlib.util.spec_from_file_location("agentabstain_probe_binding", MODULE)
assert spec and spec.loader
binding = importlib.util.module_from_spec(spec)
spec.loader.exec_module(binding)


def test_regex_binding_records_provenance() -> None:
    tool = {
        "name": "bank.verify",
        "input_schema": {
            "type": "object",
            "properties": {
                "account_number": {"type": "string"},
                "routing_number": {"type": "string"},
            },
        },
    }
    profile = {
        "profile_id": "bank-account-link/v1",
        "tool": "bank.verify",
        "required_fields": ["account_number", "routing_number"],
        "extractors": {
            "account_number": {
                "kind": "regex",
                "pattern": r"account\s+(?P<value>\d{10})",
            },
            "routing_number": {
                "kind": "regex",
                "pattern": r"routing\s+(?P<value>\d{9})",
            },
        },
    }

    result = binding.bind(
        instruction="Send to account 5540119283, routing 021000089.",
        tool=tool,
        profile=profile,
    )

    assert result["binding_complete"] is True
    assert result["arguments"] == {
        "account_number": "5540119283",
        "routing_number": "021000089",
    }
    assert result["unbound_fields"] == []
    assert result["provenance"]["account_number"]["text"] == "5540119283"


def test_missing_semantic_field_stays_incomplete() -> None:
    tool = {
        "name": "weather.verify",
        "input_schema": {
            "type": "object",
            "properties": {
                "location": {"type": "string"},
                "date": {"type": "string"},
            },
        },
    }
    profile = {
        "profile_id": "weather-alert/v1",
        "tool": "weather.verify",
        "required_fields": ["location", "date"],
        "extractors": {
            "location": {
                "kind": "regex",
                "pattern": r"for\s+(?P<value>Asheville)",
            },
            "date": {
                "kind": "regex",
                "pattern": r"(?P<value>\d{4}-\d{2}-\d{2})",
            },
        },
    }

    result = binding.bind(
        instruction="Check the alert for Asheville on Saturday.",
        tool=tool,
        profile=profile,
    )

    assert result["binding_complete"] is False
    assert result["arguments"] == {"location": "Asheville"}
    assert result["unbound_fields"] == ["date"]


def test_enum_literal_requires_unique_match() -> None:
    tool = {
        "name": "orders.verify",
        "input_schema": {
            "type": "object",
            "properties": {
                "status": {"type": "string", "enum": ["active", "cancelled"]},
            },
        },
    }
    profile = {
        "profile_id": "order-status/v1",
        "tool": "orders.verify",
        "required_fields": ["status"],
        "extractors": {"status": {"kind": "enum_literal"}},
    }

    result = binding.bind(
        instruction="Confirm the order is active.",
        tool=tool,
        profile=profile,
    )
    assert result["binding_complete"] is True
    assert result["arguments"]["status"] == "active"


def test_profile_cannot_claim_field_missing_from_tool_schema() -> None:
    tool = {
        "name": "calendar.verify",
        "input_schema": {"type": "object", "properties": {"date": {"type": "string"}}},
    }
    profile = {
        "profile_id": "calendar/v1",
        "tool": "calendar.verify",
        "required_fields": ["title"],
        "extractors": {
            "title": {"kind": "regex", "pattern": r"(?P<value>dentist)"}
        },
    }

    with pytest.raises(ValueError, match="absent from tool schema"):
        binding.bind(
            instruction="Check dentist appointment",
            tool=tool,
            profile=profile,
        )
