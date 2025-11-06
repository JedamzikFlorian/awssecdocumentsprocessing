# Implementation Plan

## Overview

This implementation plan breaks down the SEC document table extraction pipeline into discrete, manageable coding tasks. Each task builds incrementally on previous work, focusing on the minimal viable implementation for learning purposes.

---

## Tasks

- [x] 1. Set up local development environment




  - Install Python dependencies (PyMuPDF, boto3, python-dotenv)
  - Create virtual environment
  - Set up .env file for AWS configuration
  - Verify AWS CLI is configured
  - _Requirements: All requirements (foundational)_

- [x] 2. Implement PDF to image conversion script




  - [x] 2.1 Fix typo in `docs_to_images.py` (connvert → convert)

    - Correct function name spelling
    - _Requirements: 1.1, 1.2_

  - [ ] 2.2 Add error handling for corrupted PDFs
    - Wrap fitz.open() in try-except block
    - Log errors and continue processing

    - _Requirements: 1.5_
  - [ ] 2.3 Add validation for output directory creation
    - Verify directory was created successfully
    - _Requirements: 1.3_

- [ ] 3. Implement training data JSON generation
  - [ ] 3.1 Update `generate_training_data_json.py` to match LLaMA-Factory format
    - Change output format from simple dict to messages array format
    - Add system/user/assistant message structure
    - Include proper image path handling
    - _Requirements: 3.2, 3.3, 3.4_
  - [ ] 3.2 Add validation for missing HTML files
    - Log warnings for images without HTML
    - Skip entries gracefully
    - _Requirements: 3.6_
  - [ ] 3.3 Add HTML validation
    - Check for well-formed table tags
    - Log validation errors
    - _Requirements: 2.4_

- [ ] 4. Update CDK infrastructure stack for minimal setup
  - [ ] 4.1 Modify VPC configuration to use single AZ
    - Change max_azs from 2 to 1
    - Remove public subnet configuration
    - Keep only private subnet
    - _Requirements: 4.1_
  - [ ] 4.2 Add S3 VPC Endpoint
    - Create VPC endpoint for S3 (Gateway type)
    - Associate with private subnet route table
    - _Requirements: 4.1_
  - [ ] 4.3 Consolidate S3 buckets into single bucket
    - Remove model_bucket
    - Keep only data_bucket with organized prefixes
    - Update bucket name to `sec-documents-{account}-{region}`
    - _Requirements: 4.2_
  - [ ] 4.4 Update IAM role to minimal permissions
    - Replace managed policies with inline policy
    - Grant only S3 GetObject/PutObject/ListBucket on specific bucket
    - Grant minimal SageMaker permissions
    - _Requirements: 4.3_
  - [ ] 4.5 Remove versioning and encryption configurations
    - Set versioned=False
    - Remove encryption config (use default)
    - _Requirements: 4.6_
  - [ ] 4.6 Update CDK outputs
    - Add SubnetId output
    - Change DataBucketName to BucketName
    - Remove ModelBucketName
    - _Requirements: 4.5_

- [ ] 5. Simplify lifecycle script
  - [ ] 5.1 Remove unnecessary environment variables
    - Remove EFA, NCCL, PYTHONUNBUFFERED exports
    - Keep only essential setup
    - _Requirements: 6.5_
  - [ ] 5.2 Remove logging configuration
    - Remove tee and logger setup
    - Use simple echo statements
    - _Requirements: 6.5_
  - [ ] 5.3 Simplify package installation
    - Remove curl, unzip from apt install
    - Keep only git and python3-pip
    - _Requirements: 6.2_

- [ ] 6. Update cluster configuration for single worker
  - [ ] 6.1 Modify `generate_cluster_config.py` to remove controller group
    - Keep only worker-group in InstanceGroups
    - Update cluster name to "sec-table-extraction-minimal"
    - _Requirements: 5.1_
  - [ ] 6.2 Update ThreadsPerCore to 1
    - Change from 2 to 1 for cost savings
    - _Requirements: 5.1_
  - [ ] 6.3 Update environment variable references
    - Change S3_BUCKET references to single bucket
    - _Requirements: 5.5_

- [ ] 7. Create S3 upload script
  - [ ] 7.1 Write `upload_to_s3.py` script
    - Upload preprocessed images to s3://{bucket}/data/images/
    - Upload training JSON to s3://{bucket}/data/training.json
    - Upload lifecycle script to s3://{bucket}/scripts/lifecycle.sh
    - Use boto3 for uploads
    - _Requirements: 10.1, 10.2, 10.3_
  - [ ] 7.2 Add progress indication
    - Print upload status for each file
    - _Requirements: 10.4_

- [ ] 8. Create training configuration file
  - [ ] 8.1 Write LLaMA-Factory training config YAML
    - Set model_name_or_path to Qwen/Qwen2-VL-7B-Instruct
    - Configure QLoRA parameters (4-bit, rank=8)
    - Set minimal batch size and epochs
    - Configure S3 output directory
    - _Requirements: 7.1, 7.2, 7.3, 7.5_
  - [ ] 8.2 Create dataset configuration JSON
    - Define dataset name and path
    - Set image resolution to 512
    - Configure max_length to 1024
    - _Requirements: 7.3_

- [ ] 9. Create training execution script
  - [ ] 9.1 Write `train.sh` script for HyperPod
    - Source environment setup
    - Navigate to LLaMA-Factory directory
    - Execute training with config file
    - Save checkpoints to S3
    - _Requirements: 7.4, 7.5, 7.6_
  - [ ] 9.2 Add basic error handling
    - Check if LLaMA-Factory is installed
    - Verify GPU availability
    - _Requirements: 7.1_

- [ ] 10. Create model download script
  - [ ] 10.1 Write `download_model.py` script
    - Download final checkpoint from S3 to local
    - Download adapter weights
    - Preserve directory structure
    - _Requirements: 8.1_

- [ ] 11. Create simple evaluation script
  - [ ] 11.1 Write `evaluate_simple.py` script
    - Load fine-tuned model with adapters
    - Process 2-3 test images
    - Generate HTML predictions
    - Save predictions to files
    - _Requirements: 8.2, 8.3_
  - [ ] 11.2 Add visual comparison helper
    - Generate side-by-side HTML for ground truth vs prediction
    - _Requirements: 8.4_

- [ ] 12. Create deployment documentation
  - [ ] 12.1 Write step-by-step deployment guide
    - Document CDK deployment commands
    - Document S3 upload process
    - Document HyperPod cluster creation
    - Document training execution
    - Document model download and evaluation
  - [ ] 12.2 Add troubleshooting section
    - Common errors and solutions
    - Cost monitoring tips
    - Cleanup instructions

- [ ] 13. Create cleanup script
  - [ ] 13.1 Write `cleanup.sh` script
    - Delete HyperPod cluster
    - Optionally empty and delete S3 bucket
    - Delete CDK stack
    - Verify all resources are removed

