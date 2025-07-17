import os
import json

def generate_training_data(image_dir, outpunt_json_path):
    examples = []

    for file in os.listdir(image_dir):
        if file.endswith(".png"):
            base = os.path.splitext(file)[0]
            html_path = os.path.join(image_dir, base + ".html")
            image_path = file

            if os.path.exists(html_path):
                with open(html_path, "r", encoding="utf-8") as f:
                    html_content = f.read()


                examples.append({
                    "image": image_path,
                    "html": html_content
                })

    with open(outpunt_json_path, "w", encoding="utf-8") as out_f:
        json.dump(examples, out_f, indent=2, ensure_ascii=False)

    print(f"{len(examples)} Beispiele gespeichert in {outpunt_json_path}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Nutzung: python generate_training_data_json.py <ordner> <ziel.json>")
        exit(1)

    generate_training_data(sys.argv[1], sys.argv[2])