#!/usr/bin/env python3
"""
Setup script for SEC Document Table Extraction Pipeline
Verifies environment setup and dependencies
"""

import sys
import subprocess
import os
from pathlib import Path


def check_python_version():
    """Check if Python version is 3.8 or higher"""
    print("Checking Python version...")
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"❌ Python 3.8+ required, found {version.major}.{version.minor}")
        return False
    print(f"✓ Python {version.major}.{version.minor}.{version.micro}")
    return True


def check_venv():
    """Check if running in a virtual environment"""
    print("\nChecking virtual environment...")
    in_venv = hasattr(sys, 'real_prefix') or (
        hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix
    )
    if in_venv:
        print(f"✓ Virtual environment active: {sys.prefix}")
    else:
        print("⚠ Not running in a virtual environment")
        print("  Recommendation: Create and activate a virtual environment")
        print("  Windows: python -m venv venv && venv\\Scripts\\activate")
        print("  Linux/Mac: python -m venv venv && source venv/bin/activate")
    return in_venv


def check_dependencies():
    """Check if required Python packages are installed"""
    print("\nChecking Python dependencies...")
    required_packages = [
        'boto3',
        'fitz',  # PyMuPDF
        'dotenv',  # python-dotenv
        'aws_cdk',
    ]
    
    missing = []
    for package in required_packages:
        try:
            __import__(package)
            print(f"✓ {package}")
        except ImportError:
            print(f"❌ {package} not found")
            missing.append(package)
    
    if missing:
        print(f"\n⚠ Missing packages: {', '.join(missing)}")
        print("  Install with: pip install -r requirements.txt")
        return False
    return True


def check_aws_cli():
    """Check if AWS CLI is installed and configured"""
    print("\nChecking AWS CLI...")
    try:
        result = subprocess.run(
            ['aws', '--version'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            version = result.stdout.strip() or result.stderr.strip()
            print(f"✓ AWS CLI installed: {version}")
            
            # Check if credentials are configured
            result = subprocess.run(
                ['aws', 'sts', 'get-caller-identity'],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                print("✓ AWS credentials configured")
                return True
            else:
                print("❌ AWS credentials not configured")
                print("  Run: aws configure")
                return False
        else:
            print("❌ AWS CLI not working properly")
            return False
    except FileNotFoundError:
        print("❌ AWS CLI not installed")
        print("  Install from: https://aws.amazon.com/cli/")
        return False
    except subprocess.TimeoutExpired:
        print("❌ AWS CLI command timed out")
        return False


def check_env_file():
    """Check if .env file exists and has required variables"""
    print("\nChecking .env file...")
    env_path = Path('.env')
    
    if not env_path.exists():
        print("❌ .env file not found")
        print("  Creating template .env file...")
        create_env_template()
        return False
    
    print("✓ .env file exists")
    
    # Check for required variables
    required_vars = [
        'AWS_ACCOUNT_ID',
        'REGION',
        'S3_BUCKET',
        'SAGEMAKER_EXECUTION_ROLE'
    ]
    
    with open(env_path, 'r') as f:
        content = f.read()
    
    missing_vars = []
    for var in required_vars:
        if var not in content:
            missing_vars.append(var)
        else:
            print(f"  ✓ {var}")
    
    if missing_vars:
        print(f"  ⚠ Missing variables: {', '.join(missing_vars)}")
        return False
    
    return True


def create_env_template():
    """Create a template .env file"""
    template = """# AWS Configuration
AWS_ACCOUNT_ID=your-account-id
SAGEMAKER_EXECUTION_ROLE=arn:aws:iam::your-account-id:role/your-role-name
S3_BUCKET=your-bucket-name
REGION=us-east-1
"""
    with open('.env', 'w') as f:
        f.write(template)
    print("  Created .env template - please update with your values")


def check_directory_structure():
    """Check if required directories exist"""
    print("\nChecking directory structure...")
    required_dirs = [
        'data/raw_pdfs',
        'data/preprocessed',
        'scripts',
        'cdk',
        'configs'
    ]
    
    all_exist = True
    for dir_path in required_dirs:
        path = Path(dir_path)
        if path.exists():
            print(f"✓ {dir_path}")
        else:
            print(f"⚠ {dir_path} (will be created as needed)")
    
    return True


def main():
    """Run all checks"""
    print("=" * 60)
    print("SEC Document Table Extraction - Environment Setup Check")
    print("=" * 60)
    
    checks = [
        ("Python Version", check_python_version()),
        ("Virtual Environment", check_venv()),
        ("Python Dependencies", check_dependencies()),
        ("AWS CLI", check_aws_cli()),
        ("Environment File", check_env_file()),
        ("Directory Structure", check_directory_structure()),
    ]
    
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    
    all_passed = True
    for name, passed in checks:
        status = "✓" if passed else "❌"
        print(f"{status} {name}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✓ Environment setup complete!")
        print("\nNext steps:")
        print("1. Review the .env file and update if needed")
        print("2. Start with task 2: Implement PDF to image conversion")
    else:
        print("⚠ Some checks failed - please address the issues above")
        print("\nQuick fix:")
        print("1. Activate virtual environment (if not already)")
        print("2. Run: pip install -r requirements.txt")
        print("3. Configure AWS CLI: aws configure")
        print("4. Update .env file with your AWS details")
    print("=" * 60)
    
    return 0 if all_passed else 1


if __name__ == '__main__':
    sys.exit(main())
