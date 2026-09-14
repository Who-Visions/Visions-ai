/**
 * suntimes.js -- NOAA solar position algorithm and ephemeris engine for God's Eye.
 * Pure mathematical arithmetic: 0 dependencies, 0 network, 0 rate limit.
 *
 * Provides:
 * - Civil Dawn / Dusk
 * - Sunrise / Sunset
 * - Golden Hour Windows (Morning & Evening)
 * - Real-time Solar Elevation & Azimuth
 * - Solar Phase Classification (Night, Civil Dawn, Sunrise, Golden Morning, Daylight, Golden Evening, Sunset, Civil Dusk)
 */

export const SAVED_SUN_SITES = {
  palmbeach: { name: 'Palm Beach Island (Worth Ave)', lat: 26.7056, lon: -80.0364, tz: -4.0 },
  lakeworth: { name: 'Lake Worth Pier', lat: 26.6156, lon: -80.0339, tz: -4.0 },
  lantana: { name: 'Lantana Beach', lat: 26.5875, lon: -80.0364, tz: -4.0 },
  miami: { name: 'Miami Beach', lat: 25.7617, lon: -80.1918, tz: -4.0 },
  nyc: { name: 'New York City', lat: 40.7128, lon: -74.0060, tz: -4.0 },
  tokyo: { name: 'Tokyo', lat: 35.6762, lon: 139.6503, tz: 9.0 },
  london: { name: 'London', lat: 51.5074, lon: -0.1278, tz: 1.0 },
  paris: { name: 'Paris', lat: 48.8566, lon: 2.3522, tz: 2.0 },
  dubai: { name: 'Dubai', lat: 25.2048, lon: 55.2708, tz: 4.0 },
  dc: { name: 'Washington DC', lat: 38.9072, lon: -77.0369, tz: -4.0 },
};

export const ZENITH = {
  civil_dawn: 96.0,
  sunrise: 90.833,
  golden_end: 84.0,
  golden_start: 84.0,
  sunset: 90.833,
  civil_dusk: 96.0,
};

const rad = (d) => (d * Math.PI) / 180;
const deg = (r) => (r * 180) / Math.PI;

function julianDay(year, month, day) {
  let y = year;
  let m = month;
  if (m <= 2) {
    y -= 1;
    m += 12;
  }
  const a = Math.floor(y / 100);
  const b = 2 - a + Math.floor(a / 4);
  return Math.floor(365.25 * (y + 4716)) + Math.floor(30.6001 * (m + 1)) + day + b - 1524.5;
}

function solarCalculations(jd) {
  const t = (jd - 2451545.0) / 36525.0;
  const l0 = (280.46646 + t * (36000.76983 + t * 0.0003032)) % 360;
  const m = 357.52911 + t * (35999.05029 - 0.0001537 * t);
  const e = 0.016708634 - t * (0.000042037 + 0.0000001267 * t);
  const mr = rad(m);
  const c =
    Math.sin(mr) * (1.914602 - t * (0.004817 + 0.000014 * t)) +
    Math.sin(2 * mr) * (0.019993 - 0.000101 * t) +
    Math.sin(3 * mr) * 0.000289;
  const omega = 125.04 - 1934.136 * t;
  const lam = l0 + c - 0.00569 - 0.00478 * Math.sin(rad(omega));
  const secs = 21.448 - t * (46.815 - t * (0.00059 - t * 0.001813));
  const eps = 23 + (26 + secs / 60) / 60 + 0.00256 * Math.cos(rad(omega));
  const decl = deg(Math.asin(Math.sin(rad(eps)) * Math.sin(rad(lam))));
  const y = Math.tan(rad(eps / 2)) ** 2;
  const l0r = rad(l0);
  const eqt =
    4 *
    deg(
      y * Math.sin(2 * l0r) -
        2 * e * Math.sin(mr) +
        4 * e * y * Math.sin(mr) * Math.cos(2 * l0r) -
        0.5 * y * y * Math.sin(4 * l0r) -
        1.25 * e * e * Math.sin(2 * mr)
    );
  return { decl, eqt };
}

