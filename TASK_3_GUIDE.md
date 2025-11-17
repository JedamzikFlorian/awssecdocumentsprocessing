# Task 3: Training Data JSON Generation - Implementation Guide

## Overview
You'll be updating the `scripts/generate_training_data_json.py` file to generate training data in the LLaMA-Factory format. This script converts image-HTML pairs into a structured JSON format that the multimodal model can use for training.

## What You Need to Do

There are 3 sub-tasks to complete:
1. Update the output format to match LLaMA-Factory's messages array format
2. Add validation for missing HTML files
3. Add HTML validation to check for well-formed table tags

---

## Understanding the LLaMA-Factory Format

### Current Format (Wrong)
```json
[
  {
    "image": "page_1.png",
    "html": "<table>...</table>"
  }
]
```

### LLaMA-Factory Format (Correct)
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
        "content": "<table>...</table>"
      }
    ],
    "images": ["data/preprocessed/company_name/page_1.png"]
  }
]
```

**Key Differences:**
- Uses `messages` array with system/user/assistant roles (like ChatGPT)
- Uses `images` array (plural) instead of single `image`
- Image path should be relative or absolute path
- HTML content goes in the assistant's message

---

## Sub-task 3.1: Update to LLaMA-Factory Format

### Current Problems
1. Wrong output format (simple dict instead of messages array)
2. Typo in parameter name: `outpunt_json_path` should be `output_json_path`
3. Image path handling doesn't preserve directory structure

### What to Change

**Step 1:** Fix the function signature (line 4)

Change:
```python
def generate_training_data(image_dir, outpunt_json_path):
```

To:
```python
def generate_training_data(image_dir, html_dir, output_json_path):
```

**Why:** We need separate directories for images and HTML files, and fix the typo.

**Step 2:** Update the function to use the new format

Replace the entire function body (lines 5-24) with:

```python
def generate_training_data(image_dir, html_dir, output_json_path):
    """
    Generate LLaMA-Factory compatible training data JSON
    
    Args:
        image_dir: Directory containing PNG images
        html_dir: Directory containing HTML ground truth files
        output_json_path: Path for output JSON file
    
    Returns:
        Number of examples created
    """
    examples = []
    skipped_files = []
    
    # System prompt for the model
    system_prompt = "You are a financial document processing assistant specialized in extracting table structures from SEC filings."
    
    # User instruction
    user_prompt = "Extract the table structure from this image and output as HTML. Preserve all rows, columns, merged cells (colspan/rowspan), and cell content."
    
    # Scan all PNG images in the image directory
    for file in os.listdir(image_dir):
        if file.endswith(".png"):
            base = os.path.splitext(file)[0]
            html_path = os.path.join(html_dir, base + ".html")
            image_path = os.path.join(image_dir, file)
            
            # Check if corresponding HTML file exists
            if os.path.exists(html_path):
                try:
                    with open(html_path, "r", encoding="utf-8") as f:
                        html_content = f.read()
                    
                    # Create LLaMA-Factory format entry
                    example = {
                        "messages": [
                            {
                                "role": "system",
                                "content": system_prompt
                            },
                            {
                                "role": "user",
                                "content": user_prompt
                            },
                            {
                                "role": "assistant",
                                "content": html_content
                            }
                        ],
                        "images": [image_path]
                    }
                    
                    examples.append(example)
                    
                except Exception as e:
                    print(f"⚠ Warning: Failed to read {html_path}: {str(e)}")
                    skipped_files.append(file)
            else:
                skipped_files.append(file)
    
    # Save to JSON file
    with open(output_json_path, "w", encoding="utf-8") as out_f:
        json.dump(examples, out_f, indent=2, ensure_ascii=False)
    
    print(f"✓ {len(examples)} examples saved to {output_json_path}")
    
    if skipped_files:
        print(f"⚠ Skipped {len(skipped_files)} images without HTML files")
    
    return len(examples)
```

**Step 3:** Update the main block (lines 26-32)

Change:
```python
if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Nutzung: python generate_training_data_json.py <ordner> <ziel.json>")
        exit(1)

    generate_training_data(sys.argv[1], sys.argv[2])
```

To:
```python
if __name__ == "__main__":
    import sys
    if len(sys.argv) < 4:
        print("Usage: python generate_training_data_json.py <image_dir> <html_dir> <output.json>")
        print("Example: python generate_training_data_json.py data/preprocessed data/html_tables data/training.json")
        exit(1)
    
    image_dir = sys.argv[1]
    html_dir = sys.argv[2]
    output_json = sys.argv[3]
    
    count = generate_training_data(image_dir, html_dir, output_json)
    exit(0 if count > 0 else 1)
```

---

## Sub-task 3.2: Add Validation for Missing HTML Files

This is already included in the code above! Look for these parts:

```python
skipped_files = []

# ... in the loop ...
if os.path.exists(html_path):
    # process file
else:
    skipped_files.append(file)

# ... at the end ...
if skipped_files:
    print(f"⚠ Skipped {len(skipped_files)} images without HTML files")
