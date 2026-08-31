import math
from collections import Counter
from datetime import UTC, datetime
from typing import Protocol

import httpx
from pydantic import BaseModel, ConfigDict, ValidationError

from bitecheck_api.restaurants.models import (
    InspectionAttentionLevel,
    InspectionExplorerRequest,
    InspectionExplorerResponse,
    PublicInspectionHistory,
    PublicInspectionRestaurant,
    PublicInspectionSummary,
)


CHICAGO_INSPECTIONS_API_URL = (
    "https://data.cityofchicago.org/resource/4ijn-s7e5.json"
)
CHICAGO_INSPECTIONS_SOURCE_URL = (
    "https://data.cityofchicago.org/Health-Human-Services/"
    "Food-Inspections/4ijn-s7e5"
)
SOURCE_NAME = "City of Chicago Food Inspections"
SOURCE_SELECT = (
    "inspection_id,dba_name,aka_name,license_,facility_type,risk,address,"
    "city,state,zip,inspection_date,inspection_type,results,latitude,longitude"
)


class InspectionProviderError(RuntimeError):
    """Raised when the public inspection source cannot be queried safely."""


class SourceInspection(BaseModel):
    """Validated boundary model for one City API row."""

    model_config = ConfigDict(extra="ignore")

    inspection_id: str
    dba_name: str
    aka_name: str | None = None
    license_: str
    facility_type: str
    risk: str = "Risk category unavailable"
    address: str
    city: str = "CHICAGO"
    state: str = "IL"
    zip: str = ""
    inspection_date: datetime
    inspection_type: str
    results: str
    latitude: float
    longitude: float


class InspectionProvider(Protocol):
    async def fetch(
        self, request: InspectionExplorerRequest
    ) -> tuple[SourceInspection, ...]:
        """Return validated rows in newest-inspection-first order."""


def _escaped_query(value: str) -> str:
    return value.casefold().replace("'", "''")


def build_chicago_query(request: InspectionExplorerRequest) -> dict[str, str]:
    clauses = [
        "lower(facility_type) like '%restaurant%'",
        "latitude is not null",
        "longitude is not null",
    ]
    if request.latitude is not None and request.longitude is not None:
        radius_metres = round(request.radius_km * 1_000)
        clauses.append(
            "within_circle(location,"
            f"{request.latitude:.6f},{request.longitude:.6f},{radius_metres})"
        )
    if request.query is not None:
        query = _escaped_query(request.query)
        clauses.append(
            "(lower(dba_name) like '%"
            f"{query}%' or lower(aka_name) like '%{query}%' "
            f"or lower(address) like '%{query}%' or zip = '{query}')"
        )

    source_limit = min(2_000, max(300, request.limit * 30))
    return {
        "$select": SOURCE_SELECT,
        "$where": " and ".join(clauses),
        "$order": "inspection_date desc,inspection_id desc",
        "$limit": str(source_limit),
    }


def parse_source_rows(payload: object) -> tuple[SourceInspection, ...]:
    if not isinstance(payload, list):
        raise InspectionProviderError("The City inspection response was invalid.")

    rows: list[SourceInspection] = []
    for item in payload:
        try:
            rows.append(SourceInspection.model_validate(item))
        except ValidationError:
            continue
    return tuple(rows)


class ChicagoInspectionProvider:
    """Read live public restaurant-inspection rows through the SODA API."""

    async def fetch(
        self, request: InspectionExplorerRequest
    ) -> tuple[SourceInspection, ...]:
        try:
            async with httpx.AsyncClient(timeout=8, follow_redirects=True) as client:
                response = await client.get(
                    CHICAGO_INSPECTIONS_API_URL,
                    params=build_chicago_query(request),
                    headers={"Accept": "application/json"},
                )
                response.raise_for_status()
                payload: object = response.json()
        except (httpx.HTTPError, ValueError) as error:
            raise InspectionProviderError(
                "The City inspection service is unavailable."
            ) from error
        return parse_source_rows(payload)


def get_inspection_provider() -> InspectionProvider:
    return ChicagoInspectionProvider()


