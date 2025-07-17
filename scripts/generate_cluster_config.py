from dotenv import load_dotenv
import os
import json

load_dotenv()

config = {
  "ClusterName": "llama-sec-cluster",
  "InstanceGroups": [
    {
      "InstanceGroupName": "controller-group",
      "InstanceType": "ml.m5.large",
      "InstanceCount": 1,
      "LifeCycleConfig": {
        "SourceS3Uri": f"s3://{os.getenv('S3_BUCKET')}/scripts/lifecycle.sh",
        "OnCreate": "RUN"
      },
      "ExecutionRole": os.getenv("SAGEMAKER_EXECUTION_ROLE")
    },
    {
      "InstanceGroupName": "worker-group",
      "InstanceType": "ml.g5.xlarge",
      "InstanceCount": 1,
      "LifeCycleConfig": {
        "SourceS3Uri": f"s3://{os.getenv('S3_BUCKET')}/scripts/lifecycle.sh",
        "OnCreate": "RUN"
      },
      "ExecutionRole": os.getenv("SAGEMAKER_EXECUTION_ROLE")
    }
  ]
}

output_dir = "configs"
os.makedirs(output_dir, exist_ok=True)
with open(os.path.join(output_dir, "cluster-config.json"), "w") as f:
    json.dump(config, f, indent=2)

print("✅ cluster-config.json erfolgreich generiert!")