function computeEventTime(year, month, day, lat, lon, zenith, rising, tz) {
  const jd = julianDay(year, month, day);
  let minutes = null;
  for (let i = 0; i < 3; i++) {
    const j = minutes === null ? jd : jd + minutes / 1440.0;
    const { decl, eqt } = solarCalculations(j);
    const cosH =
      Math.cos(rad(zenith)) / (Math.cos(rad(lat)) * Math.cos(rad(decl))) -
      Math.tan(rad(lat)) * Math.tan(rad(decl));
    if (cosH > 1 || cosH < -1) return null; // Polar day / polar night
    const ha = deg(Math.acos(cosH));
    minutes = 720 - 4 * (lon + (rising ? ha : -ha)) - eqt;
  }
  const local = minutes + tz * 60;
  const h = (Math.floor(local / 60) + 24) % 24;
  const m = Math.round(local % 60);
  return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}`;
}

/**
 * Compute full sun times table for given date, latitude, longitude and UTC offset.
 */
export function computeSunTimes(dateInput = new Date(), lat = 26.7056, lon = -80.0364, tz = -4.0) {
  const d = dateInput instanceof Date ? dateInput : new Date(dateInput);
  const year = d.getFullYear();
  const month = d.getMonth() + 1;
  const day = d.getDate();

  const ev = (zen, rising) => computeEventTime(year, month, day, lat, lon, zen, rising, tz);

  const civilDawn = ev(ZENITH.civil_dawn, true);
  const sunrise = ev(ZENITH.sunrise, true);
  const goldenMorningEnd = ev(ZENITH.golden_end, true);
  const goldenEveningStart = ev(ZENITH.golden_start, false);
  const sunset = ev(ZENITH.sunset, false);
  const civilDusk = ev(ZENITH.civil_dusk, false);

  return {
    date: d.toISOString().split('T')[0],
    lat,
    lon,
    utc_offset: tz,
    civil_dawn: civilDawn,
    sunrise,
    golden_morning_end: goldenMorningEnd,
    golden_evening_start: goldenEveningStart,
    sunset,
    civil_dusk: civilDusk,
    golden_morning_window: { from: sunrise, to: goldenMorningEnd },
    golden_evening_window: { from: goldenEveningStart, to: sunset },
  };
}

/**
 * Real-time solar position (elevation angle and azimuth degrees).
 */
export function getSolarPosition(dateInput = new Date(), lat = 26.7056, lon = -80.0364) {
  const d = dateInput instanceof Date ? dateInput : new Date(dateInput);
  const jd =
    d.getTime() / 86400000 -
    d.getTimezoneOffset() / 1440 +
    2440587.5;
  const { decl, eqt } = solarCalculations(jd);
  
  const utcHours = d.getUTCHours() + d.getUTCMinutes() / 60 + d.getUTCSeconds() / 3600;
  const solarTime = (utcHours * 60 + eqt + 4 * lon + 1440) % 1440;
  const ha = (solarTime / 4) - 180; // Hour angle in degrees

  const latR = rad(lat);
  const declR = rad(decl);
  const haR = rad(ha);

  const elevationR = Math.asin(
    Math.sin(latR) * Math.sin(declR) +
    Math.cos(latR) * Math.cos(declR) * Math.cos(haR)
  );
  const elevation = deg(elevationR);

  const azimuthR = Math.atan2(
    -Math.sin(haR),
    Math.tan(declR) * Math.cos(latR) - Math.sin(latR) * Math.cos(haR)
  );
  const azimuth = (deg(azimuthR) + 360) % 360;

  return {
    elevation,
    azimuth,
    declination: decl,
    hourAngle: ha,
  };
}

/**
 * Identify current lighting phase based on solar elevation angle.
 */
export function getSolarPhase(elevation) {
  if (elevation < -18) return { phase: 'Night', code: 'night', label: 'Astronomical Night' };
  if (elevation < -12) return { phase: 'Astronomical Twilight', code: 'astro_twilight', label: 'Astronomical Twilight' };
  if (elevation < -6) return { phase: 'Nautical Twilight', code: 'naut_twilight', label: 'Nautical Twilight' };
  if (elevation < -0.833) return { phase: 'Civil Twilight (Blue Hour)', code: 'civil_twilight', label: 'Civil Twilight / Blue Hour' };
  if (elevation <= 6.0) return { phase: 'Golden Hour', code: 'golden_hour', label: 'Golden Hour 🌅' };
  if (elevation > 6.0 && elevation < 25.0) return { phase: 'Low Sun', code: 'low_sun', label: 'Low Sun Daylight' };
  return { phase: 'Daylight', code: 'daylight', label: 'Full Sunlight ☀️' };
}
