# enricher/discovery.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping

from .urls import extract_urls_from_text, filter_external_urls


@dataclass(frozen=True)
class DiscoveryConfig:
    """
    Controlled public discovery configuration.
    - field_priority: which fields to scan first (ordered)
    - max_urls_per_row: max external URLs retained per row
    - exclude_low_value: exclude domains like paypal.me, etc.
    """
    field_priority: tuple[str, ...] = ("bio_links", "bio_text", "description")
    max_urls_per_row: int = 2
    exclude_low_value: bool = True


def discover_external_urls_from_row(
    row: Mapping[str, str],
    cfg: DiscoveryConfig | None = None,
) -> tuple[list[str], str]:
    """
    Discover external URLs from a CSV row, scanning multiple fields in priority order.

    Returns:
      (urls, discovery_source)

    discovery_source:
      - name of the first field that produced at least one retained URL
      - "none" if nothing found
    """
    cfg = cfg or DiscoveryConfig()

    # Collect candidates in priority order; stop as soon as we have enough retained URLs
    for field in cfg.field_priority:
        raw = row.get(field, "") or ""
        candidates = extract_urls_from_text(raw)

        retained = filter_external_urls(
            candidates,
            max_urls=cfg.max_urls_per_row,
            exclude_low_value=cfg.exclude_low_value,
        )

        if retained:
            return retained, field

    return [], "none"


def discover_external_urls_bulk(
    rows: Iterable[Mapping[str, str]],
    cfg: DiscoveryConfig | None = None,
) -> list[tuple[list[str], str]]:
    """
    Bulk helper for testing or batch runs: returns list of (urls, discovery_source) for each row.
    """
    cfg = cfg or DiscoveryConfig()
    out: list[tuple[list[str], str]] = []
    for r in rows:
        out.append(discover_external_urls_from_row(r, cfg))
    return out
