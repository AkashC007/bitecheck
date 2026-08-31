from __future__ import annotations

import argparse
import json
import math
import os
import re
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Final, TypedDict, cast
from urllib.parse import urlencode
from urllib.request import Request, urlopen


ROOT: Final = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_PATH: Final = (
    ROOT / "data" / "raw" / "chicago_food_inspections.json"
)
DATASET_ID: Final = "4ijn-s7e5"
DATASET_NAME: Final = "Food Inspections"
SOURCE_URL: Final = (
    "https://data.cityofchicago.org/Health-Human-Services/"
    "Food-Inspections/4ijn-s7e5"
)
API_URL: Final = f"https://data.cityofchicago.org/resource/{DATASET_ID}.json"
ATTRIBUTION: Final = "City of Chicago"
HISTORY_START_DATE: Final = "2024-01-01"
SNAPSHOT_DATE: Final = "2026-08-30"
TARGET_COUNT: Final = 24
MAX_DISTANCE_KM: Final = 3.0
PAGE_SIZE: Final = 5_000
ACCEPTED_LATEST_RESULTS: Final = frozenset({"Pass", "Pass w/ Conditions"})


class AreaCenter(TypedDict):
    latitude: float
    longitude: float


AREA_CENTERS: Final[dict[str, AreaCenter]] = {
    "Illinois Tech": {"latitude": 41.8349, "longitude": -87.6270},
    "Chinatown": {"latitude": 41.8520, "longitude": -87.6321},
    "Chicago Loop": {"latitude": 41.8781, "longitude": -87.6298},
    "Hyde Park": {"latitude": 41.7943, "longitude": -87.5907},
    "Bridgeport": {"latitude": 41.8381, "longitude": -87.6512},
    "Lakeview": {"latitude": 41.9439, "longitude": -87.6493},
    "River North": {"latitude": 41.8924, "longitude": -87.6341},
}


class InspectionRow(TypedDict, total=False):
    inspection_id: str
    dba_name: str
    aka_name: str
    license_: str
    facility_type: str
    risk: str
    address: str
    city: str
    state: str
    zip: str
    inspection_date: str
    inspection_type: str
    results: str
    latitude: str
    longitude: str


class LatestInspection(TypedDict):
    inspection_id: str
    inspection_date: str
    result: str
    inspection_type: str
    risk: str


class InspectionHistory(TypedDict):
    start_date: str
    end_date: str
    inspection_count: int
    pass_count: int
    pass_with_conditions_count: int
    fail_count: int


class SnapshotRestaurant(TypedDict):
    restaurant_id: str
    license_number: str
    name: str
    dba_name: str
    address: str
    city: str
    state: str
    zip_code: str
    neighborhood: str
    latitude: float
    longitude: float
    latest_inspection: LatestInspection
    inspection_history: InspectionHistory


class SnapshotMetadata(TypedDict):
    dataset_id: str
    dataset_name: str
    source_url: str
    api_url: str
    attribution: str
    retrieved_on: str
    snapshot_date: str
    history_start_date: str
    source_row_count: int
    selected_record_count: int
    modification_note: str
    disclaimer: str


class Snapshot(TypedDict):
    metadata: SnapshotMetadata
    restaurants: list[SnapshotRestaurant]


@dataclass(frozen=True)
class CleanInspection:
    inspection_id: str
    dba_name: str
    aka_name: str
    license_number: str
    risk: str
    address: str
    city: str
    state: str
    zip_code: str
    inspection_date: str
    inspection_type: str
    result: str
    latitude: float
    longitude: float


def _query_parameters(limit: int, offset: int) -> dict[str, str | int]:
    fields = (
        "inspection_id,dba_name,aka_name,license_,facility_type,risk,address,"
        "city,state,zip,inspection_date,inspection_type,results,latitude,longitude"
    )
    where = (
        "upper(facility_type) like '%RESTAURANT%' "
        "and upper(city)='CHICAGO' "
        "and license_ is not null and latitude is not null and longitude is not null "
        f"and inspection_date between '{HISTORY_START_DATE}T00:00:00.000' "
        f"and '{SNAPSHOT_DATE}T23:59:59.999' "
        "and latitude between 41.75 and 41.98 "
        "and longitude between -87.70 and -87.56"
    )
    return {
        "$select": fields,
        "$where": where,
        "$order": "inspection_date desc,inspection_id desc",
        "$limit": limit,
        "$offset": offset,
    }


def fetch_inspection_rows() -> list[InspectionRow]:
    """Download the bounded source window from Chicago's Socrata API."""

    rows: list[InspectionRow] = []
    app_token = os.getenv("CHICAGO_DATA_APP_TOKEN", "").strip()

    for offset in range(0, 100_000, PAGE_SIZE):
        request = Request(
            f"{API_URL}?{urlencode(_query_parameters(PAGE_SIZE, offset))}",
            headers={"User-Agent": "BiteCheck portfolio data pipeline/2.0"},
        )
        if app_token:
            request.add_header("X-App-Token", app_token)

        with urlopen(request, timeout=60) as response:  # noqa: S310
            page = cast(list[InspectionRow], json.load(response))

        rows.extend(page)
        if len(page) < PAGE_SIZE:
            return rows

    raise RuntimeError("Chicago inspection download exceeded the safety limit.")


