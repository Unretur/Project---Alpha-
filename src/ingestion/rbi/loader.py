from pathlib import Path

from pypdf import PdfReader

PDF_PATH = Path(
    "data/raw/rbi/"
    "Daily Money Market Operations.pdf"
)


def load_pdf_text(pdf_path: Path) -> str:
    reader = PdfReader(pdf_path)

    pages = []

    for page in reader.pages:
        text = page.extract_text()

        if text:
            pages.append(text)

    return "\n".join(pages)


if __name__ == "__main__":
    text = load_pdf_text(PDF_PATH)

    print("PDF loaded successfully")
    print("Characters extracted:", len(text))
    print("\nFirst 2000 characters:\n")
    print(text[:2000])