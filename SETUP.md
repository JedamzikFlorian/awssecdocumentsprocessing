# Local Development Environment Setup

This guide will help you set up your local development environment for the SEC Document Table Extraction Pipeline.

## Prerequisites

- Python 3.8 or higher
- AWS CLI installed and configured
- Git (for cloning repositories)

## Setup Steps

### 1. Create Virtual Environment

**Windows:**
```cmd
python -m venv venv
venv\Scripts\activate
```

**Linux/Mac:**
```bash
python -m venv venv
source venv/bin/activate
```

### 2. Install Python Dependencies

```cmd
pip install -r requirements.txt
```

This will install:
- `boto3` - AWS SDK for Python
- `PyMuPDF` - PDF processing library
- `python-dotenv` - Environment variable management
- `aws-cdk-lib` - AWS CDK for infrastructure
- Other supporting libraries

### 3. Configure AWS CLI

If not already configured:

```cmd
aws configure
```

You'll need to provide:
- AWS Access Key ID
- AWS Secret Access Key
- Default region (e.g., `eu-central-1`)
- Default output format (e.g., `json`)

Verify configuration:
```cmd
aws sts get-caller-identity
```

### 4. Set Up Environment Variables

The `.env` file is already configured with:
```
AWS_ACCOUNT_ID=642338715709
SAGEMAKER_EXECUTION_ROLE=arn:aws:iam::642338715709:role/Sagemaker-SEC-Processing-Role
S3_BUCKET=financial-documents-sec
REGION=eu-central-1
```

Update these values if needed for your AWS account.

### 5. Verify Setup

Run the setup verification script:

```cmd
python setup_env.py
```

This will check:
- ✓ Python version (3.8+)
- ✓ Virtual environment activation
- ✓ Required Python packages
- ✓ AWS CLI installation and configuration
- ✓ .env file configuration
- ✓ Directory structure

## Directory Structure

```
.
├── data/
│   ├── raw_pdfs/          # Input PDF files
│   └── preprocessed/      # Converted images
├── scripts/               # Processing scripts
├── cdk/                   # Infrastructure code
├── configs/               # Configuration files
├── requirements.txt       # Python dependencies
├── .env                   # Environment variables
└── setup_env.py          # Setup verification script
```

## Troubleshooting

### Virtual Environment Not Activating

**Windows:**
If you get an execution policy error:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### AWS CLI Not Found

Install AWS CLI:
- Windows: Download from https://aws.amazon.com/cli/
- Linux: `sudo apt-get install awscli` or `pip install awscli`
- Mac: `brew install awscli`

### Import Errors

Make sure you're in the virtual environment and have installed dependencies:
```cmd
pip install -r requirements.txt
```

### AWS Credentials Issues

Check your credentials file:
- Windows: `%USERPROFILE%\.aws\credentials`
- Linux/Mac: `~/.aws/credentials`

Or use environment variables:
```cmd
set AWS_ACCESS_KEY_ID=your-key-id
set AWS_SECRET_ACCESS_KEY=your-secret-key
```

## Next Steps

Once setup is complete:
1. Review the requirements document: `.kiro/specs/sec-document-table-extraction/requirements.md`
2. Review the design document: `.kiro/specs/sec-document-table-extraction/design.md`
3. Start implementing tasks from: `.kiro/specs/sec-document-table-extraction/tasks.md`

Begin with Task 2: Implement PDF to image conversion script
