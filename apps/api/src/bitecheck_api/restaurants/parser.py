import re
import unicodedata
from collections.abc import Iterable
from typing import Protocol

from bitecheck_api.restaurants.models import RestaurantSearchFilters


PARSER_VERSION = "1.0.0"

CUISINE_ALIASES: dict[str, tuple[str, ...]] = {
    "American": ("american",),
    "Chinese": ("chinese",),
    "Ethiopian": ("ethiopian",),
    "Indian": ("indian",),
    "Italian": ("italian",),
    "Japanese": ("japanese",),
    "Korean": ("korean",),
    "Mediterranean": ("mediterranean",),
    "Mexican": ("mexican",),
    "Thai": ("thai",),
}

STARTING_AREA_ALIASES: dict[str, tuple[str, ...]] = {
    "Illinois Tech": (
        "illinois tech",
        "illinois institute of technology",
        "iit",
    ),
    "Chinatown": ("chinatown",),
    "Chicago Loop": ("chicago loop", "the loop"),
    "Hyde Park": ("hyde park",),
    "Bridgeport": ("bridgeport",),
    "Lakeview": ("lakeview", "lake view"),
    "River North": ("river north",),
}

_BUDGET_PATTERNS = (
    re.compile(r"\$\s*(?P<value>\d{1,4})\b"),
    re.compile(
        r"\b(?:under|below|less than|no more than|up to|"
        r"max(?:imum)? budget(?: of)?|budget(?: of| is| around)?|"
        r"spend(?:ing)?(?: up to)?)\s+\$?\s*(?P<value>\d{1,4})"
        r"(?!\s*(?:minutes?|mins?)\b)(?:\s*(?:dollars?|bucks?))?\b"
    ),
)

_TRAVEL_TIME_PATTERNS = (
    re.compile(
        r"\b(?:within|under|below|less than|no more than|up to|"
        r"max(?:imum)?(?: travel time)?(?: of)?)\s+"
        r"(?P<value>\d{1,4})\s*(?:minutes?|mins?)\b"
    ),
    re.compile(
        r"\b(?P<value>\d{1,4})\s*(?:minutes?|mins?)\s+"
        r"(?:away|or less|maximum|max)\b"
    ),
)

_VEGETARIAN_PATTERN = re.compile(r"\b(?:vegetarian|veggie|meatless)\b")
_NEGATIVE_VEGETARIAN_PATTERNS = (
    re.compile(r"\b(?:no|without)\s+(?:vegetarian|veggie|meatless)\b"),
    re.compile(
        r"\b(?:vegetarian|veggie|meatless)(?:\s+options?)?\s+"
        r"(?:are\s+)?(?:not required|optional)\b"
    ),
)


class NaturalLanguageParseError(ValueError):
    """Explain why a sentence cannot safely become structured filters."""

    def __init__(
        self,
        field: str,
        message: str,
        candidates: tuple[str, ...] = (),
    ) -> None:
        self.field = field
        self.candidates = candidates
        super().__init__(message)


class RestaurantRequestParser(Protocol):
    """Replaceable interface for sentence-to-filter parsers."""

    def parse(self, text: str) -> RestaurantSearchFilters:
        """Convert user text into validated restaurant search filters."""


def normalize_text(text: str) -> str:
    """Create a stable comparison form without changing the original input."""

    unicode_normalized = unicodedata.normalize("NFKC", text)
    return " ".join(unicode_normalized.casefold().split())


def _contains_phrase(text: str, phrase: str) -> bool:
    return re.search(rf"(?<!\w){re.escape(phrase)}(?!\w)", text) is not None


def _matching_canonical_values(
    text: str,
    aliases_by_value: dict[str, tuple[str, ...]],
) -> tuple[str, ...]:
    matches = {
        canonical
        for canonical, aliases in aliases_by_value.items()
        if any(_contains_phrase(text, alias) for alias in aliases)
    }
    return tuple(sorted(matches))


def _extract_numbers(text: str, patterns: Iterable[re.Pattern[str]]) -> tuple[int, ...]:
    values = {
        int(match.group("value"))
        for pattern in patterns
        for match in pattern.finditer(text)
    }
    return tuple(sorted(values))


def _one_or_none(
    field: str,
    values: tuple[str, ...] | tuple[int, ...],
) -> str | int | None:
    if len(values) > 1:
        candidates = tuple(str(value) for value in values)
        raise NaturalLanguageParseError(
            field=field,
            message=(
                f"The request mentions multiple {field.replace('_', ' ')} values. "
                "Please choose one."
            ),
            candidates=candidates,
        )
    return values[0] if values else None


def _vegetarian_is_required(text: str) -> bool:
    if any(pattern.search(text) for pattern in _NEGATIVE_VEGETARIAN_PATTERNS):
        return False
    return _VEGETARIAN_PATTERN.search(text) is not None


class RuleBasedRestaurantRequestParser:
    """Deterministic parser for the five Milestone 2 search filters."""

    def parse(self, text: str) -> RestaurantSearchFilters:
        normalized = normalize_text(text)

        cuisine = _one_or_none(
            "cuisine",
            _matching_canonical_values(normalized, CUISINE_ALIASES),
        )
        starting_area = _one_or_none(
            "starting_area",
            _matching_canonical_values(normalized, STARTING_AREA_ALIASES),
        )
        maximum_budget = _one_or_none(
            "maximum_budget",
            _extract_numbers(normalized, _BUDGET_PATTERNS),
        )
        maximum_travel_time = _one_or_none(
            "maximum_travel_time",
            _extract_numbers(normalized, _TRAVEL_TIME_PATTERNS),
        )

        if maximum_budget is not None and int(maximum_budget) <= 0:
            raise NaturalLanguageParseError(
                field="maximum_budget",
                message="Maximum budget must be greater than zero.",
            )
        if maximum_travel_time is not None and int(maximum_travel_time) <= 0:
            raise NaturalLanguageParseError(
                field="maximum_travel_time",
                message="Maximum travel time must be greater than zero.",
            )

        if maximum_travel_time is not None and starting_area is None:
            raise NaturalLanguageParseError(
                field="starting_area",
                message=(
                    "A starting area is required when the request includes a "
                    "maximum travel time."
                ),
            )

        return RestaurantSearchFilters(
            cuisine=str(cuisine) if cuisine is not None else None,
            maximum_budget=(
                int(maximum_budget) if maximum_budget is not None else None
            ),
            vegetarian_required=_vegetarian_is_required(normalized),
            starting_area=(
                str(starting_area) if starting_area is not None else None
            ),
            maximum_travel_time=(
                int(maximum_travel_time)
                if maximum_travel_time is not None
                else None
            ),
        )


def get_restaurant_request_parser() -> RestaurantRequestParser:
    return RuleBasedRestaurantRequestParser()
