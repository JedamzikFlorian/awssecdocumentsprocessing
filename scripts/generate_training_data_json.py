import os
import json

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