def _distance_km(
    latitude_a: float,
    longitude_a: float,
    latitude_b: float,
    longitude_b: float,
) -> float:
    earth_radius_km = 6_371.0088
    latitude_delta = math.radians(latitude_b - latitude_a)
    longitude_delta = math.radians(longitude_b - longitude_a)
    latitude_a_radians = math.radians(latitude_a)
    latitude_b_radians = math.radians(latitude_b)
    haversine = (
        math.sin(latitude_delta / 2) ** 2
        + math.cos(latitude_a_radians)
        * math.cos(latitude_b_radians)
        * math.sin(longitude_delta / 2) ** 2
    )
    return earth_radius_km * 2 * math.atan2(
        math.sqrt(haversine), math.sqrt(1 - haversine)
    )


def _result_group(result: str) -> str:
    normalized = result.casefold()
    if normalized == "pass":
        return "pass"
    if "condition" in normalized:
        return "conditions"
    if normalized == "fail":
        return "fail"
    return "other"


def _attention(result: str) -> tuple[InspectionAttentionLevel, str]:
    group = _result_group(result)
    if group == "pass":
        return "latest_passed", "Latest inspection passed"
    if group == "conditions":
        return "conditions_noted", "Latest inspection passed with conditions"
    if group == "fail":
        return "review_latest_report", "Review the latest failed inspection"
    return "informational", f"Latest City result: {result}"


def _public_address(row: SourceInspection) -> str:
    parts = [row.address, row.city, row.state, row.zip]
    return ", ".join(part for part in parts if part)


class InspectionExplorerService:
    def __init__(self, provider: InspectionProvider) -> None:
        self._provider = provider

    async def explore(
        self, request: InspectionExplorerRequest
    ) -> InspectionExplorerResponse:
        source_rows = await self._provider.fetch(request)
        rows_by_license: dict[str, list[SourceInspection]] = {}
        for row in source_rows:
            rows_by_license.setdefault(row.license_, []).append(row)

        restaurants: list[PublicInspectionRestaurant] = []
        for rows in rows_by_license.values():
            rows.sort(
                key=lambda row: (row.inspection_date, row.inspection_id),
                reverse=True,
            )
            latest = rows[0]
            group = _result_group(latest.results)
            if request.result_filter != "all" and group != request.result_filter:
                continue

            counts = Counter(_result_group(row.results) for row in rows)
            distance = None
            if request.latitude is not None and request.longitude is not None:
                distance = round(
                    _distance_km(
                        request.latitude,
                        request.longitude,
                        latest.latitude,
                        latest.longitude,
                    ),
                    2,
                )
            attention_level, attention_label = _attention(latest.results)
            restaurants.append(
                PublicInspectionRestaurant(
                    license_number=latest.license_,
                    name=latest.dba_name,
                    alternate_name=(
                        latest.aka_name
                        if latest.aka_name
                        and latest.aka_name.casefold() != latest.dba_name.casefold()
                        else None
                    ),
                    facility_type=latest.facility_type,
                    city_risk_category=latest.risk,
                    address=_public_address(latest),
                    latitude=latest.latitude,
                    longitude=latest.longitude,
                    distance_km=distance,
                    attention_level=attention_level,
                    attention_label=attention_label,
                    latest_inspection=PublicInspectionSummary(
                        inspection_id=latest.inspection_id,
                        inspection_date=latest.inspection_date.date(),
                        result=latest.results,
                        inspection_type=latest.inspection_type,
                    ),
                    history=PublicInspectionHistory(
                        records_in_query=len(rows),
                        pass_count=counts["pass"],
                        conditions_count=counts["conditions"],
                        fail_count=counts["fail"],
                        other_count=counts["other"],
                    ),
                )
            )

        if request.latitude is not None:
            restaurants.sort(
                key=lambda restaurant: (
                    restaurant.distance_km
                    if restaurant.distance_km is not None
                    else math.inf,
                    restaurant.name.casefold(),
                )
            )
        else:
            restaurants.sort(
                key=lambda restaurant: (
                    restaurant.latest_inspection.inspection_date,
                    restaurant.name.casefold(),
                ),
                reverse=True,
            )

        limited = restaurants[: request.limit]
        return InspectionExplorerResponse(
            source_name=SOURCE_NAME,
            source_url=CHICAGO_INSPECTIONS_SOURCE_URL,
            retrieved_at=datetime.now(UTC).isoformat(),
            source_record_count=len(source_rows),
            restaurant_count=len(limited),
            restaurants=limited,
            data_notice=(
                "Live City of Chicago inspection records. Results describe the "
                "conditions observed on an inspection date; they do not guarantee "
                "that a business is currently open or currently safe. History "
                "counts include only records returned by this live query."
            ),
        )
