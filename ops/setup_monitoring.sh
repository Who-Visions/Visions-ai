#!/bin/bash
# Set up alert policies for IAM policy changes

# Ensure you are authenticated or running in an environment with appropriate permissions
# Usage: ./setup_monitoring.sh <email_address>

EMAIL=${1:-"dave@whovisions.com"} # Default email if not provided

echo "Setting up IAM Policy Change Alert for $EMAIL..."

gcloud alpha monitoring policies create \
  --notification-channels="email:$EMAIL" \
  --display-name="IAM Policy Changes" \
  --condition-display-name="IAM Modified" \
  --condition-threshold-value=0 \
  --condition-threshold-duration=0s \
  --filter='resource.type="global" AND log_name="projects/'$GOOGLE_CLOUD_PROJECT'/logs/cloudaudit.googleapis.com%2Factivity" AND protoPayload.methodName="SetIamPolicy"'

echo "Alert policy created."
