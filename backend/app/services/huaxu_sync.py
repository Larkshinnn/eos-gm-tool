from __future__ import annotations

import csv
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


API_ROOT = "https://api.huaxu.app/servers/ap"


def _fetch_json(path: str) -> dict:
    request = Request(f"{API_ROOT}/{path}", headers={"Accept": "application/json", "User-Agent": "WACMK-PGR-GM-Tool/1.0"})
    try:
        with urlopen(request, timeout=20) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError, UnicodeDecodeError) as error:
        raise RuntimeError(f"Huaxu request failed for {path}: {error}") from error
    if not isinstance(payload, dict) or payload.get("status") != "success" or not isinstance(payload.get("data"), dict):
        raise RuntimeError(f"Huaxu returned an unexpected response for {path}")
    return payload["data"]


def _snapshot_path(server_path: str | Path) -> Path:
    root = Path(server_path)
    candidates = [
        root / "Resources" / "Configs" / "huaxu_activity_snapshot.json",
        root / "PGRLocalSever" / "Resources" / "Configs" / "huaxu_activity_snapshot.json",
        Path(__file__).resolve().parents[4] / "PGRLocalSever" / "Resources" / "Configs" / "huaxu_activity_snapshot.json",
    ]
    for path in candidates:
        if path.parent.is_dir():
            return path
    raise FileNotFoundError("PGRLocalSever Resources/Configs directory was not found")



def _resource_file(server_path: str | Path, relative: str) -> Path:
    root = Path(server_path)
    candidates = [
        root / "Resources" / "table" / "share" / relative,
        root / "PGRLocalSever" / "Resources" / "table" / "share" / relative,
        Path(__file__).resolve().parents[4] / "PGRLocalSever" / "Resources" / "table" / "share" / relative,
    ]
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(f"PGRLocalSever table was not found: {relative}")


def _write_table(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    shutil.copy2(path, path.with_name(f"{path.name}.{stamp}.bak"))
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames, delimiter="\t", lineterminator="\n", extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    temporary.replace(path)


def _sync_local_tables(server_path: str | Path, warzone: dict, ppc: dict) -> dict[str, int]:
    ppc_path = _resource_file(server_path, "fuben/bosssingle/BossSingleStage.tsv")
    with ppc_path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file, delimiter="\t")
        ppc_fields = reader.fieldnames or []
        ppc_rows = list(reader)
    score_by_stage = {
        str(stage.get("id")): str(stage.get("score"))
        for boss in ppc.get("bosses", []) if isinstance(boss, dict)
        for stage in boss.get("stages", []) if isinstance(stage, dict)
        if stage.get("id") is not None and stage.get("score") is not None
    }
    ppc_updates = 0
    for row in ppc_rows:
        score = score_by_stage.get(row.get("StageId", ""))
        if score is not None and row.get("Score") != score:
            row["Score"] = score
            ppc_updates += 1
    if ppc_updates:
        _write_table(ppc_path, ppc_rows, ppc_fields)

    area_path = _resource_file(server_path, "fuben/arena/AreaStage.tsv")
    with area_path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file, delimiter="\t")
        area_fields = reader.fieldnames or []
        area_rows = list(reader)
    zones = {str(zone.get("id")): zone for zone in warzone.get("area", {}).get("zones", []) if isinstance(zone, dict)}
    area_updates = 0
    for row in area_rows:
        zone = zones.get(row.get("Id", ""))
        if zone is None:
            continue
        values = {
            "Name": zone.get("name", ""), "Desc": zone.get("description", ""),
            "BuffName[1]": "", "BuffName[2]": "", "BuffIds[1]": "", "BuffIds[2]": "",
            "BuffDesc[1]": "", "BuffDesc[2]": "",
        }
        for index, buff in enumerate(zone.get("buffs", [])[:2], start=1):
            values[f"BuffName[{index}]"] = buff.get("name", "")
            values[f"BuffIds[{index}]"] = str(buff.get("id", ""))
            values[f"BuffDesc[{index}]"] = buff.get("description", "")
        for field, value in values.items():
            if field in row and row[field] != str(value):
                row[field] = str(value)
                area_updates += 1
    if area_updates:
        _write_table(area_path, area_rows, area_fields)
    return {"ppcStageRows": ppc_updates, "warzoneAreaFields": area_updates}


def sync_huaxu_activity(server_path: str | Path) -> dict:
    warzone_data = _fetch_json("warzone/current/16")
    ppc_data = _fetch_json("ppc/current/4?ranking=false")
    warzone = warzone_data.get("warzone")
    ppc = ppc_data.get("ppc")
    if not isinstance(warzone, dict) or not isinstance(ppc, dict):
        raise RuntimeError("Huaxu response did not include current Warzone and PPC metadata")

    # Rankings are intentionally excluded: this snapshot stores event configuration only.
    snapshot = {
        "source": "Huaxu API",
        "syncedAt": datetime.now(timezone.utc).isoformat(),
        "server": "ap",
        "warzone": {"activity": warzone, "activities": warzone_data.get("activities")},
        "ppc": {"activity": ppc, "activities": ppc_data.get("activities")},
    }
    table_updates = _sync_local_tables(server_path, warzone, ppc)
    snapshot["localTableUpdates"] = table_updates
    path = _snapshot_path(server_path)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)
    return {"warzone": {"activity": warzone.get("activity"), "start": warzone.get("start"), "end": warzone.get("end")},
            "ppc": {"activity": ppc.get("activity"), "start": ppc.get("start"), "end": ppc.get("end"), "bosses": ppc.get("bosses", [])},
            "tableUpdates": table_updates, "snapshot": str(path)}

