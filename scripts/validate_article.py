#!/usr/bin/env python3
"""Validate the fixed 嘻哈地质人 WeChat HTML structure."""

from __future__ import annotations

import argparse
import re
import sys
from html.parser import HTMLParser
from pathlib import Path


SECTIONS = ["本期导读：", "主要内容", "研究方法", "主要讨论", "主要结论", "图片详解", "参考文献："]
TEMPLATE_TOKEN = re.compile(r"\{\{[A-Z0-9_]+\}\}")
DOI = re.compile(r"10\.\d{4,9}/[-._;()/:A-Z0-9]+", re.I)


class StrictEnoughHTMLParser(HTMLParser):
    def error(self, message: str) -> None:  # pragma: no cover
        raise ValueError(message)


def validate(path: Path, figure_count: int | None) -> list[str]:
    errors: list[str] = []
    try:
        text = path.read_text(encoding="utf-8")
    except Exception as exc:
        return [f"cannot read UTF-8 HTML: {exc}"]

    missing = [section for section in SECTIONS if section not in text]
    if missing:
        errors.append("missing sections: " + ", ".join(missing))
    else:
        positions = [text.index(section) for section in SECTIONS]
        if positions != sorted(positions):
            errors.append("fixed sections are out of order")

    for number in range(1, 6):
        if f">0{number}<" not in text:
            errors.append(f"missing numbered divider 0{number}")

    if "原创&nbsp;&nbsp;嘻哈地质人" not in text and "原创  嘻哈地质人" not in text:
        errors.append("missing account byline")

    if figure_count is not None:
        for number in range(1, figure_count + 1):
            if f"原论文图{number}" not in text:
                errors.append(f"missing figure placeholder for main Figure {number}")

    if not DOI.search(text):
        errors.append("no DOI found in reference block")

    tokens = sorted(set(TEMPLATE_TOKEN.findall(text)))
    if tokens:
        errors.append("unresolved template tokens: " + ", ".join(tokens))

    try:
        StrictEnoughHTMLParser().feed(text)
    except Exception as exc:
        errors.append(f"HTML parse error: {exc}")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("html", type=Path)
    parser.add_argument("--figures", type=int, default=None, help="expected number of main-text figures")
    args = parser.parse_args()

    errors = validate(args.html, args.figures)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print(f"OK: {args.html}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
