from __future__ import annotations

import argparse
import json
import math
import random
from pathlib import Path
from typing import Final, Literal, TypedDict


DEFAULT_SEED: Final = 42
DEFAULT_RESTAURANT_COUNT: Final = 24
GENERATOR_VERSION: Final = "1.0.0"
SCHEMA_VERSION: Final = "1.0.0"
DEFAULT_OUTPUT_PATH: Final = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "synthetic"
    / "restaurants.json"
)

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
    "Illinois Tech": {
        "latitude": 41.8349,
        "longitude": -87.6270,
        "zip_code": "60616",
    },
    "Chinatown": {
        "latitude": 41.8520,
        "longitude": -87.6321,
        "zip_code": "60616",
    },
    "Chicago Loop": {
        "latitude": 41.8781,
        "longitude": -87.6298,
        "zip_code": "60601",
    },
    "Hyde Park": {
        "latitude": 41.7943,
        "longitude": -87.5907,
        "zip_code": "60615",
    },
    "Bridgeport": {
        "latitude": 41.8381,
        "longitude": -87.6512,
        "zip_code": "60608",
    },
    "Lakeview": {
        "latitude": 41.9439,
        "longitude": -87.6493,
        "zip_code": "60657",
    },
    "River North": {
        "latitude": 41.8924,
        "longitude": -87.6341,
        "zip_code": "60654",
    },
}

CUISINES: Final = (
    "American",
    "Chinese",
    "Ethiopian",
    "Indian",
    "Italian",
    "Japanese",
    "Korean",
    "Mediterranean",
    "Mexican",
    "Thai",
)

PRICE_RANGES: Final[dict[str, tuple[int, int]]] = {
    "$": (10, 18),
    "$$": (19, 35),
    "$$$": (36, 60),
}

NAME_PREFIXES: Final = (
    "Amber",
    "Blue",
    "Bright",
    "Cedar",
    "Golden",
    "Lake",
    "Little",
    "North",
    "Prairie",
    "Red",
    "Silver",
    "Windy",
)

NAME_SUFFIXES: Final = ("Cafe", "House", "Kitchen", "Table")

CUISINE_NOUNS: Final[dict[str, tuple[str, ...]]] = {
    "American": ("Griddle", "Harvest", "Supper"),
    "Chinese": ("Dumpling", "Lantern", "Noodle"),
    "Ethiopian": ("Berbere", "Injera", "Mesob"),
    "Indian": ("Masala", "Saffron", "Tandoor"),
    "Italian": ("Olive", "Pasta", "Trattoria"),
    "Japanese": ("Miso", "Sakura", "Umami"),
    "Korean": ("Banchan", "Seoul", "Sesame"),
    "Mediterranean": ("Cypress", "Olive", "Sumac"),
    "Mexican": ("Agave", "Maiz", "Salsa"),
    "Thai": ("Basil", "Lemongrass", "Orchid"),
}

FICTIONAL_STREETS: Final = (
    "Demo Avenue",
    "Example Street",
    "Sample Road",
    "Test Kitchen Way",
)


class OpeningPeriod(TypedDict):
    open: str
    close: str


class TravelEstimate(TypedDict):
    straight_line_distance_km: float
    walking_minutes: int
    public_transit_minutes: int
    driving_minutes: int
    estimate_type: Literal["synthetic"]


class Restaurant(TypedDict):
    restaurant_id: str
    name: str
    address: str
    city: str
    state: str
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
    data_provenance: Literal["synthetic"]


class DatasetMetadata(TypedDict):
    dataset_name: str
    description: str
    city: str
    synthetic: Literal[True]
    seed: int
    record_count: int
    generator_version: str
    schema_version: str


class Dataset(TypedDict):
    metadata: DatasetMetadata
    restaurants: list[Restaurant]


def _balanced_values(
    values: tuple[str, ...], count: int, rng: random.Random
) -> list[str]:
    assignments = [values[index % len(values)] for index in range(count)]
    rng.shuffle(assignments)
    return assignments


def _unique_name(
    cuisine: str,
    record_number: int,
    used_names: set[str],
    rng: random.Random,
) -> str:
    for _ in range(100):
        candidate = " ".join(
            (
                rng.choice(NAME_PREFIXES),
                rng.choice(CUISINE_NOUNS[cuisine]),
                rng.choice(NAME_SUFFIXES),
            )
        )
        if candidate not in used_names:
            used_names.add(candidate)
            return candidate

    fallback = f"Synthetic {cuisine} Restaurant {record_number:03d}"
    used_names.add(fallback)
    return fallback


