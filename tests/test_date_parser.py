from datetime import date

import pytest

from app.services.date_parser import (
    DateParseError,
    format_assigned_month,
    format_us_date,
    parse_assigned_month,
    parse_us_date,
)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("07232026", date(2026, 7, 23)),
        ("7232026", date(2026, 7, 23)),
        ("07/23/2026", date(2026, 7, 23)),
        ("7/23/2026", date(2026, 7, 23)),
        ("07-23-2026", date(2026, 7, 23)),
        ("7-23-2026", date(2026, 7, 23)),
        ("07.23.2026", date(2026, 7, 23)),
        ("2026-07-23", date(2026, 7, 23)),
        ("08012026", date(2026, 8, 1)),
        ("8012026", date(2026, 8, 1)),
        ("7/23/26", date(2026, 7, 23)),
        ("01022026", date(2026, 1, 2)),
        ("02/29/2024", date(2024, 2, 29)),
        (" 07/23/2026 ", date(2026, 7, 23)),
    ],
)
def test_parse_us_date(value, expected):
    assert parse_us_date(value) == expected


@pytest.mark.parametrize(
    "value",
    ["02/29/2025", "02/30/2026", "13/20/2026", "13322026", "00000000", "abcd", "07", "23/2026"],
)
def test_parse_us_date_rejects_invalid_values(value):
    with pytest.raises(DateParseError):
        parse_us_date(value)


@pytest.mark.parametrize("value", ["", "  ", None])
def test_empty_date_is_unset(value):
    assert parse_us_date(value) is None


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("072026", "2026-07"),
        ("07/2026", "2026-07"),
        ("7/2026", "2026-07"),
        ("07-2026", "2026-07"),
        ("2026-07", "2026-07"),
    ],
)
def test_parse_assigned_month(value, expected):
    assert parse_assigned_month(value) == expected


@pytest.mark.parametrize("value", ["13/2026", "002026", "2026-00", "July", "07"])
def test_parse_assigned_month_rejects_invalid_values(value):
    with pytest.raises(DateParseError):
        parse_assigned_month(value)


def test_format_iso_values_for_us_display():
    assert format_us_date("2026-07-23") == "07/23/2026"
    assert format_assigned_month("2026-07") == "07/2026"
