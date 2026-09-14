import { test } from 'node:test';
import assert from 'node:assert/strict';
import * as Cesium from 'cesium';
import { searchAndFlyTo } from './locations.js';

function stubViewer() {
  const flights = [];
  return {
    flights,
    scene: { globe: null, canvas: { clientWidth: 0, clientHeight: 0 } },
    camera: {
      positionCartographic: {
        longitude: Cesium.Math.toRadians(-80.053),
        latitude: Cesium.Math.toRadians(26.715),
        height: 1200,
      },
      cancelFlight() {},
      flyTo(options) { flights.push(options); },
      flyToBoundingSphere(sphere, options) { flights.push({ sphere, ...options }); },
      lookAt() {},
      lookAtTransform() {},
    },
  };
}

test('searchAndFlyTo resolves West Palm Beach Florida without Google API Key via Photon/OSM fallback', async () => {
  const viewer = stubViewer();
  const priorWindow = globalThis.window;
  try {
    delete globalThis.window;
    const res = await searchAndFlyTo(viewer, 'West Palm Beach Florida');
    assert.ok(res, 'Expected a resolved location result');
    assert.match(res.label, /West Palm Beach/i);
    assert.ok(viewer.flights.length > 0, 'Expected viewer flight to be scheduled');
  } finally {
    if (priorWindow !== undefined) globalThis.window = priorWindow;
  }
});
