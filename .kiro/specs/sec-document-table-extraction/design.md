# Design Document: SEC Document Table Extraction Pipeline

## Overview

This system implements a minimal learning/experimentation pipeline for extracting structured tables from PDF documents using multimodal AI. The architecture is inspired by the AWS blog post "How Apoidea Group enhances visual information extraction from banking documents with multimodal models using LLaMA Factory on Amazon SageMaker HyperPod," but simplified to minimize costs and complexity for learning purposes.

The pipeline consists of four major phases:
1. **Data Preprocessing**: Convert PDF documents to images and create HTML ground truth annotations
2. **Infrastructure Provisioning**: Deploy minimal AWS resources using CDK (VPC with VPC endpoints, S3, IAM)
3. **Training Environment Setup**: Configure minimal SageMaker HyperPod cluster (single GPU)
4. **Model Fine-tuning**: Train Qwen2-VL-7B-Instruct using QLoRA and LLaMA-Factory on single GPU

### Key Design Principles

- **Cost Minimization**: Use smallest viable instance types, VPC endpoints instead of NAT Gateway, single S3 bucket
- **Simplicity**: No monitoring, no CloudWatch, no X-Ray, no Secrets Manager, no production features
- **Learning Focus**: Understand the core training pipeline without production overhead
- **Multimodal Approach**: Use vision-language models to process both visual layout and textual content
- **Efficient Fine-tuning**: Apply QLoRA (4-bit quantization) to fit training on single GPU


## Architecture

### System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          Local Development Environment                   │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐              │
│  │ PDF Reports  │───▶│ Preprocessing│───▶│ HTML Ground  │              │
│  │              │    │ Scripts      │    │ Truth        │              │
│  └──────────────┘    └──────────────┘    └──────────────┘              │
│                              │                                           │
│                              ▼                                           │
│                    ┌──────────────────┐                                 │
│                    │ Training Data    │                                 │
│                    │ JSON Generator   │                                 │
│                    └──────────────────┘                                 │
└─────────────────────────────┬───────────────────────────────────────────┘
                              │ Upload (AWS CLI)
                              ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          AWS Cloud Infrastructure                        │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │                    Amazon S3 Storage (Single Bucket)            │    │
│  │  ┌──────────────────────────────────────────────────────┐      │    │
│  │  │ sec-documents-{account}-{region}                     │      │    │
│  │  │ - data/images/                                       │      │    │
│  │  │ - data/training.json                                 │      │    │
│  │  │ - scripts/lifecycle.sh                               │      │    │
│  │  │ - models/checkpoints/                                │      │    │
│  │  └──────────────────────────────────────────────────────┘      │    │
│  └────────────────────────────────────────────────────────────────┘    │
│                              │                                           │
│                              ▼ (VPC Endpoint - No NAT Gateway)          │
│  ┌────────────────────────────────────────────────────────────────┐    │
│  │              SageMaker HyperPod Cluster (VPC)                   │    │
│  │                                                                  │    │
│  │  ┌──────────────────────────────────────────────────────┐      │    │
│  │  │   Single Worker Node (GPU)                           │      │    │
│  │  │   ml.g5.xlarge (1x NVIDIA A10G, 24GB VRAM)          │      │    │
│  │  │   - LLaMA-Factory                                    │      │    │
│  │  │   - Qwen2-VL Model                                   │      │    │
│  │  │   - QLoRA Training (4-bit)                           │      │    │
│  │  └──────────────────────────────────────────────────────┘      │    │
│  │                                                                  │    │
│  │  No FSx, No Slurm, Direct S3 Access via VPC Endpoint            │    │
│  └────────────────────────────────────────────────────────────────┘    │
│                              │                                           │
│                              ▼                                           │
│                    Download model to local                               │
│                    (Optional: Test with vLLM locally)                    │
└─────────────────────────────────────────────────────────────────────────┘
```


### Data Flow

1. **Ingestion**: PDF documents converted to PNG images (200 DPI) locally
2. **Annotation**: Manual HTML ground truth creation for table structures
3. **Dataset Generation**: Image-HTML pairs formatted as LLaMA-Factory JSON
4. **Upload**: Training data uploaded to S3 bucket via AWS CLI
5. **Training**: HyperPod worker loads data from S3 via VPC endpoint, fine-tunes model with QLoRA
6. **Checkpointing**: Model adapters saved to S3 at regular intervals
7. **Download**: Download fine-tuned model to local machine
8. **Evaluation**: Test locally by running inference on sample images


## Components and Interfaces

### 1. Data Preprocessing Module

**Purpose**: Convert PDF documents to training-ready format

**Components**:
- `docs_to_images.py`: PDF to PNG converter using PyMuPDF (fitz)
- `generate_training_data_json.py`: Creates LLaMA-Factory compatible JSON dataset

**Interfaces**:
```python
# PDF to Images
def convert_pdf_to_images(pdf_path: str, output_dir: str, dpi: int = 200) -> List[str]:
    """
    Convert PDF pages to PNG images
    
    Args:
        pdf_path: Path to input PDF file
        output_dir: Directory for output images
        dpi: Resolution for image conversion
    
    Returns:
        List of generated image file paths
    """