def _opening_hours(rng: random.Random) -> dict[str, OpeningPeriod | None]:
    opening_hour = rng.choice((10, 11, 12))
    closing_hour = rng.choice((20, 21, 22, 23))
    closed_day = rng.choice((*DAYS, None, None, None, None))

    return {
        day: (
            None
            if day == closed_day
            else {
                "open": f"{opening_hour:02d}:00",
                "close": f"{closing_hour:02d}:00",
            }
        )
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
            location["latitude"],
            location["longitude"],
            latitude,
            longitude,
        )
        estimates[origin] = {
            "straight_line_distance_km": round(distance_km, 2),
            "walking_minutes": max(
                3, round((distance_km / 4.8) * 60 + rng.uniform(1, 4))
            ),
            "public_transit_minutes": max(
                8, round(7 + (distance_km / 22) * 60 + rng.uniform(0, 7))
            ),
            "driving_minutes": max(
                5, round(4 + (distance_km / 28) * 60 + rng.uniform(0, 6))
            ),
            "estimate_type": "synthetic",
        }

    return estimates


def generate_dataset(
    count: int = DEFAULT_RESTAURANT_COUNT,
    seed: int = DEFAULT_SEED,
) -> Dataset:
    """Build a deterministic synthetic Chicago restaurant dataset."""

    if count <= 0:
        raise ValueError("Restaurant count must be greater than zero.")

    rng = random.Random(seed)
    neighborhood_assignments = _balanced_values(
        tuple(NEIGHBORHOODS), count, rng
    )
    cuisine_assignments = _balanced_values(CUISINES, count, rng)
    price_assignments = _balanced_values(tuple(PRICE_RANGES), count, rng)
    used_names: set[str] = set()
    restaurants: list[Restaurant] = []

    for index in range(1, count + 1):
        neighborhood = neighborhood_assignments[index - 1]
        neighborhood_config = NEIGHBORHOODS[neighborhood]
        cuisine = cuisine_assignments[index - 1]
        price_category = price_assignments[index - 1]
        minimum_cost, maximum_cost = PRICE_RANGES[price_category]
        latitude = round(
            neighborhood_config["latitude"] + rng.uniform(-0.006, 0.006), 6
        )
        longitude = round(
            neighborhood_config["longitude"] + rng.uniform(-0.008, 0.008), 6
        )
        vegetarian_available = index % 5 != 0
        vegan_available = vegetarian_available and index % 3 == 0
        street_number = 100 + index * 37
        street_name = FICTIONAL_STREETS[(index - 1) % len(FICTIONAL_STREETS)]

        restaurants.append(
            {
                "restaurant_id": f"CHI-SYN-{index:03d}",
                "name": _unique_name(cuisine, index, used_names, rng),
                "address": (
                    f"{street_number} {street_name}, Chicago, IL "
                    f"{neighborhood_config['zip_code']}"
                ),
                "city": "Chicago",
                "state": "IL",
                "neighborhood": neighborhood,
                "latitude": latitude,
                "longitude": longitude,
                "cuisine": cuisine,
                "price_category": price_category,
                "estimated_cost_per_person": rng.randint(
                    minimum_cost, maximum_cost
                ),
                "vegetarian_available": vegetarian_available,
                "vegan_available": vegan_available,
                "rating": round(rng.uniform(3.2, 4.9), 1),
                "review_count": rng.randint(12, 1_200),
                "opening_hours": _opening_hours(rng),
                "estimated_transportation": _transportation_estimates(
                    latitude, longitude, rng
                ),
                "data_provenance": "synthetic",
            }
        )

    return {
        "metadata": {
            "dataset_name": "BiteCheck Synthetic Chicago Restaurants",
            "description": (
                "Reproducible fictional restaurant records for portfolio "
                "development and testing."
            ),
            "city": "Chicago",
            "synthetic": True,
            "seed": seed,
            "record_count": count,
            "generator_version": GENERATOR_VERSION,
            "schema_version": SCHEMA_VERSION,
        },
        "restaurants": restaurants,
    }


def write_dataset(
    output_path: Path = DEFAULT_OUTPUT_PATH,
    count: int = DEFAULT_RESTAURANT_COUNT,
    seed: int = DEFAULT_SEED,
) -> Path:
    """Write deterministic JSON and return the resolved output path."""

    dataset = generate_dataset(count=count, seed=seed)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(dataset, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return output_path.resolve()


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate BiteCheck's synthetic Chicago restaurant data."
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_PATH,
        help="Destination JSON path.",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=DEFAULT_RESTAURANT_COUNT,
        help="Number of restaurant records to create.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=DEFAULT_SEED,
        help="Random seed used for reproducible output.",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    output_path = write_dataset(
        output_path=args.output,
        count=args.count,
        seed=args.seed,
    )
    print(f"Generated {args.count} synthetic restaurants at {output_path}")


if __name__ == "__main__":
    main()
