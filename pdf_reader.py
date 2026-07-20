"""استخراج النص من ملفات PDF لتغذية محرك التدقيق"""

from pypdf import PdfReader


def extract_text_from_pdf(file_path_or_stream):
    """
    يستخرج النص الكامل من ملف PDF.
    يقبل مسار ملف (string) أو stream (مثل ملف مرفوع من Flask).
    """
    reader = PdfReader(file_path_or_stream)
    text_parts = []

    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text_parts.append(page_text)

    full_text = "\n".join(text_parts).strip()

    if not full_text:
        raise ValueError(
            "لم يتم استخراج أي نص من الملف. "
            "قد يكون الملف عبارة عن صور ممسوحة ضوئياً (scanned) ويحتاج OCR."
        )

    return full_text
