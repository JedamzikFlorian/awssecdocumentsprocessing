# Requirements Document

## Introduction

This project implements a minimal learning/experimentation pipeline for extracting structured tables from PDF documents using multimodal AI. The system fine-tunes the Qwen2-VL-7B-Instruct vision-language model using LLaMA-Factory on AWS SageMaker HyperPod to convert table images into HTML format. This is a proof-of-concept setup focused on understanding the technology with minimal AWS costs.

## Glossary

- **System**: The SEC Document Table Extraction Pipeline
- **HyperPod**: AWS SageMaker HyperPod distributed training cluster
- **VLM**: Vision Language Model (Qwen2-VL-7B-Instruct)
- **LLaMA-Factory**: Open-source framework for efficient LLM fine-tuning
- **Ground Truth**: Manually annotated HTML representations of table structures
- **Training Dataset**: Collection of image-HTML pairs in LLaMA-Factory JSON format
- **Fine-tuned Model**: QLoRA-adapted VLM specialized for financial table extraction
- **User**: Data scientist or ML engineer operating the pipeline

## Requirements

### Requirement 1: Data Preprocessing Pipeline

**User Story:** As a User, I want to convert PDF financial reports into individual page images, so that I can prepare visual inputs for the VLM training process.

#### Acceptance Criteria

1. WHEN the User provides a PDF file path and output directory, THE System SHALL convert each PDF page into a PNG image at 200 DPI resolution
2. THE System SHALL save each page image with sequential naming format "page_N.png" where N is the page number
3. THE System SHALL create the output directory if it does not exist
4. WHEN conversion completes, THE System SHALL log the output path for each saved image
5. IF the PDF file is corrupted or unreadable, THEN THE System SHALL raise an error with a descriptive message

### Requirement 2: Ground Truth Annotation Workflow

**User Story:** As a User, I want to create HTML annotations for table images, so that I can build training data with accurate structure labels.

#### Acceptance Criteria

1. THE System SHALL provide a directory structure where HTML files correspond to image files by page number
2. WHEN the User creates an HTML file at "data/html_tables/page_N.html", THE System SHALL associate it with "data/preprocessed/[company]/page_N.png"
3. THE System SHALL support HTML table elements including colspan, rowspan, and nested structures
4. THE System SHALL validate that HTML files contain well-formed table markup
5. WHERE the User has multiple companies, THE System SHALL organize images in company-specific subdirectories

### Requirement 3: Training Data Generation

**User Story:** As a User, I want to convert image-HTML pairs into LLaMA-Factory JSON format, so that I can train the VLM with properly structured data.

#### Acceptance Criteria

1. THE System SHALL scan the preprocessed directory for all PNG images
2. WHEN an image has a corresponding HTML file, THE System SHALL create a JSON training entry
3. THE System SHALL format each entry with fields: "messages" containing system/user/assistant roles, "images" array with file paths
4. THE System SHALL use the prompt "Extract the table structure from this image and output as HTML"
5. THE System SHALL save the complete dataset as a single JSON file compatible with LLaMA-Factory multimodal format
6. IF an image lacks a corresponding HTML file, THEN THE System SHALL skip that image and log a warning

### Requirement 4: AWS Infrastructure Provisioning

**User Story:** As a User, I want to deploy minimal AWS infrastructure using CDK, so that I have basic resources for training with lowest possible costs.

#### Acceptance Criteria

1. THE System SHALL create a VPC with private subnets and VPC endpoints for S3 access without NAT Gateway
2. THE System SHALL provision one S3 bucket for both training data and model artifacts
3. THE System SHALL create an IAM role with minimal required permissions for SageMaker and S3
4. THE System SHALL configure a security group allowing outbound traffic for HyperPod
5. THE System SHALL output the VPC ID, bucket name, role ARN, and security group ID after deployment
6. THE System SHALL NOT include monitoring, logging, or security features beyond basic IAM

### Requirement 5: HyperPod Cluster Configuration

**User Story:** As a User, I want to configure a minimal SageMaker HyperPod cluster, so that I can run basic training experiments with one GPU.

#### Acceptance Criteria

1. THE System SHALL define a cluster with one worker instance (ml.g5.xlarge) without a separate controller
2. THE System SHALL configure basic node recovery
3. THE System SHALL reference a lifecycle script stored in S3 for instance initialization
4. THE System SHALL use the IAM execution role created by the infrastructure stack
5. THE System SHALL generate cluster configuration from environment variables (account ID, region, S3 bucket, role ARN)

### Requirement 6: Environment Setup via Lifecycle Script

**User Story:** As a User, I want HyperPod instances to automatically install dependencies, so that the training environment is ready without manual intervention.

#### Acceptance Criteria

1. WHEN a HyperPod instance starts, THE System SHALL execute the lifecycle script
2. THE System SHALL install system packages: git, python3-pip
3. THE System SHALL clone the LLaMA-Factory repository to /opt/llama-factory
4. THE System SHALL install Python dependencies from LLaMA-Factory requirements.txt
5. THE System SHALL verify GPU accessibility with nvidia-smi

### Requirement 7: Model Fine-tuning with QLoRA

**User Story:** As a User, I want to fine-tune Qwen2-VL-7B-Instruct using QLoRA on HyperPod, so that I can learn how the training process works.

#### Acceptance Criteria

1. THE System SHALL load the base Qwen2-VL-7B-Instruct model from Hugging Face
2. THE System SHALL apply 4-bit quantization using QLoRA for memory efficiency
3. THE System SHALL use the training dataset JSON file from S3
4. THE System SHALL run training on a single GPU
5. THE System SHALL save model checkpoints to S3 at regular intervals
6. WHEN training completes, THE System SHALL save the final adapter weights to S3

### Requirement 8: Model Evaluation

**User Story:** As a User, I want to evaluate the fine-tuned model on test data, so that I can see if the training worked.

#### Acceptance Criteria

1. THE System SHALL load the fine-tuned model with adapter weights
2. THE System SHALL process test images and generate HTML predictions
3. THE System SHALL save prediction outputs as HTML files for visual inspection
4. THE System SHALL provide a simple comparison between base model and fine-tuned model outputs

### Requirement 9: Model Deployment with vLLM (Optional)

**User Story:** As a User, I want to optionally test the fine-tuned model with vLLM locally, so that I can see how inference works.

#### Acceptance Criteria

1. THE System SHALL provide a script to load the fine-tuned model locally with vLLM
2. THE System SHALL accept image inputs and return HTML predictions
3. THE System SHALL run on a local machine or EC2 instance with GPU

### Requirement 10: Data Upload and Synchronization

**User Story:** As a User, I want to upload training data to S3, so that HyperPod instances can access it during training.

#### Acceptance Criteria

1. THE System SHALL upload all preprocessed images to the S3 bucket
2. THE System SHALL upload the training dataset JSON file to S3
3. THE System SHALL upload the lifecycle script to S3
4. THE System SHALL preserve directory structure when uploading