def _clean_text(value: str) -> str:
    return " ".join(value.strip().split())


def _display_name(value: str) -> str:
    cleaned = _clean_text(value)
    if not cleaned:
        return cleaned
    if cleaned != cleaned.upper():
        return cleaned
    titled = cleaned.title().replace("'S", "'s")
    titled = re.sub(
        r"\b(\d+)(St|Nd|Rd|Th)\b",
        lambda match: f"{match.group(1)}{match.group(2).lower()}",
        titled,
    )
    return re.sub(r"\bLlc\b", "LLC", titled)


def _parse_row(row: InspectionRow) -> CleanInspection | None:
    required_values = (
        row.get("inspection_id", ""),
        row.get("dba_name", ""),
        row.get("license_", ""),
        row.get("address", ""),
        row.get("inspection_date", ""),
        row.get("results", ""),
        row.get("latitude", ""),
        row.get("longitude", ""),
    )
    if any(not _clean_text(value) for value in required_values):
        return None

    try:
        inspection_date = datetime.fromisoformat(row["inspection_date"]).date()
        latitude = float(row["latitude"])
        longitude = float(row["longitude"])
    except (ValueError, TypeError):
        return None

    if not (
        date.fromisoformat(HISTORY_START_DATE)
        <= inspection_date
        <= date.fromisoformat(SNAPSHOT_DATE)
    ):
        return None

    license_number = re.sub(r"\.0$", "", _clean_text(row["license_"]))
    if not license_number or license_number == "0":
        return None

    return CleanInspection(
        inspection_id=_clean_text(row["inspection_id"]),
        dba_name=_display_name(row["dba_name"]),
        aka_name=_display_name(row.get("aka_name", "")),
        license_number=license_number,
        risk=_clean_text(row.get("risk", "Unknown")) or "Unknown",
        address=_display_name(row["address"]),
        city=_display_name(row.get("city", "Chicago")) or "Chicago",
        state=_clean_text(row.get("state", "IL")).upper() or "IL",
        zip_code=_clean_text(row.get("zip", "")),
        inspection_date=inspection_date.isoformat(),
        inspection_type=_clean_text(row.get("inspection_type", "Unknown"))
        or "Unknown",
        result=_clean_text(row["results"]),
        latitude=latitude,
        longitude=longitude,
    )


def _haversine_distance_km(
    latitude_a: float,
    longitude_a: float,
    latitude_b: float,
    longitude_b: float,
) -> float:
    earth_radius_km = 6_371.0
    latitude_delta = math.radians(latitude_b - latitude_a)
    longitude_delta = math.radians(longitude_b - longitude_a)
    latitude_a_radians = math.radians(latitude_a)
    latitude_b_radians = math.radians(latitude_b)
    value = (
        math.sin(latitude_delta / 2) ** 2
        + math.cos(latitude_a_radians)
        * math.cos(latitude_b_radians)
        * math.sin(longitude_delta / 2) ** 2
    )
    return earth_radius_km * 2 * math.atan2(
        math.sqrt(value), math.sqrt(1 - value)
    )


def _nearest_area(inspection: CleanInspection) -> tuple[str, float]:
    distances = {
        area: _haversine_distance_km(
            inspection.latitude,
            inspection.longitude,
            center["latitude"],
            center["longitude"],
        )
        for area, center in AREA_CENTERS.items()
    }
    return min(distances.items(), key=lambda item: (item[1], item[0]))


def _latest_sort_key(inspection: CleanInspection) -> tuple[str, int]:
    try:
        inspection_id = int(inspection.inspection_id)
    except ValueError:
        inspection_id = 0
    return inspection.inspection_date, inspection_id


def _history(rows: list[CleanInspection]) -> InspectionHistory:
    return {
        "start_date": HISTORY_START_DATE,
        "end_date": SNAPSHOT_DATE,
        "inspection_count": len(rows),
        "pass_count": sum(row.result == "Pass" for row in rows),
        "pass_with_conditions_count": sum(
            row.result == "Pass w/ Conditions" for row in rows
        ),
        "fail_count": sum(row.result == "Fail" for row in rows),
    }


def _normalized_identity(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.casefold())


