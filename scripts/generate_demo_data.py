from __future__ import annotations

import argparse
import json
import math
import random
from pathlib import Path
from typing import Final, Literal, TypedDict, cast


ROOT: Final = Path(__file__).resolve().parents[1]
DEFAULT_SEED: Final = 42
DEFAULT_RESTAURANT_COUNT: Final = 24
GENERATOR_VERSION: Final = "2.0.0"
SCHEMA_VERSION: Final = "2.0.0"
DEFAULT_SOURCE_PATH: Final = (
    ROOT / "data" / "raw" / "chicago_food_inspections.json"
)
DEFAULT_OUTPUT_PATH: Final = ROOT / "data" / "synthetic" / "restaurants.json"

DAYS: Final = (
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
)


class NeighborhoodConfig(TypedDict):
    latitude: float
    longitude: float
    zip_code: str


NEIGHBORHOODS: Final[dict[str, NeighborhoodConfig]] = {
    "Illinois Tech": {"latitude": 41.8349, "longitude": -87.6270, "zip_code": "60616"},
    "Chinatown": {"latitude": 41.8520, "longitude": -87.6321, "zip_code": "60616"},
    "Chicago Loop": {"latitude": 41.8781, "longitude": -87.6298, "zip_code": "60601"},
    "Hyde Park": {"latitude": 41.7943, "longitude": -87.5907, "zip_code": "60615"},
    "Bridgeport": {"latitude": 41.8381, "longitude": -87.6512, "zip_code": "60608"},
    "Lakeview": {"latitude": 41.9439, "longitude": -87.6493, "zip_code": "60657"},
    "River North": {"latitude": 41.8924, "longitude": -87.6341, "zip_code": "60654"},
}

CUISINES: Final = (
    "American", "Chinese", "Ethiopian", "Indian", "Italian", "Japanese",
    "Korean", "Mediterranean", "Mexican", "Thai",
)

PRICE_RANGES: Final[dict[str, tuple[int, int]]] = {
    "$": (10, 18),
    "$$": (19, 35),
    "$$$": (36, 60),
}


class OpeningPeriod(TypedDict):
    open: str
    close: str


class TravelEstimate(TypedDict):
    straight_line_distance_km: float
    walking_minutes: int
    public_transit_minutes: int
    driving_minutes: int
    estimate_type: Literal["synthetic"]


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


class SourceRestaurant(TypedDict):
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


class SourceMetadata(TypedDict):
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


class SourceDataset(TypedDict):
    metadata: SourceMetadata
    restaurants: list[SourceRestaurant]


class Restaurant(TypedDict):
    restaurant_id: str
    license_number: str
    name: str
    address: str
    city: str
    state: str
    zip_code: str
    neighborhood: str
    latitude: float
    longitude: float
    cuisine: str
    price_category: str
    estimated_cost_per_person: int
    vegetarian_available: bool
    vegan_available: bool
    rating: float
    review_count: int
    opening_hours: dict[str, OpeningPeriod | None]
    estimated_transportation: dict[str, TravelEstimate]
    latest_inspection: LatestInspection
    inspection_history: InspectionHistory
    identity_provenance: Literal["city_of_chicago_food_inspections"]
    profile_provenance: Literal["synthetic_enrichment"]
    data_provenance: Literal["hybrid"]


class DatasetMetadata(TypedDict):
    dataset_name: str
    description: str
    city: str
    hybrid: Literal[True]
    synthetic: Literal[False]
    seed: int
    record_count: int
    generator_version: str
    schema_version: str
    identity_source: str
    identity_source_url: str
    identity_snapshot_date: str
    synthetic_fields: list[str]
    source_disclaimer: str


class Dataset(TypedDict):
    metadata: DatasetMetadata
    restaurants: list[Restaurant]


def _balanced_values(values: tuple[str, ...], count: int, rng: random.Random) -> list[str]:
    assignments = [values[index % len(values)] for index in range(count)]
    rng.shuffle(assignments)
    return assignments


def _opening_hours(rng: random.Random) -> dict[str, OpeningPeriod | None]:
    opening_hour = rng.choice((10, 11, 12))
    closing_hour = rng.choice((20, 21, 22, 23))
    closed_day = rng.choice((*DAYS, None, None, None, None))
    return {
        day: None if day == closed_day else {
            "open": f"{opening_hour:02d}:00",
            "close": f"{closing_hour:02d}:00",
        }
        for day in DAYS
    }


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
    haversine_value = (
        math.sin(latitude_delta / 2) ** 2
        + math.cos(latitude_a_radians)
        * math.cos(latitude_b_radians)
        * math.sin(longitude_delta / 2) ** 2
    )
    return earth_radius_km * 2 * math.atan2(
        math.sqrt(haversine_value), math.sqrt(1 - haversine_value)
    )