```

**What it does:**
- Tracks which image files don't have corresponding HTML files
- Skips them gracefully without crashing
- Reports the count at the end

---

## Sub-task 3.3: Add HTML Validation

### What to Add

**Step 1:** Import BeautifulSoup at the top of the file (after line 2):

```python
import os
import json
from bs4 import BeautifulSoup
```

**Step 2:** Add a validation function after the imports (before `generate_training_data`):

```python
def validate_html(html_content, filename):
    """
    Validate HTML content for well-formed table structure
    
    Args:
        html_content: HTML string to validate
        filename: Name of file being validated (for error messages)
    
    Returns:
        (is_valid, error_message)
    """
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Check if there's at least one table tag
        tables = soup.find_all('table')
        if not tables:
            return False, "No <table> tag found"
        
        # Check for basic table structure
        for table in tables:
            rows = table.find_all('tr')
            if not rows:
                return False, "Table has no <tr> (row) tags"
            
            # Check if rows have cells
            has_cells = False
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if cells:
                    has_cells = True
                    break
            
            if not has_cells:
                return False, "Table rows have no <td> or <th> (cell) tags"
        
        return True, None
        
    except Exception as e:
        return False, f"HTML parsing error: {str(e)}"
```

**Step 3:** Use the validation function in `generate_training_data`

Find this section in the function:
```python
with open(html_path, "r", encoding="utf-8") as f:
    html_content = f.read()
```

Add validation right after reading the HTML:
```python
with open(html_path, "r", encoding="utf-8") as f:
    html_content = f.read()

# Validate HTML structure
is_valid, error_msg = validate_html(html_content, file)
if not is_valid:
    print(f"⚠ Warning: Invalid HTML in {html_path}: {error_msg}")
    skipped_files.append(file)
    continue
```

---

## Complete Final Code

Here's what your complete `scripts/generate_training_data_json.py` should look like:

```python
import os
import json
from bs4 import BeautifulSoup


def validate_html(html_content, filename):
    """
    Validate HTML content for well-formed table structure
    
    Args:
        html_content: HTML string to validate
        filename: Name of file being validated (for error messages)
    
    Returns:
        (is_valid, error_message)
    """
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Check if there's at least one table tag
        tables = soup.find_all('table')
        if not tables:
            return False, "No <table> tag found"
        
        # Check for basic table structure
        for table in tables:
            rows = table.find_all('tr')
            if not rows:
                return False, "Table has no <tr> (row) tags"
            
            # Check if rows have cells
            has_cells = False
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if cells:
                    has_cells = True
                    break
            
            if not has_cells:
                return False, "Table rows have no <td> or <th> (cell) tags"
        
        return True, None
        
    except Exception as e:
        return False, f"HTML parsing error: {str(e)}"


def generate_training_data(image_dir, html_dir, output_json_path):
    """
    Generate LLaMA-Factory compatible training data JSON
    
    Args:
        image_dir: Directory containing PNG images
        html_dir: Directory containing HTML ground truth files
        output_json_path: Path for output JSON file
    
    Returns:
        Number of examples created
    """
    examples = []
    skipped_files = []
    validation_errors = []
    
    # System prompt for the model
    system_prompt = "You are a financial document processing assistant specialized in extracting table structures from SEC filings."
    
    # User instruction
    user_prompt = "Extract the table structure from this image and output as HTML. Preserve all rows, columns, merged cells (colspan/rowspan), and cell content."
    
    # Scan all PNG images in the image directory
    for file in os.listdir(image_dir):
        if file.endswith(".png"):
            base = os.path.splitext(file)[0]
            html_path = os.path.join(html_dir, base + ".html")
            image_path = os.path.join(image_dir, file)
            
            # Check if corresponding HTML file exists
            if os.path.exists(html_path):
                try:
                    with open(html_path, "r", encoding="utf-8") as f:
                        html_content = f.read()
                    
                    # Validate HTML structure
                    is_valid, error_msg = validate_html(html_content, file)
                    if not is_valid:
                        print(f"⚠ Warning: Invalid HTML in {html_path}: {error_msg}")
                        validation_errors.append((file, error_msg))
                        skipped_files.append(file)
                        continue
                    
                    # Create LLaMA-Factory format entry
                    example = {
                        "messages": [
                            {
                                "role": "system",
                                "content": system_prompt
                            },
                            {
                                "role": "user",
                                "content": user_prompt
                            },
                            {
                                "role": "assistant",
                                "content": html_content
                            }
                        ],
                        "images": [image_path]
                    }
                    
                    examples.append(example)
                    
                except Exception as e:
                    print(f"⚠ Warning: Failed to read {html_path}: {str(e)}")
                    skipped_files.append(file)
            else:
                skipped_files.append(file)
    
    # Save to JSON file
    with open(output_json_path, "w", encoding="utf-8") as out_f:
        json.dump(examples, out_f, indent=2, ensure_ascii=False)
    
    print(f"✓ {len(examples)} examples saved to {output_json_path}")
    
    if skipped_files:
        print(f"⚠ Skipped {len(skipped_files)} images without HTML files or with validation errors")
        if validation_errors:
            print(f"   - {len(validation_errors)} files had HTML validation errors")
    
    return len(examples)


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 4:
        print("Usage: python generate_training_data_json.py <image_dir> <html_dir> <output.json>")
        print("Example: python generate_training_data_json.py data/preprocessed data/html_tables data/training.json")
        exit(1)
    
    image_dir = sys.argv[1]
    html_dir = sys.argv[2]
    output_json = sys.argv[3]
    
    count = generate_training_data(image_dir, html_dir, output_json)
    exit(0 if count > 0 else 1)
