# Visions AI Cloud Run Deployment Script
$PROJECT_ID = "endless-duality-480201-t3"
$SERVICE_NAME = "visions-agent-v3"
$REGION = "us-central1"
$IMAGE_TAG = "gcr.io/$PROJECT_ID/$SERVICE_NAME"

Write-Host "🚀 Starting Cloud Run Deployment: $SERVICE_NAME" -ForegroundColor Cyan

# 1. Build and Push using Cloud Build (No local Docker needed)
Write-Host "🛠️ Building container in Cloud Build..." -ForegroundColor Yellow
gcloud builds submit --tag $IMAGE_TAG --project $PROJECT_ID

# 2. Deploy to Cloud Run
Write-Host "🚢 Deploying to Cloud Run..." -ForegroundColor Yellow
gcloud run deploy $SERVICE_NAME `
    --image $IMAGE_TAG `
    --platform managed `
    --region $REGION `
    --project $PROJECT_ID `
    --allow-unauthenticated `
    --memory 2Gi `
    --cpu 1 `
    --timeout 300 `
    --set-env-vars "VERTEX_PROJECT_ID=$PROJECT_ID,VERTEX_LOCATION=$REGION"

Write-Host "✅ Deployment Successful!" -ForegroundColor Green
gcloud run services describe $SERVICE_NAME --platform managed --region $REGION --project $PROJECT_ID --format 'value(status.url)'
