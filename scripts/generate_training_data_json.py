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

        # Check if there is at least one table tag
        tables = soup.find_all('table')
        if not tables:
            return False, "No <table> found"

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
                    with open(html_path, "r",
                    encoding='utf-8') as f:
                        html_content = f.read()

                        # Validate HTML structure
                        is_valid, error_msg = validate_html(html_content, file)
                        if not is_valid:
                            print(f"Warning: Invalid HTML in {html_path}: {error_msg}")
                            skipped_files.append(file)
                            continue

                    # Create LLaMA-Factory format entry
                    example = {
                        "messages": [
                            {
                                "role":"system",
                                "content":
                                system_prompt
                            },
                            {
                                "role":"user",
                                "content":
                                user_prompt
                            },
                            {
                                "role":"assistant",
                                "content":
                                html_content
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