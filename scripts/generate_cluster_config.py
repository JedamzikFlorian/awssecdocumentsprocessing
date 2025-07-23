import os
import json
from dotenv import load_dotenv

# .env laden
load_dotenv()

# Werte aus .env lesen
ACCOUNT_ID = os.getenv("AWS_ACCOUNT_ID")
REGION = os.getenv("REGION")
S3_BUCKET = os.getenv("S3_BUCKET")
ROLE_ARN = os.getenv("SAGEMAKER_EXECUTION_ROLE")

# Cluster-Konfiguration
cluster_config = {
    "ClusterName": "llama-sec-cluster",
    "InstanceGroups": [
        {
            "InstanceGroupName": "controller-group",
            "InstanceType": "ml.m5.large",
            "InstanceCount": 1,
            "LifeCycleConfig": {
                "SourceS3Uri": f"s3://{S3_BUCKET}/scripts/",
                "OnCreate": "lifecycle.sh"
            },
            "ExecutionRole": ROLE_ARN,
            "ThreadsPerCore": 2,
        },
        {
            "InstanceGroupName": "worker-group",
            "InstanceType": "ml.g5.xlarge",
            "InstanceCount": 1,
            "LifeCycleConfig": {
                "SourceS3Uri": f"s3://{S3_BUCKET}/scripts/",
                "OnCreate": "lifecycle.sh"
            },
            "ExecutionRole": ROLE_ARN,
            "ThreadsPerCore": 2,
        }
    ],
    "NodeRecovery": "Automatic"
}

# Zielpfad anpassen
output_path = os.path.join("configs", "cluster-config.json")

# JSON schreiben
with open(output_path, "w") as f:
    json.dump(cluster_config, f, indent=2)

print(f"✅ cluster-config.json erfolgreich erzeugt unter: {output_path}")