def build_snapshot(
    source_rows: list[InspectionRow],
    *,
    retrieved_on: str = SNAPSHOT_DATE,
    target_count: int = TARGET_COUNT,
) -> Snapshot:
    """Clean, deduplicate, geographically balance, and document source rows."""

    if target_count <= 0:
        raise ValueError("Target count must be greater than zero.")

    by_license: defaultdict[str, list[CleanInspection]] = defaultdict(list)
    seen_inspections: set[tuple[str, str]] = set()
    for row in source_rows:
        parsed = _parse_row(row)
        if parsed is None:
            continue
        inspection_key = (parsed.license_number, parsed.inspection_id)
        if inspection_key in seen_inspections:
            continue
        seen_inspections.add(inspection_key)
        by_license[parsed.license_number].append(parsed)

    buckets: defaultdict[
        str, list[tuple[CleanInspection, list[CleanInspection], float]]
    ] = defaultdict(list)
    for history_rows in by_license.values():
        latest = max(history_rows, key=_latest_sort_key)
        area, distance = _nearest_area(latest)
        if (
            distance <= MAX_DISTANCE_KM
            and latest.result in ACCEPTED_LATEST_RESULTS
        ):
            buckets[area].append((latest, history_rows, distance))

    for area_rows in buckets.values():
        area_rows.sort(
            key=lambda item: (
                round(item[2], 6),
                item[0].dba_name.casefold(),
                item[0].license_number,
            )
        )

    base_quota, extra = divmod(target_count, len(AREA_CENTERS))
    quotas = {
        area: base_quota + (index < extra)
        for index, area in enumerate(AREA_CENTERS)
    }
    selected: list[tuple[str, CleanInspection, list[CleanInspection]]] = []
    used_names: set[str] = set()
    used_addresses: set[str] = set()

    for area in AREA_CENTERS:
        for latest, history_rows, _distance in buckets[area]:
            name_key = _normalized_identity(latest.aka_name or latest.dba_name)
            address_key = _normalized_identity(latest.address)
            if name_key in used_names or address_key in used_addresses:
                continue
            selected.append((area, latest, history_rows))
            used_names.add(name_key)
            used_addresses.add(address_key)
            if sum(item[0] == area for item in selected) == quotas[area]:
                break

    if len(selected) != target_count:
        counts = {
            area: sum(item[0] == area for item in selected)
            for area in AREA_CENTERS
        }
        raise ValueError(
            f"Could only select {len(selected)} of {target_count} records: {counts}"
        )

    restaurants: list[SnapshotRestaurant] = []
    for area, latest, history_rows in selected:
        full_address = f"{latest.address}, {latest.city}, {latest.state}"
        if latest.zip_code:
            full_address = f"{full_address} {latest.zip_code}"
        restaurants.append(
            {
                "restaurant_id": f"CHI-COC-{latest.license_number}",
                "license_number": latest.license_number,
                "name": latest.aka_name or latest.dba_name,
                "dba_name": latest.dba_name,
                "address": full_address,
                "city": latest.city,
                "state": latest.state,
                "zip_code": latest.zip_code,
                "neighborhood": area,
                "latitude": latest.latitude,
                "longitude": latest.longitude,
                "latest_inspection": {
                    "inspection_id": latest.inspection_id,
                    "inspection_date": latest.inspection_date,
                    "result": latest.result,
                    "inspection_type": latest.inspection_type,
                    "risk": latest.risk,
                },
                "inspection_history": _history(history_rows),
            }
        )

    return {
        "metadata": {
            "dataset_id": DATASET_ID,
            "dataset_name": DATASET_NAME,
            "source_url": SOURCE_URL,
            "api_url": API_URL,
            "attribution": ATTRIBUTION,
            "retrieved_on": retrieved_on,
            "snapshot_date": SNAPSHOT_DATE,
            "history_start_date": HISTORY_START_DATE,
            "source_row_count": len(source_rows),
            "selected_record_count": len(restaurants),
            "modification_note": (
                "Filtered to restaurant-type Chicago facilities near seven demo "
                "areas; removed duplicate inspection IDs; deduplicated establishments "
                "by license; kept records whose latest inspection in the source window "
                "was Pass or Pass w/ Conditions."
            ),
            "disclaimer": (
                "Inspection results describe conditions observed at inspection time. "
                "This fixed snapshot does not guarantee current operation or safety."
            ),
        },
        "restaurants": restaurants,
    }


def write_snapshot(
    output_path: Path = DEFAULT_OUTPUT_PATH,
    *,
    retrieved_on: str = SNAPSHOT_DATE,
) -> Path:
    source_rows = fetch_inspection_rows()
    snapshot = build_snapshot(source_rows, retrieved_on=retrieved_on)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(snapshot, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return output_path.resolve()


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build BiteCheck's City of Chicago restaurant snapshot."
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument(
        "--retrieved-on",
        default=SNAPSHOT_DATE,
        help="ISO date recorded in snapshot metadata.",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    output_path = write_snapshot(
        output_path=args.output,
        retrieved_on=args.retrieved_on,
    )
    print(f"Wrote {TARGET_COUNT} real establishment records to {output_path}")


if __name__ == "__main__":
    main()