# Training Data Generation
def generate_training_data(
    image_dir: str, 
    html_dir: str, 
    output_json_path: str
) -> Dict[str, Any]:
    """
    Generate LLaMA-Factory JSON format from image-HTML pairs
    
    Args:
        image_dir: Directory containing PNG images
        html_dir: Directory containing HTML ground truth files
        output_json_path: Path for output JSON file
    
    Returns:
        Dictionary with dataset statistics
    """
```

**LLaMA-Factory JSON Format**:
```json
[
  {
    "messages": [
      {
        "role": "system",
        "content": "You are a financial document processing assistant."
      },
      {
        "role": "user",
        "content": "Extract the table structure from this image and output as HTML"
      },
      {
        "role": "assistant",
        "content": "<table><tr><td>...</td></tr></table>"
      }
    ],
    "images": ["data/preprocessed/company_name/page_1.png"]
  }
]
```


### 2. Infrastructure Provisioning Module (CDK)

**Purpose**: Deploy AWS resources with infrastructure-as-code

**Components**:
- `SecDocumentsProcessingStack`: CDK stack defining all AWS resources
- `generate_cluster_config.py`: Generates HyperPod cluster configuration from environment variables

**Resources Created**:

1. **VPC Configuration**:
   - 1 Availability Zone (cost savings)
   - Private subnet only (no public subnet needed)
   - VPC Endpoint for S3 (no NAT Gateway - saves ~$32/month)
   - CIDR: /24 for private subnet

2. **S3 Bucket** (Single bucket for everything):
   - Bucket: `sec-documents-{account}-{region}`
     - Stores: training images, JSON datasets, lifecycle scripts, model checkpoints
     - No versioning (cost savings)
     - No encryption beyond default

3. **IAM Role**:
   - Service Principal: `sagemaker.amazonaws.com`
   - Minimal inline policy:
     - S3: GetObject, PutObject, ListBucket on specific bucket
     - SageMaker: Basic permissions for HyperPod
   - Used by: HyperPod instance

4. **Security Group**:
   - Attached to: HyperPod instance
   - Egress: HTTPS to S3 VPC endpoint only
   - Ingress: None

**Interfaces**:
```python
class SecDocumentsProcessingStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs):
        # Creates VPC, S3 buckets, IAM role, security group
        # Outputs: VPC ID, bucket names, role ARN, security group ID