```

---

## How to Test Your Changes

### Test 1: Create Sample Data

**Step 1:** Create test directories and files:

```cmd
mkdir data\test_images
mkdir data\test_html
```

**Step 2:** Create a sample image (you can copy any PNG file):
```cmd
copy some_image.png data\test_images\page_1.png
```

**Step 3:** Create a sample HTML file `data\test_html\page_1.html`:
```html
<table>
  <tr>
    <th>Header 1</th>
    <th>Header 2</th>
  </tr>
  <tr>
    <td>Data 1</td>
    <td>Data 2</td>
  </tr>
</table>
```

### Test 2: Run the Script

```cmd
python scripts/generate_training_data_json.py data/test_images data/test_html data/test_output.json
```

**Expected Output:**
```
✓ 1 examples saved to data/test_output.json
```

### Test 3: Verify the Output Format

Open `data/test_output.json` and verify it looks like:

```json
[
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
        "content": "<table>\n  <tr>\n    <th>Header 1</th>\n    <th>Header 2</th>\n  </tr>\n  <tr>\n    <td>Data 1</td>\n    <td>Data 2</td>\n  </tr>\n</table>"
      }
    ],
    "images": [
      "data/test_images\\page_1.png"
    ]
  }
]
```

### Test 4: Test Missing HTML File

**Step 1:** Create an image without HTML:
```cmd
copy some_image.png data\test_images\page_2.png
```

**Step 2:** Run the script again:
```cmd
python scripts/generate_training_data_json.py data/test_images data/test_html data/test_output.json
```

**Expected Output:**
```
✓ 1 examples saved to data/test_output.json
⚠ Skipped 1 images without HTML files or with validation errors
```

### Test 5: Test Invalid HTML

**Step 1:** Create invalid HTML `data\test_html\page_3.html`:
```html
<div>This is not a table</div>
```

**Step 2:** Create corresponding image:
```cmd
copy some_image.png data\test_images\page_3.png
```

**Step 3:** Run the script:
```cmd
python scripts/generate_training_data_json.py data/test_images data/test_html data/test_output.json
```

**Expected Output:**
```
⚠ Warning: Invalid HTML in data\test_html\page_3.html: No <table> tag found
✓ 1 examples saved to data/test_output.json
⚠ Skipped 2 images without HTML files or with validation errors
   - 1 files had HTML validation errors
```

---

## Installing BeautifulSoup

You'll need to install BeautifulSoup4 for HTML validation:

```cmd
pip install beautifulsoup4
```

Or add it to your `requirements.txt`:
```
beautifulsoup4
```

Then run:
```cmd
pip install -r requirements.txt
```

---

## Checklist

Before you consider this task complete, verify:

- [ ] Function signature updated: `generate_training_data(image_dir, html_dir, output_json_path)`
- [ ] Typo fixed: `outpunt_json_path` → `output_json_path`
- [ ] BeautifulSoup imported
- [ ] `validate_html()` function added
- [ ] Output format changed to LLaMA-Factory messages array format
- [ ] System prompt added
- [ ] User prompt added
- [ ] HTML content goes in assistant message
- [ ] Images array (plural) used instead of single image
- [ ] Image path includes directory structure
- [ ] Missing HTML files are tracked and reported
- [ ] HTML validation is performed before adding to dataset
- [ ] Validation errors are logged with details
- [ ] Main block updated to accept 3 arguments
- [ ] Exit code reflects success/failure
- [ ] All tests pass successfully

---

## Requirements Mapping

This task addresses:
- **Requirement 3.1**: Scan preprocessed directory for PNG images ✓
- **Requirement 3.2**: Create JSON entry when HTML exists ✓
- **Requirement 3.3**: Format with messages array (system/user/assistant) ✓
- **Requirement 3.4**: Use proper prompt for table extraction ✓
- **Requirement 3.6**: Skip images without HTML and log warning ✓
- **Requirement 2.4**: Validate HTML for well-formed table tags ✓

---

## Tips

1. **BeautifulSoup**: Make sure to install it first with `pip install beautifulsoup4`
2. **Path separators**: Windows uses backslashes, but forward slashes work too in Python
3. **JSON formatting**: The `indent=2` makes the output readable
4. **Testing**: Start with just 1-2 test files to make sure it works before processing many files
5. **Validation**: The HTML validation is lenient - it just checks for basic table structure

---

## What's Next?

Once you've completed all 3 sub-tasks and verified they work:
1. Let me know you're done
2. I'll mark the task as complete
3. We'll move on to Task 4: Update CDK infrastructure

Good luck! This one is a bit more complex, but take it step by step. 🚀
