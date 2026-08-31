export type Coordinates = {
  latitude: number;
  longitude: number;
};

const EARTH_RADIUS_KM = 6_371;

function radians(value: number): number {
  return (value * Math.PI) / 180;
}

export function straightLineDistanceKm(
  origin: Coordinates,
  destination: Coordinates,
): number {
  const latitudeDelta = radians(destination.latitude - origin.latitude);
  const longitudeDelta = radians(destination.longitude - origin.longitude);
  const originLatitude = radians(origin.latitude);
  const destinationLatitude = radians(destination.latitude);
  const haversine =
    Math.sin(latitudeDelta / 2) ** 2 +
    Math.cos(originLatitude) *
      Math.cos(destinationLatitude) *
      Math.sin(longitudeDelta / 2) ** 2;

  return (
    EARTH_RADIUS_KM *
    2 *
    Math.atan2(Math.sqrt(haversine), Math.sqrt(1 - haversine))
  );
}

export function formatDistance(distanceKm: number): string {
  if (distanceKm < 1) {
    return `${Math.round(distanceKm * 1_000)} m`;
  }
  return `${distanceKm.toFixed(1)} km`;
}

export function openStreetMapUrl(coordinates: Coordinates): string {
  const latitude = coordinates.latitude.toFixed(6);
  const longitude = coordinates.longitude.toFixed(6);
  return `https://www.openstreetmap.org/?mlat=${latitude}&mlon=${longitude}#map=18/${latitude}/${longitude}`;
}
