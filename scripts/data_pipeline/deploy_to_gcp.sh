# GCP Cloud Storage Deployment Script
# Bucket: gs://pastoral-workstation-assets/

echo "1. Uploading compressed SQLite database to GCP..."
gcloud storage cp "C:\Users\packr\Desktop\성경주혜주석\scripts\data_pipeline\bible_pastoral_core.db.gz" "gs://pastoral-workstation-assets/databases/bible_pastoral_core.db.gz" --cache-control="public, max-age=31536000"

echo "2. Uploading release manifest to GCP..."
gcloud storage cp "C:\Users\packr\Desktop\성경주혜주석\scripts\data_pipeline\release_manifest.json" "gs://pastoral-workstation-assets/databases/release_manifest.json" --cache-control="no-cache"

echo "3. Setting public read access (if distributed to pastor tablet without auth)..."
gcloud storage objects add-iam-policy-binding "gs://pastoral-workstation-assets/databases/bible_pastoral_core.db.gz" --member=allUsers --role=roles/storage.objectViewer

echo "Deployment complete! Mobile devices can download from: https://storage.googleapis.com/pastoral-workstation-assets/databases/bible_pastoral_core.db.gz"
