/**
 * VISIONS AI - TIERED RATE LIMITER
 * Refactored for 5 Tiers: Free ($0), Basic ($8), Pro ($20), Business ($50), Enterprise ($200)
 * Uses Firestore for counter tracking.
 */
const { Firestore } = require('@google-cloud/firestore');
const firestore = new Firestore();

const TIER_LIMITS = {
  'free': 10,        // 10 requests per minute
  'basic': 30,       // 30 requests per minute
  'pro': 100,        // 100 requests per minute (Popular)
  'business': 500,   // 500 requests per minute (Power User)
  'enterprise': 1000 // 1000 requests per minute (Teams)
};

exports.checkRateLimit = async (req, res) => {
  const userId = req.headers['x-user-id'];
  const tier = req.headers['x-tier'] || 'free';
  const limit = TIER_LIMITS[tier.toLowerCase()] || 10;

  if (!userId) {
    return res.status(400).json({ error: 'Missing x-user-id header' });
  }

  const now = Date.now();
  const usageRef = firestore.collection('visions_usage').doc(`${userId}_${tier}`);

  try {
    const usageDoc = await usageRef.get();
    let count = 0;

    if (usageDoc.exists) {
      const data = usageDoc.data();
      // Window reset logic (1 minute)
      if (now - data.lastRequest > 60000) {
        count = 0;
      } else {
        count = data.count || 0;
      }
    }

    if (count >= limit) {
      return res.status(429).json({
        error: 'Rate limit exceeded',
        message: `Your current ${tier} plan limit is ${limit} requests per minute. Upgrade at visions.ai/pricing to increase this.`,
        tier,
        limit,
        resetInSeconds: Math.ceil((60000 - (now % 60000)) / 1000)
      });
    }

    // Atomic update
    await usageRef.set({
      count: count + 1,
      lastRequest: now
    }, { merge: true });

    res.json({
      allowed: true,
      tier,
      remaining: limit - count - 1,
      limit
    });

  } catch (err) {
    console.error("Rate limit check failed", err);
    // Fail open
    res.json({ allowed: true, remaining: 1, warning: "Rate limit service error" });
  }
};
