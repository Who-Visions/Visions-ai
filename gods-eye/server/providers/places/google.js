import {
  googleServerApiKey,
  keylessGooglePlacesResponse,
} from './google-key.js';
import { makeOptInRateLimiter, clientKey } from '../common/rate-limit.js';
import {
  projectNearbyPlaces,
  projectTextSearchPlaces,
} from '../../../src/data/placeProviderPayloads.js';
import {
  computeSunTimes,
  getSolarPosition,
  getSolarPhase,
  SAVED_SUN_SITES,
} from '../../../src/data/suntimes.js';

// Construct lazily after the standalone environment has loaded.
// undefined = not built yet; null = unlimited; fn = active limiter
let _googleRateLimiter;

/** Google cost endpoint (nearby-places). Null = unlimited (default). */
function googleRateLimiter() {
  if (_googleRateLimiter === undefined)
    _googleRateLimiter = makeOptInRateLimiter(
      process.env.GEV_RATELIMIT_GOOGLE_PER_MIN,
    );
  return _googleRateLimiter;
}

/** Nearby place labels and view-biased text search, with request-time key resolution. */
export function googlePlacesContextProxy({
  resolveApiKey = googleServerApiKey,
} = {}) {
  function install(middlewares) {
    middlewares.use('/api/google/nearby-places', async (req, res) => {
      if (req.method !== 'GET') {
        res.statusCode = 405;
        res.setHeader('Content-Type', 'application/json');
        res.end(JSON.stringify({ error: 'Method not allowed', places: [] }));
        return;
      }

      // Keyless place context has no provider cost, so it resolves before the
      // paid-endpoint limiter can consume or exhaust quota (mirrors the HUD
      // summary route).
      const apiKey = resolveApiKey();
      const keyless = keylessGooglePlacesResponse(apiKey);
      if (keyless) {
        res.statusCode = keyless.statusCode;
        res.setHeader('Content-Type', 'application/json');
        res.setHeader('Cache-Control', 'no-store');
        res.end(JSON.stringify(keyless.payload));
        return;
      }

      // Opt-in per-IP throttle (GEV_RATELIMIT_GOOGLE_PER_MIN). No-op when unset.
      // Inlined (not the shared helper) so the 429 body keeps this endpoint's
      // `places: []` contract that the client expects on every error response.
      const _grl = googleRateLimiter();
      if (_grl && !_grl(clientKey(req))) {
        res.statusCode = 429;
        res.setHeader('Content-Type', 'application/json');
        res.setHeader('Retry-After', '5');
        res.end(JSON.stringify({ error: 'Rate limit exceeded', places: [] }));
        return;
      }

      const requestUrl = new URL(req.url || '', 'http://localhost');
      const latitude = Number(requestUrl.searchParams.get('lat'));
      const longitude = Number(requestUrl.searchParams.get('lon'));
      const radiusM = Math.max(
        25,
        Math.min(5000, Number(requestUrl.searchParams.get('radiusM')) || 250),
      );
      if (!Number.isFinite(latitude) || !Number.isFinite(longitude)) {
        res.statusCode = 400;
        res.setHeader('Content-Type', 'application/json');
        res.end(
          JSON.stringify({
            error: 'Valid lat and lon are required',
            places: [],
          }),
        );
        return;
      }

      try {
        const response = await fetch(
          'https://places.googleapis.com/v1/places:searchNearby',
          {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'X-Goog-Api-Key': apiKey,
              'X-Goog-FieldMask': [
                'places.id',
                'places.displayName',
                'places.formattedAddress',
                'places.shortFormattedAddress',
                'places.location',
                'places.primaryType',
                'places.primaryTypeDisplayName',
                'places.types',
              ].join(','),
            },
            body: JSON.stringify({
              maxResultCount: 20,
              rankPreference: 'DISTANCE',
              locationRestriction: {
                circle: {
                  center: { latitude, longitude },
                  radius: radiusM,
                },
              },
            }),
          },
        );
        const data = await response.json().catch(() => ({}));
        const places = projectNearbyPlaces(data, latitude, longitude);

        res.statusCode = response.ok ? 200 : response.status;
        res.setHeader('Content-Type', 'application/json; charset=utf-8');
        res.setHeader('Cache-Control', 'private, max-age=300');
        res.end(
          JSON.stringify({
            places,
            error: response.ok
              ? null
              : data.error?.message || 'Google Places request failed',
          }),
        );
      } catch (error) {
        res.statusCode = 502;
        res.setHeader('Content-Type', 'application/json; charset=utf-8');
        res.end(
          JSON.stringify({
            error: error?.message || 'Google Places request failed',
            places: [],
          }),
        );
      }
    });

    // Text Search: resolve a named landmark/POI to a real coordinate, biased to
    // the view. Geocoding scatters obscure monument/POI names across the city;
    // a view-biased Text Search lands on the actual feature. Same key, field
    // mask, throttle, and `places: []` error contract as nearby-places above.
    middlewares.use('/api/google/text-search', async (req, res) => {
      if (req.method !== 'GET') {
        res.statusCode = 405;
        res.setHeader('Content-Type', 'application/json');
        res.end(JSON.stringify({ error: 'Method not allowed', places: [] }));
        return;
      }

      // Keyless place context has no provider cost, so it resolves before the
      // paid-endpoint limiter can consume or exhaust quota (mirrors the HUD
      // summary route).
      const apiKey = resolveApiKey();
      const keyless = keylessGooglePlacesResponse(apiKey);
      if (keyless) {
        res.statusCode = keyless.statusCode;
        res.setHeader('Content-Type', 'application/json');
        res.setHeader('Cache-Control', 'no-store');
        res.end(JSON.stringify(keyless.payload));
        return;
      }

      // Opt-in per-IP throttle (GEV_RATELIMIT_GOOGLE_PER_MIN). No-op when unset.
      // Inlined (like nearby-places) so the 429 body keeps the `places: []`
      // contract the client expects on every error response.
      const _grl = googleRateLimiter();
      if (_grl && !_grl(clientKey(req))) {
        res.statusCode = 429;
        res.setHeader('Content-Type', 'application/json');
        res.setHeader('Retry-After', '5');
        res.end(JSON.stringify({ error: 'Rate limit exceeded', places: [] }));
        return;
      }

      const requestUrl = new URL(req.url || '', 'http://localhost');
      const textQuery = String(requestUrl.searchParams.get('q') || '').trim();
      const latitude = Number(requestUrl.searchParams.get('lat'));
      const longitude = Number(requestUrl.searchParams.get('lon'));
      const radiusM = Math.max(
        50,
        Math.min(50000, Number(requestUrl.searchParams.get('radiusM')) || 4000),
      );
      if (
        !textQuery ||
        !Number.isFinite(latitude) ||
        !Number.isFinite(longitude)
      ) {
        res.statusCode = 400;
        res.setHeader('Content-Type', 'application/json');
        res.end(
          JSON.stringify({ error: 'q, lat and lon are required', places: [] }),
        );
        return;
      }

      try {
        const response = await fetch(
          'https://places.googleapis.com/v1/places:searchText',
          {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'X-Goog-Api-Key': apiKey,
              'X-Goog-FieldMask': [
                'places.id',
                'places.displayName',
                'places.formattedAddress',
                'places.location',
                'places.viewport',
                'places.primaryType',
                'places.types',
              ].join(','),
            },
            body: JSON.stringify({
              textQuery,
              locationBias: {
                circle: {
                  center: { latitude, longitude },
                  radius: radiusM,
                },
              },
              maxResultCount: 5,
            }),
          },
        );
        const data = await response.json().catch(() => ({}));
        const places = projectTextSearchPlaces(data, latitude, longitude);

        res.statusCode = response.ok ? 200 : response.status;
        res.setHeader('Content-Type', 'application/json; charset=utf-8');
        res.setHeader('Cache-Control', 'private, max-age=300');
        res.end(
          JSON.stringify({
            places,
            error: response.ok
              ? null
              : data.error?.message || 'Google Places request failed',
          }),
        );
      } catch (error) {
        res.statusCode = 502;
        res.setHeader('Content-Type', 'application/json; charset=utf-8');
        res.end(
          JSON.stringify({
            error: error?.message || 'Google Places request failed',
            places: [],
          }),
        );
      }
    });

    // Dynamic Geocode & Reverse Geocode Fallback Route: Resolves any address, city, coordinate or landmark
    middlewares.use('/api/geocode', async (req, res) => {
      if (req.method !== 'GET') {
        res.statusCode = 405;
        res.setHeader('Content-Type', 'application/json');
        res.end(JSON.stringify({ error: 'Method not allowed' }));
        return;
      }
      const requestUrl = new URL(req.url || '', 'http://localhost');
      const query = String(requestUrl.searchParams.get('q') || requestUrl.searchParams.get('address') || '').trim();
      const latParam = requestUrl.searchParams.get('lat') || (requestUrl.searchParams.get('latlng') ? requestUrl.searchParams.get('latlng').split(',')[0] : null);
      const lonParam = requestUrl.searchParams.get('lon') || requestUrl.searchParams.get('lng') || (requestUrl.searchParams.get('latlng') ? requestUrl.searchParams.get('latlng').split(',')[1] : null);

      const apiKey = process.env.GOOGLE_MAPS_SERVER_API_KEY || process.env.GOOGLE_MAPS_API_KEY || resolveApiKey();

      // REVERSE GEOCODING MODE
      if (latParam != null && lonParam != null) {
        const revLat = parseFloat(latParam);
        const revLon = parseFloat(lonParam);
        if (Number.isFinite(revLat) && Number.isFinite(revLon)) {
          // 1. Google Reverse Geocode
          if (apiKey) {
            try {
              const gRevUrl = `https://maps.googleapis.com/maps/api/geocode/json?latlng=${revLat},${revLon}&key=${apiKey}`;
              const gRes = await fetch(gRevUrl);
              const gData = await gRes.json();
              if (gData.status === 'OK' && gData.results?.length) {
                res.statusCode = 200;
                res.setHeader('Content-Type', 'application/json');
                res.end(JSON.stringify({
                  source: 'google',
                  lat: revLat,
                  lon: revLon,
                  label: gData.results[0].formatted_address,
                  results: gData.results
                }));
                return;
              }
            } catch (e) {}
          }
          // 2. Nominatim Reverse Geocode
          try {
            const nomRevUrl = `https://nominatim.openstreetmap.org/reverse?lat=${revLat}&lon=${revLon}&format=json&addressdetails=1`;
            const nomRes = await fetch(nomRevUrl, {
              headers: { 'User-Agent': 'VisionsAi-DigitalTwin/1.0 (observatory@nougen.ai)' }
            });
            if (nomRes.ok) {
              const nomData = await nomRes.json();
              if (nomData && nomData.display_name) {
                res.statusCode = 200;
                res.setHeader('Content-Type', 'application/json');
                res.end(JSON.stringify({
                  source: 'nominatim',
                  lat: revLat,
                  lon: revLon,
                  label: nomData.display_name,
                  results: [{
                    formatted_address: nomData.display_name,
                    geometry: { location: { lat: revLat, lng: revLon } },
                    address_components: Object.entries(nomData.address || {}).map(([k, v]) => ({
                      long_name: v,
                      types: [k]
                    }))
                  }]
                }));
                return;
              }
            }
          } catch (e) {}
        }
      }

      // FORWARD GEOCODING MODE
      if (!query) {
        res.statusCode = 400;
        res.setHeader('Content-Type', 'application/json');
        res.end(JSON.stringify({ error: 'Query parameter q or address is required', result: null }));
        return;
      }

      // 1. Google Geocoding if API key available
      if (apiKey) {
        try {
          const gUrl = `https://maps.googleapis.com/maps/api/geocode/json?address=${encodeURIComponent(query)}&key=${apiKey}`;
          const gRes = await fetch(gUrl);
          const gData = await gRes.json();
          if (gData.status === 'OK' && gData.results?.length) {
            const item = gData.results[0];
            res.statusCode = 200;
            res.setHeader('Content-Type', 'application/json');
            res.end(JSON.stringify({
              source: 'google',
              lat: item.geometry.location.lat,
              lon: item.geometry.location.lng,
              label: item.formatted_address,
              types: item.types || ['locality'],
              viewport: item.geometry.bounds || item.geometry.viewport || null,
              results: gData.results
            }));
            return;
          }
        } catch (e) {
          // fallback
        }
      }

      // 2. Photon Geocoder (Fast, exact, and handles street numbers & zip codes globally)
      try {
        const pUrl = `https://photon.komoot.io/api/?q=${encodeURIComponent(query)}&limit=1`;
        const pRes = await fetch(pUrl, { headers: { 'User-Agent': 'VisionsAi/1.0' } });
        if (pRes.ok) {
          const pData = await pRes.json();
          if (pData.features?.length > 0) {
            const feat = pData.features[0];
            const coords = feat.geometry.coordinates;
            const props = feat.properties || {};
            const label = [props.name, props.street, props.city, props.state, props.postcode, props.country].filter(Boolean).join(', ');
            const typeVal = props.type || props.osm_value || 'locality';
            let viewport = null;
            if (Array.isArray(props.extent) && props.extent.length === 4) {
              viewport = {
                southwest: { lat: props.extent[3], lng: props.extent[0] },
                northeast: { lat: props.extent[1], lng: props.extent[2] }
              };
            }
            res.statusCode = 200;
            res.setHeader('Content-Type', 'application/json');
            res.end(JSON.stringify({
              source: 'photon',
              lat: coords[1],
              lon: coords[0],
              label: label || query,
              types: [typeVal, typeVal === 'city' ? 'locality' : typeVal],
              viewport,
              results: [{
                formatted_address: label || query,
                geometry: { location: { lat: coords[1], lng: coords[0] }, bounds: viewport }
              }]
            }));
            return;
          }
        }
      } catch (e) {
        // fallback
      }

      // 3. US Census Bureau Geocoder (Authoritative US Street Addresses & Rooftop coordinates)
      try {
        const censusUrl = `https://geocoding.geo.census.gov/geocoder/locations/onelineaddress?address=${encodeURIComponent(query)}&benchmark=Public_AR_Current&format=json`;
        const cRes = await fetch(censusUrl, { headers: { 'User-Agent': 'VisionsAi/1.0' } });
        if (cRes.ok) {
          const cData = await cRes.json();
          const matches = cData?.result?.addressMatches;
          if (Array.isArray(matches) && matches.length > 0) {
            const match = matches[0];
            const cLon = match.coordinates?.x;
            const cLat = match.coordinates?.y;
            if (Number.isFinite(cLat) && Number.isFinite(cLon)) {
              res.statusCode = 200;
              res.setHeader('Content-Type', 'application/json');
              res.end(JSON.stringify({
                source: 'census',
                lat: cLat,
                lon: cLon,
                label: match.matchedAddress || query,
                types: ['street_address', 'premise'],
                viewport: {
                  southwest: { lat: cLat - 0.005, lng: cLon - 0.005 },
                  northeast: { lat: cLat + 0.005, lng: cLon + 0.005 }
                },
                results: [{
                  formatted_address: match.matchedAddress || query,
                  geometry: { location: { lat: cLat, lng: cLon } }
                }]
              }));
              return;
            }
          }
        }
      } catch (e) {
        // fallback
      }

      // 4. OpenStreetMap Nominatim Geocoder
      try {
        const nUrl = `https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(query)}&format=json&addressdetails=1&limit=1`;
        const nRes = await fetch(nUrl, {
          headers: { 'User-Agent': 'VisionsAi-DigitalTwin/1.0 (observatory@nougen.ai)' }
        });
        if (nRes.ok) {
          const nData = await nRes.json();
          if (nData?.length > 0) {
            const item = nData[0];
            let viewport = null;
            if (Array.isArray(item.boundingbox) && item.boundingbox.length === 4) {
              viewport = {
                southwest: { lat: parseFloat(item.boundingbox[0]), lng: parseFloat(item.boundingbox[2]) },
                northeast: { lat: parseFloat(item.boundingbox[1]), lng: parseFloat(item.boundingbox[3]) }
              };
            }
            const typeVal = item.type || item.addresstype || 'locality';
            res.statusCode = 200;
            res.setHeader('Content-Type', 'application/json');
            res.end(JSON.stringify({
              source: 'nominatim',
              lat: parseFloat(item.lat),
              lon: parseFloat(item.lon),
              label: item.display_name,
              types: [typeVal, typeVal === 'city' ? 'locality' : typeVal],
              viewport,
              results: [{
                formatted_address: item.display_name,
                geometry: { location: { lat: parseFloat(item.lat), lng: parseFloat(item.lon) }, bounds: viewport }
              }]
            }));
            return;
          }
        }
      } catch (e) {
        // fallback
      }

      // 5. Coordinate parser fallback ("lat, lon")
      const coordMatch = query.match(/(-?\d+\.?\d*)[,\s]+(-?\d+\.?\d*)/);
      if (coordMatch) {
        const latVal = parseFloat(coordMatch[1]);
        const lonVal = parseFloat(coordMatch[2]);
        if (Number.isFinite(latVal) && Number.isFinite(lonVal) && Math.abs(latVal) <= 90 && Math.abs(lonVal) <= 180) {
          res.statusCode = 200;
          res.setHeader('Content-Type', 'application/json');
          res.end(JSON.stringify({
            source: 'coordinates',
            lat: latVal,
            lon: lonVal,
            label: `Coordinate (${latVal.toFixed(4)}, ${lonVal.toFixed(4)})`,
            types: ['precise-place'],
            viewport: null,
            results: [{
              formatted_address: `Coordinate (${latVal.toFixed(4)}, ${lonVal.toFixed(4)})`,
              geometry: { location: { lat: latVal, lng: lonVal } }
            }]
          }));
          return;
        }
      }

      res.statusCode = 404;
      res.setHeader('Content-Type', 'application/json');
      res.end(JSON.stringify({ error: 'Location not found', result: null }));
    });

    // Dynamic Sun Times & Solar Ephemeris Route: Pure NOAA solar math (0 external dependencies)
    middlewares.use('/api/suntimes', async (req, res) => {
      if (req.method !== 'GET') {
        res.statusCode = 405;
        res.setHeader('Content-Type', 'application/json');
        res.end(JSON.stringify({ error: 'Method not allowed' }));
        return;
      }
      const requestUrl = new URL(req.url || '', 'http://localhost');
      const siteKey = String(requestUrl.searchParams.get('site') || '').toLowerCase().trim();
      const dateStr = requestUrl.searchParams.get('date') || new Date().toISOString().split('T')[0];
      let lat = parseFloat(requestUrl.searchParams.get('lat'));
      let lon = parseFloat(requestUrl.searchParams.get('lon') || requestUrl.searchParams.get('lng'));
      let tz = parseFloat(requestUrl.searchParams.get('tz'));
      let siteName = 'Custom Location';

      if (siteKey && SAVED_SUN_SITES[siteKey]) {
        const siteInfo = SAVED_SUN_SITES[siteKey];
        lat = siteInfo.lat;
        lon = siteInfo.lon;
        tz = siteInfo.tz;
        siteName = siteInfo.name;
      } else if (!Number.isFinite(lat) || !Number.isFinite(lon)) {
        // Default to Palm Beach if unspecified
        lat = 26.7056;
        lon = -80.0364;
        tz = -4.0;
        siteName = 'Palm Beach Island (Default)';
      }

      if (!Number.isFinite(tz)) {
        // Approximate standard timezone offset from longitude if not supplied
        tz = Math.round(lon / 15);
      }

      const sunTimes = computeSunTimes(dateStr, lat, lon, tz);
      const solarPos = getSolarPosition(new Date(), lat, lon);
      const phaseInfo = getSolarPhase(solarPos.elevation);

      res.statusCode = 200;
      res.setHeader('Content-Type', 'application/json');
      res.end(JSON.stringify({
        success: true,
        site: siteName,
        lat,
        lon,
        timezone_offset: tz,
        date: dateStr,
        times: sunTimes,
        current_solar_position: {
          elevation_degrees: parseFloat(solarPos.elevation.toFixed(2)),
          azimuth_degrees: parseFloat(solarPos.azimuth.toFixed(2)),
          phase: phaseInfo.phase,
          phase_label: phaseInfo.label,
          phase_code: phaseInfo.code,
        },
        saved_sites: Object.keys(SAVED_SUN_SITES),
      }));
    });
  }

  return {
    name: 'google-places-context-proxy',
    configureServer(server) {
      install(server.middlewares);
    },
    configurePreviewServer(server) {
      install(server.middlewares);
    },
  };
}
