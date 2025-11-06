import fitz
import os

def convert_pdf_to_images(pdf_path, output_dir):
    os.makedirs(output_dir, exist_ok=True)

    # Validate directory was created successfully
    if not os.path.exists(output_dir):
        print(f" ❌ Error: Failed to create output directory: {output_dir}")
        return False

    if not os.access(output_dir, os.W_OK):
        print(f"❌ Error: Output directory is not writable: {output_dir}")
        return False

    print(f"✓ Output directory ready: {output_dir}")

    try:
        doc = fitz.open(pdf_path)

        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            pix = page.get_pixmap(dpi=200)
            output_path = os.path.join(output_dir, f"page_{page_num + 1}.png")
            pix.save(output_path)
            print(f"Gespeichert: {output_path}")

    except fitz.FileDataError as e:
        print(f"❌ Error: PDF file is corrupted or password-protected: {pdf_path}")
        print(f"    Details: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error processing {pdf_path}: {str(e)}")
        return False

    return True
    

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Nutzung: python pdf_to_images.py <pfad/zur/pdf> <ausgabeordner>")
        exit(1)

    pdf_path = sys.argv[1]
    output_dir = sys.argv[2]
    convert_pdf_to_images(pdf_path, output_dir)