```

**CDK Outputs**:
- `VPCId`: Used for HyperPod cluster configuration
- `SubnetId`: Private subnet for HyperPod
- `BucketName`: Single bucket for all data
- `SageMakerRoleArn`: Execution role for HyperPod
- `SecurityGroupId`: Network security for instance


### 3. SageMaker HyperPod Cluster

**Purpose**: Provide scalable, fault-tolerant distributed training infrastructure

**Cluster Configuration**:

```json
{
  "ClusterName": "sec-table-extraction-minimal",
  "InstanceGroups": [
    {
      "InstanceGroupName": "worker-group",
      "InstanceType": "ml.g5.xlarge",
      "InstanceCount": 1,
      "LifeCycleConfig": {
        "SourceS3Uri": "s3://{bucket}/scripts/",
        "OnCreate": "lifecycle.sh"
      },
      "ExecutionRole": "{role_arn}",
      "ThreadsPerCore": 1
    }
  ],
  "NodeRecovery": "Automatic"
}
```

**Instance Type**:
- **Worker (ml.g5.xlarge)**:
  - 4 vCPUs, 16 GB RAM, 1x NVIDIA A10G GPU (24 GB VRAM)
  - Runs training workload
  - No separate controller node (cost savings)
  - Cost: ~$1.41/hour on-demand

**Lifecycle Script** (`lifecycle.sh`):
- Executed on instance startup (OnCreate hook)
- Installs minimal system dependencies: git, python3-pip
- Clones LLaMA-Factory repository to `/opt/llama-factory`
- Installs Python dependencies from requirements.txt
- Verifies GPU with nvidia-smi

**Fault Tolerance**:
- `NodeRecovery: Automatic` - Basic recovery if instance fails
- Training checkpoints saved to S3 for manual resume if needed


### 4. Model Fine-tuning Module

**Purpose**: Adapt Qwen2-VL-7B-Instruct for financial table extraction using QLoRA

**Model Architecture**:
- **Base Model**: Qwen2-VL-7B-Instruct (7 billion parameters)
- **Vision Encoder**: Vision Transformer (ViT) for image feature extraction
- **Language Model**: Transformer decoder for text generation
- **Multimodal Fusion**: Cross-attention layers connecting vision and language

**Fine-tuning Strategy - QLoRA**:
- **Quantization**: 4-bit NormalFloat (NF4) quantization of base model weights
- **Low-Rank Adaptation**: Trainable adapter matrices with rank r=8-64
- **Target Modules**: Query, Key, Value projection layers in attention blocks
- **Memory Savings**: ~75% reduction compared to full fine-tuning
- **Performance**: Maintains 95%+ of full fine-tuning accuracy

**Training Configuration**:
```yaml
# LLaMA-Factory training arguments (minimal)
model_name_or_path: Qwen/Qwen2-VL-7B-Instruct
dataset: sec_tables_train
output_dir: s3://{bucket}/models/checkpoints
num_train_epochs: 1
per_device_train_batch_size: 1
gradient_accumulation_steps: 4
learning_rate: 2e-4
lr_scheduler_type: cosine
warmup_ratio: 0.1
logging_steps: 10
save_steps: 50
save_total_limit: 2
fp16: true

# QLoRA specific
quantization_bit: 4
lora_rank: 8
lora_alpha: 16
lora_dropout: 0.05
lora_target: q_proj,v_proj

# Multimodal
image_resolution: 512
max_length: 1024
```

**Single GPU Training**:
- No distributed training (single GPU only)
- No Slurm, no torchrun
- Direct Python script execution
- Minimal batch size to fit in 24GB VRAM

**Training Script Interface**:
```bash
# Direct training on HyperPod instance
cd /opt/llama-factory
python src/train.py \
  --stage sft \
  --model_name_or_path Qwen/Qwen2-VL-7B-Instruct \
  --dataset sec_tables_train \
  --template qwen2_vl \
  --finetuning_type lora \
  --output_dir s3://{bucket}/models/checkpoints \
  --per_device_train_batch_size 1 \
  --num_train_epochs 1 \
  --quantization_bit 4
```


### 5. Model Evaluation Module

**Purpose**: Simple visual verification that training worked

**Evaluation Approach**:
- Download fine-tuned model from S3 to local machine
- Run inference on 2-3 test images locally
- Manually compare HTML output to ground truth
- Visual inspection of rendered tables in browser

**Simple Evaluation Script**:
```python
def simple_evaluation(model_path: str, test_images: List[str]):
    """
    Simple local evaluation
    
    Args:
        model_path: Path to downloaded model checkpoint
        test_images: List of test image paths
    """
    # Load model with adapters
    # Process each test image
    # Save HTML predictions
    # Print predictions to console
```

**Success Criteria**:
- Model generates valid HTML
- Table structure roughly matches ground truth
- Better than random output


### 6. Model Deployment Module (Optional - Local Only)

**Purpose**: Test inference locally to verify the model works

**Local vLLM Testing** (Optional):
```bash
# Install vLLM locally (requires GPU)
pip install vllm

# Load model and run inference
python -m vllm.entrypoints.openai.api_server \
  --model ./downloaded-model \
  --dtype float16 \
  --max-model-len 2048 \
  --port 8000
```

**Simple Inference Script**:
```python
# Direct inference without vLLM
from transformers import AutoModelForCausalLM, AutoTokenizer

model = AutoModelForCausalLM.from_pretrained("./downloaded-model")
tokenizer = AutoTokenizer.from_pretrained("./downloaded-model")

