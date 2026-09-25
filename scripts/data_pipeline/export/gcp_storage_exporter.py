"""
GCP Cloud Storage Exporter and Packaging Utility for Mobile SQLite Database.
Generates compressed bundles (Gzip/Zstandard), calculates SHA256 checksums,
and generates release metadata for Google Cloud Storage distribution.
"""

import os
import gzip
import hashlib
import json
from datetime import datetime, timezone
from typing import Dict, Any, Optional

class GcpStorageExporter:
    """
    Packages and exports the processed SQLite database for Google Cloud Storage.
    """

    def __init__(self, gcs_bucket: str = "pastoral-workstation-assets"):
        self.gcs_bucket = gcs_bucket

    def calculate_sha256(self, file_path: str) -> str:
        """Calculates SHA256 checksum of a file."""
        hasher = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                hasher.update(chunk)
        return hasher.hexdigest()

    def compress_db(self, db_path: str, output_gz_path: Optional[str] = None) -> str:
        """Compresses the SQLite DB using high-ratio gzip for mobile deployment."""
        if not output_gz_path:
            output_gz_path = f"{db_path}.gz"

        print(f"Compressing database: {db_path} -> {output_gz_path}...")
        with open(db_path, "rb") as f_in:
            with gzip.open(output_gz_path, "wb", compresslevel=9) as f_out:
                for chunk in iter(lambda: f_in.read(65536), b""):
                    f_out.write(chunk)
                    
        orig_size = os.path.getsize(db_path)
        comp_size = os.path.getsize(output_gz_path)
        ratio = (1.0 - (comp_size / orig_size)) * 100.0
        print(f"Compression complete: {orig_size:,} bytes -> {comp_size:,} bytes ({ratio:.1f}% reduction)")
        return output_gz_path

    def generate_release_manifest(
        self,
        db_path: str,
        compressed_path: str,
        version: str = "1.0.0",
        notes: str = "Initial release of 8 Pastoral Commentaries with Deep Cross-References and Entity Chains"
    ) -> Dict[str, Any]:
        """Generates version manifest JSON for Flutter client auto-updater."""
        raw_sha256 = self.calculate_sha256(db_path)
        compressed_sha256 = self.calculate_sha256(compressed_path)
        
        manifest = {
            "version": version,
            "release_date": datetime.now(timezone.utc).isoformat(),
            "target_app": "Biblical Exegesis & Commentary Pastoral Workstation",
            "database_name": os.path.basename(db_path),
            "uncompressed_size_bytes": os.path.getsize(db_path),
            "uncompressed_sha256": raw_sha256,
            "compressed_file_name": os.path.basename(compressed_path),
            "compressed_size_bytes": os.path.getsize(compressed_path),
            "compressed_sha256": compressed_sha256,
            "commentaries_supported": [
                "OXFORD", "WESLEY", "HOKMA", "GRAND", 
                "CHARISMA", "MATTHEW_HENRY", "BAKER", "ESV_EXPOSITORY"
            ],
            "theological_features": [
                "Deep Cross-References & Entity Chain-References (Full-Text)",
                "Strong's Hebrew/Greek Concordance Integration",
                "TSK Cross References (~340,000 links)",
                "Full-Text Search (SQLite FTS5 Unicode61)"
            ],
            "gcs_uri": f"gs://{self.gcs_bucket}/databases/{os.path.basename(compressed_path)}",
            "release_notes": notes
        }

        manifest_path = os.path.join(os.path.dirname(compressed_path), "release_manifest.json")
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, ensure_ascii=False, indent=2)

        print(f"Release manifest saved: {manifest_path}")
        return manifest

    def generate_gcp_upload_script(self, compressed_path: str, manifest_path: str) -> str:
        """Generates a bash/powershell script to deploy files to GCP Cloud Storage."""
        comp_file = os.path.basename(compressed_path)
        manifest_file = os.path.basename(manifest_path)
        script_content = f"""# GCP Cloud Storage Deployment Script
# Bucket: gs://{self.gcs_bucket}/

echo "1. Uploading compressed SQLite database to GCP..."
gcloud storage cp "{compressed_path}" "gs://{self.gcs_bucket}/databases/{comp_file}" --cache-control="public, max-age=31536000"

echo "2. Uploading release manifest to GCP..."
gcloud storage cp "{manifest_path}" "gs://{self.gcs_bucket}/databases/{manifest_file}" --cache-control="no-cache"

echo "3. Setting public read access (if distributed to pastor tablet without auth)..."
gcloud storage objects add-iam-policy-binding "gs://{self.gcs_bucket}/databases/{comp_file}" --member=allUsers --role=roles/storage.objectViewer

echo "Deployment complete! Mobile devices can download from: https://storage.googleapis.com/{self.gcs_bucket}/databases/{comp_file}"
"""
        script_file = os.path.join(os.path.dirname(compressed_path), "deploy_to_gcp.sh")
        with open(script_file, "w", encoding="utf-8") as f:
            f.write(script_content)
        return script_file