def _transportation_estimates(
    latitude: float,
    longitude: float,
    rng: random.Random,
) -> dict[str, TravelEstimate]:
    estimates: dict[str, TravelEstimate] = {}
    for origin, location in NEIGHBORHOODS.items():
        distance_km = _haversine_distance_km(
            location["latitude"], location["longitude"], latitude, longitude
        )
        estimates[origin] = {
            "straight_line_distance_km": round(distance_km, 2),
            "walking_minutes": max(3, round((distance_km / 4.8) * 60 + rng.uniform(1, 4))),
            "public_transit_minutes": max(
                8, round(7 + (distance_km / 22) * 60 + rng.uniform(0, 7))
            ),
            "driving_minutes": max(
                5, round(4 + (distance_km / 28) * 60 + rng.uniform(0, 6))
            ),
            "estimate_type": "synthetic",
        }
    return estimates


def _load_source(source_path: Path) -> SourceDataset:
    if not source_path.exists():
        raise FileNotFoundError(
            f"Real-data snapshot not found at {source_path}. Run "
            "scripts/ingest_chicago_food_inspections.py first."
        )
    return cast(SourceDataset, json.loads(source_path.read_text(encoding="utf-8")))


def generate_dataset(
    count: int = DEFAULT_RESTAURANT_COUNT,
    seed: int = DEFAULT_SEED,
    source_path: Path = DEFAULT_SOURCE_PATH,
) -> Dataset:
    """Combine real City identities with reproducible synthetic enrichment."""

    if count <= 0:
        raise ValueError("Restaurant count must be greater than zero.")
    source = _load_source(source_path)
    source_restaurants = source["restaurants"]
    if count > len(source_restaurants):
        raise ValueError(
            f"Requested {count} records, but the source contains {len(source_restaurants)}."
        )

    rng = random.Random(seed)
    cuisine_assignments = _balanced_values(CUISINES, count, rng)
    price_assignments = _balanced_values(tuple(PRICE_RANGES), count, rng)
    restaurants: list[Restaurant] = []
    for index, source_restaurant in enumerate(source_restaurants[:count], start=1):
        cuisine = cuisine_assignments[index - 1]
        price_category = price_assignments[index - 1]
        minimum_cost, maximum_cost = PRICE_RANGES[price_category]
        vegetarian_available = index % 5 != 0
        vegan_available = vegetarian_available and index % 3 == 0
        latitude = source_restaurant["latitude"]
        longitude = source_restaurant["longitude"]
        restaurants.append(
            {
                "restaurant_id": source_restaurant["restaurant_id"],
                "license_number": source_restaurant["license_number"],
                "name": source_restaurant["name"],
                "address": source_restaurant["address"],
                "city": source_restaurant["city"],
                "state": source_restaurant["state"],
                "zip_code": source_restaurant["zip_code"],
                "neighborhood": source_restaurant["neighborhood"],
                "latitude": latitude,
                "longitude": longitude,
                "cuisine": cuisine,
                "price_category": price_category,
                "estimated_cost_per_person": rng.randint(minimum_cost, maximum_cost),
                "vegetarian_available": vegetarian_available,
                "vegan_available": vegan_available,
                "rating": round(rng.uniform(3.2, 4.9), 1),
                "review_count": rng.randint(12, 1_200),
                "opening_hours": _opening_hours(rng),
                "estimated_transportation": _transportation_estimates(
                    latitude, longitude, rng
                ),
                "latest_inspection": source_restaurant["latest_inspection"],
                "inspection_history": source_restaurant["inspection_history"],
                "identity_provenance": "city_of_chicago_food_inspections",
                "profile_provenance": "synthetic_enrichment",
                "data_provenance": "hybrid",
            }
        )

    metadata = source["metadata"]
    return {
        "metadata": {
            "dataset_name": "BiteCheck Hybrid Chicago Restaurants",
            "description": (
                "Real City of Chicago establishment and inspection records combined "
                "with reproducible synthetic recommendation fields."
            ),
            "city": "Chicago",
            "hybrid": True,
            "synthetic": False,
            "seed": seed,
            "record_count": count,
            "generator_version": GENERATOR_VERSION,
            "schema_version": SCHEMA_VERSION,
            "identity_source": f"{metadata['attribution']} {metadata['dataset_name']}",
            "identity_source_url": metadata["source_url"],
            "identity_snapshot_date": metadata["snapshot_date"],
            "synthetic_fields": [
                "cuisine", "price_category", "estimated_cost_per_person",
                "vegetarian_available", "vegan_available", "rating", "review_count",
                "opening_hours", "estimated_transportation",
            ],
            "source_disclaimer": metadata["disclaimer"],
        },
        "restaurants": restaurants,
    }


def write_dataset(
    output_path: Path = DEFAULT_OUTPUT_PATH,
    count: int = DEFAULT_RESTAURANT_COUNT,
    seed: int = DEFAULT_SEED,
    source_path: Path = DEFAULT_SOURCE_PATH,
) -> Path:
    dataset = generate_dataset(count=count, seed=seed, source_path=source_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(dataset, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return output_path.resolve()


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build BiteCheck's hybrid Chicago restaurant data."
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE_PATH)
    parser.add_argument("--count", type=int, default=DEFAULT_RESTAURANT_COUNT)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    output_path = write_dataset(
        output_path=args.output,
        count=args.count,
        seed=args.seed,
        source_path=args.source,
    )
    print(f"Generated {args.count} hybrid restaurant records at {output_path}")


if __name__ == "__main__":
    main()