# Process image and generate HTML
# No API, no server, just local testing
```

**Note**: Production deployment is out of scope for this minimal setup


## Data Models

### Training Dataset Schema

**LLaMA-Factory JSON Format**:
```json
{
  "type": "array",
  "items": {
    "type": "object",
    "required": ["messages", "images"],
    "properties": {
      "messages": {
        "type": "array",
        "items": {
          "type": "object",
          "required": ["role", "content"],
          "properties": {
            "role": {
              "type": "string",
              "enum": ["system", "user", "assistant"]
            },
            "content": {
              "type": "string"
            }
          }
        }
      },
      "images": {
        "type": "array",
        "items": {
          "type": "string",
          "description": "Relative or absolute path to image file"
        }
      }
    }
  }
}
```

**Example Entry**:
```json
{
  "messages": [
    {
      "role": "system",
      "content": "You are a financial document processing assistant specialized in extracting table structures from SEC filings."
    },
    {
      "role": "user",
      "content": "Extract the table structure from this image and output as HTML. Preserve all rows, columns, merged cells (colspan/rowspan), and cell content."
    },
    {
      "role": "assistant",
      "content": "<table>\n  <tr>\n    <td></td>\n    <td colspan=\"5\">Payments due by period</td>\n  </tr>\n  <tr>\n    <td></td>\n    <td>Total</td>\n    <td>Less than 1 year</td>\n    <td>1-3 years</td>\n    <td>3-5 years</td>\n    <td>More than 5 years</td>\n  </tr>\n  <tr>\n    <td>Operating Activities:</td>\n    <td></td>\n    <td></td>\n    <td></td>\n    <td></td>\n    <td></td>\n  </tr>\n</table>"
    }
  ],
  "images": ["data/preprocessed/constellation_energy/page_9.png"]
}
```


### Model Checkpoint Structure

**Directory Layout**:
```
/opt/ml/model/checkpoints/
├── checkpoint-100/
│   ├── adapter_config.json       # LoRA configuration
│   ├── adapter_model.bin         # LoRA weights
│   ├── trainer_state.json        # Training state
│   └── training_args.bin         # Training arguments
├── checkpoint-200/
│   └── ...
└── final/
    ├── adapter_config.json
    ├── adapter_model.bin
    └── tokenizer/
        ├── tokenizer_config.json
        ├── vocab.json
        └── merges.txt
