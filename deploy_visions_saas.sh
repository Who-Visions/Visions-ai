#!/bin/bash

# ==============================================================================
# VISIONS AI - SAAS INFRASTRUCTURE DEPLOYMENT SCRIPT
# Refactored from Yuki AI for Endless Duality Project
# Project ID: endless-duality-480201-t3
# ==============================================================================

PROJECT_ID="endless-duality-480201-t3"
REGION="us-central1"

echo "🚀 Deploying Visions AI SaaS Infrastructure to $PROJECT_ID..."

# Ensure we are using the correct project and account
gcloud config set project $PROJECT_ID --quiet
gcloud config set account whoentertains@gmail.com --quiet

# ============================================
# TIER 1: CREATE SERVICE ACCOUNTS FOR EACH TIER
# ============================================
echo "👤 [TIER 1] Creating Service Accounts..."
gcloud iam service-accounts create visions-tier-free --display-name="Visions Free Tier"
gcloud iam service-accounts create visions-tier-basic --display-name="Visions Basic Tier"
gcloud iam service-accounts create visions-tier-pro --display-name="Visions Pro Tier"
gcloud iam service-accounts create visions-tier-business --display-name="Visions Business Tier"
gcloud iam service-accounts create visions-tier-enterprise --display-name="Visions Enterprise Tier"

# ============================================
# TIER 2: SET RATE LIMITS PER TIER (API GATEWAY)
# ============================================
echo "⛩️  [TIER 2] Configuring API Gateway & Quotas..."
gcloud services enable endpoints.googleapis.com
gcloud services enable apigateway.googleapis.com

# Create OpenAPI spec with limits
cat > visions-api.yaml << EOF
swagger: "2.0"
info:
  title: Visions-AI API
  description: Tier-based AI API for Visions SaaS
  version: "1.0.0"
host: "visions-ai.endpoints.${PROJECT_ID}.cloud.goog"
paths:
  "/v1/generate":
    post:
      operationId: generate
      x-google-quota:
        metricCosts:
          "free-tier": 1
          "basic-tier": 1
          "pro-tier": 1
      responses:
        200:
          description: Success
quota:
  limits:
    - name: free-limit
      metric: free-tier
      unit: 1/min/{project}
      values:
        STANDARD: 10
    - name: basic-limit
      metric: basic-tier
      unit: 1/min/{project}
      values:
        STANDARD: 60
    - name: pro-limit
      metric: pro-tier
      unit: 1/min/{project}
      values:
        STANDARD: 300
    - name: business-limit
      metric: business-tier
      unit: 1/min/{project}
      values:
        STANDARD: 1000
    - name: enterprise-limit
      metric: enterprise-tier
      unit: 1/min/{project}
      values:
        STANDARD: 10000
EOF
echo "   ✅ Generated visions-api.yaml"

# ============================================
# TIER 3: SECURE PAYMENT WEBHOOKS (SECRET MANAGER)
# ============================================
echo "🔐 [TIER 3] Setting up Secrets..."
gcloud services enable secretmanager.googleapis.com

# Placeholder values - USER MUST UPDATE THESE
echo "whsec_PLACEHOLDER_SECRET" | gcloud secrets create visions-stripe-webhook \
  --replication-policy="automatic" --data-file=- || echo "Secret visions-stripe-webhook likely exists."

echo "sk_live_PLACEHOLDER_KEY" | gcloud secrets create visions-stripe-key \
  --replication-policy="automatic" --data-file=- || echo "Secret visions-stripe-key likely exists."

# Grant service accounts access to secrets (Example for Pro Tier)
SERVICES_EMAIL="visions-tier-pro@${PROJECT_ID}.iam.gserviceaccount.com"
gcloud secrets add-iam-policy-binding visions-stripe-webhook \
  --member="serviceAccount:${SERVICES_EMAIL}" \
  --role="roles/secretmanager.secretAccessor"

# ============================================
# TIER 4: CLOUD ARMOR PROTECTION
# ============================================
echo "🛡️  [TIER 4] Deploying Cloud Armor Policies..."
gcloud compute security-policies create visions-tier-policy \
  --description="Rate limits and WAF for subscription tiers" || echo "Policy exists."

# Rule 1000: Throttle Free Tier Abuse
gcloud compute security-policies rules create 1000 \
  --security-policy=visions-tier-policy \
  --expression="request.headers['x-tier'] == 'free'" \
  --action="rate_based_ban" \
  --rate-limit-threshold-count=10 \
  --rate-limit-threshold-interval-sec=60 \
  --ban-duration-sec=3600 \
  --conform-action=allow \
  --exceed-action="deny(429)" || echo "Rule 1000 likely exists or needs update."

# ============================================
# TIER 5: VPC NETWORK ISOLATION
# ============================================
echo "🌐 [TIER 5] Configuring VPC & Serverless Connector..."
gcloud services enable vpcaccess.googleapis.com

gcloud compute networks create visions-vpc --subnet-mode=custom || echo "Visions VPC exists."

gcloud compute networks subnets create visions-subnet \
  --network=visions-vpc --range=10.0.0.0/24 --region=$REGION || echo "Subnet exists."

gcloud compute networks vpc-access connectors create visions-connector \
  --region=$REGION --range=10.8.0.0/28 --network=visions-vpc || echo "Connector exists."

# ============================================
# TIER 6: SECURE FIREBASE RULES
# ============================================
echo "🔥 [TIER 6] Generating Firestore Security Rules..."
cat > firestore.rules << EOF
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    match /users/{userId} {
      allow read, write: if request.auth != null && request.auth.uid == userId;
    }
    match /subscriptions/{subId} {
      allow read: if request.auth != null && resource.data.userId == request.auth.uid;
      allow write: if false; // Only server via webhook
    }
    match /usage/{userId} {
      allow read: if request.auth != null && request.auth.uid == userId;
      allow write: if false; // Server only
    }
  }
}
EOF
echo "   ✅ Generated firestore.rules"

# ============================================
# TIER 7: MONITORING & ALERTS
# ============================================
echo "💰 [TIER 7] Setting Budget Alerts..."
gcloud services enable budgets.googleapis.com

BILLING_ACCOUNT=$(gcloud billing accounts list --format="value(name)" | head -1)
if [ -z "$BILLING_ACCOUNT" ]; then
    echo "   ⚠️  No Billing Account found/accessible. Skipping Budget creation."
else
    gcloud billing budgets create \
      --billing-account=$BILLING_ACCOUNT \
      --display-name="Visions-AI Budget" \
      --budget-amount=10000USD \
      --threshold-rules=percent=50,percent=80,percent=100 || echo "Budget likely exists."
fi

# ============================================
# TIER 8: SECURITY COMMAND CENTER
# ============================================
echo "🚨 [TIER 8] Enabling Security Command Center..."
gcloud services enable securitycenter.googleapis.com

echo ""
echo "=========================================="
echo "✅ VISIONS AI SAAS SECURITY DEPLOYMENT COMPLETE"
echo "=========================================="
echo ""
echo "TIER LIMITS CONFIGURED:"
echo "• Free ($0): 10 requests/min"
echo "• Basic ($8): 60 requests/min"
echo "• Pro ($20): 300 requests/min"
echo "• Business ($50): 1000 requests/min"
echo "• Enterprise ($200): 10000 requests/min"
echo ""
echo "NEXT STEPS:"
echo "1. Update secrets 'visions-stripe-webhook' and 'visions-stripe-key' with real values."
echo "2. Deploy the API Gateway config: gcloud api-gateway api-configs create ..."
echo "3. Deploy Firebase rules: firebase deploy --only firestore:rules"
