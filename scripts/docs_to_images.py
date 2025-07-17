import fitz
import os

def connvert_pdf_to_images(pdf_path, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    doc = fitz.open(pdf_path)

    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        pix = page.get_pixmap(dpi=200)
        output_path = os.path.join(output_dir, f"page_{page_num + 1}.png")
        pix.save(output_path)
        print(f"Gespeichert: {output_path}")


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Nutzung: python pdf_to_images.py <pfad/zur/pdf> <ausgabeordner>")
        exit(1)

    pdf_path = sys.argv[1]
    output_dir = sys.argv[2]
    connvert_pdf_to_images(pdf_path, output_dir)