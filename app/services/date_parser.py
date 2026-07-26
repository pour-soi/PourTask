from __future__ import annotations

import re
from datetime import date


class DateParseError(ValueError):
    pass


def _year(value: str) -> int:
    year = int(value)
    return year + 2000 if len(value) == 2 else year


def _date(year: str, month: str, day: str) -> date:
    try:
        return date(_year(year), int(month), int(day))
    except (TypeError, ValueError) as exc:
        raise DateParseError("invalid date") from exc


def parse_us_date(value: str | None) -> date | None:
    text = (value or "").strip()
    if not text:
        return None

    iso = re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})", text)
    if iso:
        return _date(iso.group(1), iso.group(2), iso.group(3))

    separated = re.fullmatch(r"(\d{1,2})[./-](\d{1,2})[./-](\d{2}|\d{4})", text)
    if separated:
        return _date(separated.group(3), separated.group(1), separated.group(2))

    if text.isdigit() and len(text) == 8:
        return _date(text[4:], text[:2], text[2:4])

    if text.isdigit() and len(text) == 7:
        candidates = ((text[0], text[1:3], text[3:]), (text[:2], text[2], text[3:]))
        for month, day, year in candidates:
            try:
                return _date(year, month, day)
            except DateParseError:
                continue

    raise DateParseError("invalid date")


def format_us_date(value: date | str | None) -> str:
    if value in (None, ""):
        return ""
    parsed = date.fromisoformat(value) if isinstance(value, str) else value
    return parsed.strftime("%m/%d/%Y")


def parse_assigned_month(value: str | None) -> str | None:
    text = (value or "").strip()
    if not text:
        return None

    compact = re.fullmatch(r"(\d{2})(\d{4})", text)
    us = re.fullmatch(r"(\d{1,2})[/-](\d{4})", text)
    iso = re.fullmatch(r"(\d{4})-(\d{2})", text)
    if compact:
        month, year = compact.groups()
    elif us:
        month, year = us.groups()
    elif iso:
        year, month = iso.groups()
    else:
        raise DateParseError("invalid month")

    number = int(month)
    if not 1 <= number <= 12:
        raise DateParseError("invalid month")
    return f"{int(year):04d}-{number:02d}"


def format_assigned_month(value: str | None) -> str:
    parsed = parse_assigned_month(value)
    if parsed is None:
        return ""
    year, month = parsed.split("-")
    return f"{month}/{year}"
