from __future__ import annotations

from functools import lru_cache

from backend.app.services.player.constants import ITEM_TSV_PATH
from backend.app.services.player.utils import normalize_asset_path, normalize_int_text_map, parse_int
from backend.app.utils.tsv_reader import TSVReader


@lru_cache(maxsize=1)
def get_item_name_map() -> dict[int, str]:
    reader = TSVReader(ITEM_TSV_PATH, typed=True)
    return normalize_int_text_map(reader.get_maps("Id", "Name")[0])


@lru_cache(maxsize=1)
def get_item_catalog() -> list[dict[str, object]]:
    reader = TSVReader(ITEM_TSV_PATH, typed=True)
    catalog: list[dict[str, object]] = []
    for row in reader.data:
        item_id = parse_int(row.get("Id"))
        if item_id is None:
            continue
        catalog.append({
            "item_id": item_id,
            "name": str(row.get("Name") or "").strip(),
            "icon_url": normalize_asset_path(row.get("BigIcon") or row.get("Icon")),
            "item_type": parse_int(row.get("ItemType")),
            "quality": parse_int(row.get("Quality")),
        })
    return sorted(catalog, key=lambda item: int(item["item_id"]))
