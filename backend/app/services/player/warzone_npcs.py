from __future__ import annotations

import csv
from functools import lru_cache
from pathlib import Path


# Verified enemy NPC IDs referenced by the local endgame monster tables.
_KNOWN_BOSS_NPCS = {81300: "Roseblade", 81600: "Roland", 81800: "Vassago"}


def _npc_table_path(server_path: str | Path) -> Path:
    root = Path(server_path)
    candidates = [
        root / "Resources" / "table" / "share" / "fight" / "npc" / "Npc.tsv",
        root / "PGRLocalSever" / "Resources" / "table" / "share" / "fight" / "npc" / "Npc.tsv",
        Path(__file__).resolve().parents[5] / "PGRLocalSever" / "Resources" / "table" / "share" / "fight" / "npc" / "Npc.tsv",
    ]
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    raise FileNotFoundError("PGRLocalSever Resources/table/share/fight/npc/Npc.tsv was not found")


def _display_name_path(server_path: str | Path) -> Path | None:
    root = Path(server_path)
    candidates = [
        root / "Resources" / "table" / "share" / "statussyncfight" / "npc" / "Npc.tsv",
        root / "PGRLocalSever" / "Resources" / "table" / "share" / "statussyncfight" / "npc" / "Npc.tsv",
        Path(__file__).resolve().parents[5] / "PGRLocalSever" / "Resources" / "table" / "share" / "statussyncfight" / "npc" / "Npc.tsv",
    ]
    return next((candidate for candidate in candidates if candidate.is_file()), None)


@lru_cache(maxsize=4)
def _read_names(path: str, modified_ns: int) -> dict[int, dict[str, str | bool]]:
    del modified_ns
    with Path(path).open("r", encoding="utf-8-sig", newline="") as file:
        return {
            int(row["Id"]): {
                "name": row.get("Name", ""),
                "boss_name": row.get("ModelId", "").removeprefix("Mb1").split("Md", 1)[0] if row.get("ModelId", "").startswith("Mb1") else "",
                "model_id": row.get("ModelId", ""),
                "is_boss": row.get("BossHp") == "1",
            }
            for row in csv.DictReader(file, delimiter="\t")
            if row.get("Id", "").isdigit()
        }


@lru_cache(maxsize=4)
def _read_npcs(path: str, modified_ns: int) -> tuple[dict[str, int], ...]:
    del modified_ns
    with Path(path).open("r", encoding="utf-8-sig", newline="") as file:
        rows = csv.DictReader(file, delimiter="\t")
        return tuple(
            {
                "npc_id": int(row["Id"]),
                "type": int(row["Type"]),
                "attrib_id": int(row["AttribId"]),
                "promoted_id": int(row["PromotedId"]),
            }
            for row in rows
            if row.get("Id", "").isdigit()
            and row.get("Type", "").isdigit()
            and row.get("AttribId", "").isdigit()
            and row.get("PromotedId", "").isdigit()
        )


def get_warzone_npc_catalog(server_path: str | Path) -> list[dict[str, int | str]]:
    path = _npc_table_path(server_path)
    entries = list(_read_npcs(str(path), path.stat().st_mtime_ns))
    name_path = _display_name_path(server_path)
    names = _read_names(str(name_path), name_path.stat().st_mtime_ns) if name_path else {}
    catalog = []
    for entry in entries:
        detail = names.get(entry["npc_id"], {})
        boss_name = str(detail.get("boss_name", "") or _KNOWN_BOSS_NPCS.get(entry["npc_id"], ""))
        actor_name = str(detail.get("name", ""))
        name = " · ".join(part for part in (boss_name, actor_name) if part)
        is_boss = bool(detail.get("is_boss", False)) or entry["npc_id"] in _KNOWN_BOSS_NPCS
        catalog.append({**entry, "name": name, "boss_name": boss_name, "model_id": str(detail.get("model_id", "")), "is_boss": is_boss})
    return catalog

