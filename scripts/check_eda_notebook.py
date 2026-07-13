"""Outer behaviour check for P4-09 (EDA notebook) — realizes the issue's Gherkin scenario.

Executes ``notebooks/eda.ipynb`` top-to-bottom with no manual intervention (``nbclient``, the same
engine ``jupyter nbconvert --execute`` uses), asserting it completes with no cell errors, then
inspects the *executed* notebook's cells for the four required chart+commentary sections named in
the scenario: product mix, channel distribution, geography distribution, and promotion/discount
impact.

A section counts as satisfied when, within the notebook, a markdown **heading** cell (its first
non-empty line starts with ``#``) whose heading text matches the section's keyword is followed
(before the next matching section heading) by:
- at least one non-empty markdown cell (commentary), and
- at least one code cell producing a chart output (an image ``display_data``/``execute_result``).

Matching is restricted to heading cells (not any prose mentioning the topic in passing, e.g. this
notebook's own intro paragraph) so a section can't be satisfied by accident.

Usage: ``uv run python scripts/check_eda_notebook.py``.
Exit 0 = green, exit 1 = red (reason printed).
"""

from __future__ import annotations

import sys
from pathlib import Path

import nbformat
from nbclient import NotebookClient
from nbclient.exceptions import CellExecutionError

REPO_ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK_PATH = REPO_ROOT / "notebooks" / "eda.ipynb"

REQUIRED_SECTIONS = {
    "product mix": ("product mix",),
    "channel distribution": (
        "channel distribution",
        "customer/channel",
        "online vs. reseller",
        "online vs reseller",
    ),
    "geography distribution": ("geography distribution", "geographic distribution"),
    "promotion/discount impact": ("promotion", "discount impact"),
}


def _heading_line(markdown_text: str) -> str | None:
    """The cell's first non-empty line, if it is a markdown heading (starts with ``#``)."""
    for line in markdown_text.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped if stripped.startswith("#") else None
    return None


def _section_matched(markdown_text: str, keywords: tuple[str, ...]) -> bool:
    heading = _heading_line(markdown_text)
    if heading is None:
        return False
    lowered = heading.lower()
    return any(keyword in lowered for keyword in keywords)


def _cell_has_chart_output(cell: dict) -> bool:
    if cell.get("cell_type") != "code":
        return False
    for output in cell.get("outputs", []):
        if output.get("output_type") == "error":
            return False
        data = output.get("data", {})
        if any(mime.startswith("image/") for mime in data):
            return True
    return False


def _execute_notebook() -> nbformat.NotebookNode:
    nb = nbformat.read(NOTEBOOK_PATH, as_version=4)
    client = NotebookClient(
        nb,
        timeout=600,
        kernel_name="python3",
        resources={"metadata": {"path": str(NOTEBOOK_PATH.parent)}},
    )
    client.execute()
    return nb


def _find_missing_sections(nb: nbformat.NotebookNode) -> list[str]:
    cells = nb["cells"]
    missing: list[str] = []

    for section_name, keywords in REQUIRED_SECTIONS.items():
        header_idx = None
        for i, cell in enumerate(cells):
            if cell.get("cell_type") == "markdown" and _section_matched(
                cell.get("source", ""), keywords
            ):
                header_idx = i
                break
        if header_idx is None:
            missing.append(f"{section_name}: no markdown header/commentary cell found")
            continue

        has_commentary = False
        has_chart = False
        for cell in cells[header_idx:]:
            if cell.get("cell_type") == "markdown":
                # Stop scanning once we hit the *next* different required section header.
                if cell is not cells[header_idx] and any(
                    _section_matched(cell.get("source", ""), kw)
                    for other, kw in REQUIRED_SECTIONS.items()
                    if other != section_name
                ):
                    break
                if cell.get("source", "").strip():
                    has_commentary = True
            if _cell_has_chart_output(cell):
                has_chart = True

        if not has_commentary:
            missing.append(f"{section_name}: no commentary text found")
        if not has_chart:
            missing.append(f"{section_name}: no chart (image output) found")

    return missing


def main() -> int:
    if not NOTEBOOK_PATH.exists():
        print(f"RED: {NOTEBOOK_PATH} does not exist yet.")
        return 1

    try:
        nb = _execute_notebook()
    except CellExecutionError as exc:
        print(f"RED: notebook execution failed: {exc}")
        return 1

    missing = _find_missing_sections(nb)
    if missing:
        print("RED: notebook executed but is missing required chart+commentary sections:")
        for item in missing:
            print(f"  - {item}")
        return 1

    print(
        "GREEN: notebooks/eda.ipynb executed top-to-bottom with no errors and all four required "
        "chart+commentary sections are present (product mix, channel distribution, geography "
        "distribution, promotion/discount impact)."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