```

**Adapter Config Schema**:
```json
{
  "base_model_name_or_path": "Qwen/Qwen2-VL-7B-Instruct",
  "bias": "none",
  "fan_in_fan_out": false,
  "inference_mode": false,
  "lora_alpha": 32,
  "lora_dropout": 0.05,
  "modules_to_save": null,
  "peft_type": "LORA",
  "r": 16,
  "target_modules": ["q_proj", "v_proj", "k_proj", "o_proj"],
  "task_type": "CAUSAL_LM"
}
```

### Evaluation Results Schema

**evaluation_report.json**:
```json
{
  "model_name": "qwen2-vl-sec-tables-v1",
  "base_model": "Qwen/Qwen2-VL-7B-Instruct",
  "test_set_size": 150,
  "metrics": {
    "teds_mean": 81.1,
    "teds_std": 12.3,
    "teds_s_mean": 89.7,
    "teds_s_std": 8.5
  },
  "baseline_comparison": {
    "base_model_teds": 23.4,
    "improvement": 57.7
  },
  "error_analysis": {
    "low_score_count": 12,
    "common_errors": [
      "Incorrect colspan detection",
      "Missing nested table structures",
      "OCR errors in numeric cells"
    ]
  },
  "timestamp": "2025-11-06T10:30:00Z"
}
```


## Error Handling

### Data Preprocessing Errors

**PDF Conversion Failures**:
- **Error**: Corrupted or password-protected PDF
- **Handling**: 
  - Catch `fitz.FileDataError` exception
  - Log error with file path
  - Skip file and continue processing
  - Report failed files in summary

**Missing HTML Ground Truth**:
- **Error**: Image exists but no corresponding HTML file
- **Handling**:
  - Log warning with image path
  - Skip entry in training dataset
  - Generate report of unannotated images

**Invalid HTML Structure**:
- **Error**: Malformed HTML, missing table tags
- **Handling**:
  - Validate HTML with BeautifulSoup parser
  - Log validation errors
  - Optionally auto-correct simple issues (unclosed tags)
  - Flag for manual review

### Infrastructure Provisioning Errors

**CDK Deployment Failures**:
- **Error**: Resource name conflicts, quota limits
- **Handling**:
  - Use unique naming with account/region suffixes
  - Check service quotas before deployment
  - Implement retry logic for transient failures
  - Provide clear error messages with remediation steps

**S3 Upload Failures**:
- **Error**: Network timeout, permission denied
- **Handling**:
  - Implement exponential backoff retry (3 attempts)
  - Verify IAM permissions before upload
  - Use multipart upload for large files
  - Log failed uploads for manual retry

### Training Errors

**Out of Memory (OOM)**:
- **Error**: GPU memory exhausted during training
- **Handling**:
  - Reduce batch size automatically
  - Increase gradient accumulation steps
  - Enable gradient checkpointing
  - Log memory usage metrics

**Training Divergence**:
- **Error**: Loss becomes NaN or increases rapidly
- **Handling**:
  - Implement gradient clipping (max_norm=1.0)
  - Reduce learning rate
  - Check for data quality issues
  - Rollback to last stable checkpoint

**Node Failures**:
- **Error**: HyperPod worker instance crashes
- **Handling**:
  - Automatic node recovery (HyperPod feature)
  - Resume training from last S3 checkpoint
  - Log failure events for analysis
  - Alert on repeated failures

**Checkpoint Save Failures**:
- **Error**: S3 write timeout, disk full
- **Handling**:
  - Retry checkpoint save with exponential backoff
  - Keep local checkpoint as fallback
  - Alert on consecutive save failures
  - Implement checkpoint rotation (keep last N)

### Inference Errors

**Model Loading Failures**:
- **Error**: Corrupted checkpoint, version mismatch
- **Handling**:
  - Validate checkpoint integrity (checksums)
  - Fallback to previous stable checkpoint
  - Log detailed error information
  - Return 503 Service Unavailable

**Inference Timeout**:
- **Error**: Request exceeds 30-second timeout
- **Handling**:
  - Implement request timeout (configurable)
  - Return 408 Request Timeout with retry-after header
  - Log slow requests for optimization
  - Consider image preprocessing (resize, crop)

**Invalid Input**:
- **Error**: Non-image file, unsupported format
- **Handling**:
  - Validate input format (PNG, JPEG)
  - Check image dimensions (max 4096x4096)
  - Return 400 Bad Request with error details
  - Provide input specification in API docs


## Testing Strategy

### Unit Testing

**Data Preprocessing**:
- Test PDF to image conversion with various PDF formats
- Validate image resolution and quality
- Test HTML parsing and validation
- Verify JSON dataset generation format

**Infrastructure**:
- Test CDK stack synthesis
- Validate IAM policy permissions
- Test S3 bucket configuration
- Verify security group rules

**Test Framework**: pytest
**Coverage Target**: > 80% for utility functions

### Integration Testing

**End-to-End Data Pipeline**:
- Test complete flow: PDF → Images → HTML → JSON → S3
- Verify data integrity at each stage
- Test with multiple document types
- Validate S3 sync functionality

**Training Pipeline**:
- Test model loading and initialization
- Verify dataset loading from S3
- Test checkpoint saving and loading
- Validate distributed training setup (single-node)

**Test Environment**: Local development with mocked AWS services (moto)

### Model Evaluation Testing

**Functional Tests**:
- Test model inference on sample images
- Verify HTML output format
- Test batch processing
- Validate error handling for invalid inputs

**Performance Tests**:
- Measure inference latency (target: < 5s)
- Test throughput under load (target: > 100 req/min)
- Monitor GPU memory usage
- Test concurrent request handling

**Accuracy Tests**:
- Calculate TEDS on validation set
- Compare against baseline model
- Test on edge cases (complex tables, poor quality scans)
- Validate consistency across multiple runs

**Test Framework**: pytest + locust (load testing)

### System Testing

**HyperPod Cluster**:
- Test cluster provisioning and teardown
- Verify lifecycle script execution
- Test node recovery mechanism
- Validate multi-node training

**vLLM Deployment**:
- Test model server startup
- Verify API endpoint functionality
- Test health check endpoints
- Validate auto-scaling behavior

**Security Testing**:
- Verify VPC isolation
- Test IAM role permissions (least privilege)
- Validate S3 bucket encryption
- Test API authentication

**Test Environment**: AWS test account with isolated resources

### Acceptance Testing

**User Scenarios**:
1. Data scientist uploads new training data
2. ML engineer triggers fine-tuning job
3. System automatically recovers from node failure
4. API user submits document for extraction
5. Results are validated against ground truth

**Success Criteria**:
- All requirements met (see requirements.md)
- TEDS score > 80 on test set
- Training completes within 8 hours (1000 samples)
- API latency < 5 seconds (p95)
- Zero data loss during failures


## Security Considerations

**Minimal Security for Learning**:
- Use default S3 encryption (SSE-S3)
- IAM role with minimal permissions (S3 + SageMaker)
- VPC with private subnet and S3 VPC endpoint
- No secrets management (use IAM roles only)
- No CloudTrail, no Config, no compliance features

**Important**:
- Never commit AWS credentials to Git
- Use IAM roles instead of access keys
- This setup is NOT suitable for production or sensitive data


## Performance and Cost Optimization

### Training Optimization (Minimal)

**Memory Efficiency**:
- QLoRA 4-bit quantization: Fit 7B model in 24GB VRAM
- Batch size 1 with gradient accumulation
- FP16 mixed precision

**Expected Training Time**:
- 50-100 samples, 1 epoch, 1x A10G GPU: ~1-2 hours
- Keep dataset small for learning purposes

### Cost Optimization (Critical)

**Training Costs**:
- Use ml.g5.xlarge: ~$1.41/hour
- Train for 1-2 hours max: ~$3-5 per experiment
- Delete cluster immediately after training
- Use minimal dataset (50-100 samples)

**Infrastructure Costs**:
- VPC Endpoint for S3: ~$0.01/GB transferred (minimal)
- S3 storage: ~$0.023/GB/month (few GB = cents)
- No NAT Gateway: Save ~$32/month
- No CloudWatch, no monitoring: Save ~$10-20/month

**Estimated Total Cost for Learning**:
- One training run: $3-5
- S3 storage (10GB): $0.23/month
- VPC/networking: $1-2/month
- Total per experiment: ~$5-10


## Monitoring and Observability

**Minimal Monitoring for Learning**:
- Check training logs directly on HyperPod instance via SSH or SageMaker console
- Monitor training loss printed to console
- Check GPU utilization with `nvidia-smi` if needed
- No CloudWatch, no TensorBoard, no dashboards
- Manually check AWS Cost Explorer once a week

**Cost Monitoring**:
- Set AWS Budget alert for $50/month
- Delete HyperPod cluster immediately after training
- Check S3 storage size occasionally


## Deployment Strategy

**Simple Manual Workflow**:
1. Develop preprocessing scripts locally
2. Create small test dataset (20-50 samples)
3. Deploy infrastructure with CDK manually
4. Upload data to S3 with AWS CLI
5. Create HyperPod cluster manually via AWS Console or CLI
6. SSH into instance and run training script
7. Download model from S3
8. Test locally
9. Delete HyperPod cluster

**No CI/CD, No Staging, No Production**:
- This is a learning/experimentation setup only
- All operations are manual
- No automated pipelines
- No rollback strategy needed


## Future Enhancements

**If This Works and You Want to Continue**:
- Increase dataset size (100-500 samples)
- Try longer training (2-3 epochs)
- Experiment with different LoRA ranks
- Test on more complex tables
- Try different base models (Qwen2-VL-2B for faster training)
- Add simple TEDS metric calculation
- Consider production deployment (separate project)


## References

### Technical Documentation

**AWS Services**:
- [Amazon SageMaker HyperPod Documentation](https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-hyperpod.html)
- [AWS CDK Python Documentation](https://docs.aws.amazon.com/cdk/api/v2/python/)
- [Amazon S3 Best Practices](https://docs.aws.amazon.com/AmazonS3/latest/userguide/best-practices.html)
- [AWS Security Best Practices](https://docs.aws.amazon.com/security/)

**Model and Framework**:
- [Qwen2-VL Model Card](https://huggingface.co/Qwen/Qwen2-VL-7B-Instruct)
- [LLaMA-Factory Documentation](https://llamafactory.readthedocs.io/)
- [vLLM Documentation](https://docs.vllm.ai/)
- [QLoRA Paper](https://arxiv.org/abs/2305.14314)

**Evaluation Metrics**:
- [TEDS Metric Paper](https://arxiv.org/abs/1911.10683)
- [FinTabNet Dataset](https://developer.ibm.com/exchanges/data/all/fintabnet/)

### Blog Posts and Tutorials

- [AWS Blog: How Apoidea Group enhances visual information extraction](https://aws.amazon.com/blogs/machine-learning/how-apoidea-group-enhances-visual-information-extraction/)
- [Fine-tuning Qwen2-VL with LLaMA-Factory on SageMaker HyperPod](https://github.com/aws-samples/fine-tune-qwen2-vl-with-llama-factory)

### Related Projects

- [AWS Samples: Document Understanding](https://github.com/aws-samples/amazon-textract-comprehend-document-understanding)
- [Hugging Face: Table Transformer](https://huggingface.co/microsoft/table-transformer-detection)

