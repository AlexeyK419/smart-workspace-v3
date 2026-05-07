import os
import zipfile
import xml.etree.ElementTree as ET

from pypdf import PdfReader

TEXT_EXTENSIONS = {
    ".txt", ".md", ".csv", ".py", ".js", ".ts", ".html", ".css",
    ".json", ".xml", ".yml", ".yaml", ".sql", ".log",
}

FILE_READ_LIMIT = 260_000


def _to_text(value):
    if value is None:
        return ""
    return str(value)


def _read_zip_xml_text(path, member):
    with zipfile.ZipFile(path) as archive:
        with archive.open(member) as src:
            root = ET.parse(src).getroot()

    parts = []
    for node in root.iter():
        value = (node.text or "").strip()
        if value:
            parts.append(value)
    return "\n".join(parts)


def _read_pdf_text(path):
    reader = PdfReader(path)
    parts = []
    used = 0

    for page in reader.pages:
        value = (page.extract_text() or "").strip()
        if not value:
            continue
        remaining = FILE_READ_LIMIT - used
        if remaining <= 0:
            break
        clipped = value[:remaining]
        parts.append(clipped)
        used += len(clipped)

    return "\n\n".join(parts)


def _read_docx_text(path):
    try:
        from docx import Document
        doc = Document(path)
        parts = []
        used = 0
        for para in doc.paragraphs:
            if used >= FILE_READ_LIMIT:
                break
            text = para.text.strip()
            if text:
                parts.append(text)
                used += len(text)
        return "\n".join(parts)
    except Exception:
        return None


def _read_odt_text(path):
    try:
        from odf.opendocument import load
        from odf import text as odf_text
        doc = load(path)
        parts = []
        used = 0
        for elem in doc.getElementsByType(odf_text.P):
            if used >= FILE_READ_LIMIT:
                break
            text = _to_text(elem).strip()
            if text:
                parts.append(text)
                used += len(text)
        return "\n".join(parts)
    except Exception:
        return None


def read_file_text_raw(file_path):
    if not file_path:
        return "", "файл не прикреплен"
    if not os.path.exists(file_path):
        return "", "файл отсутствует на диске"

    ext = os.path.splitext(file_path)[1].lower()
    try:
        if ext in TEXT_EXTENSIONS:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as handle:
                return handle.read(FILE_READ_LIMIT), "ok"

        if ext == ".docx":
            text = _read_docx_text(file_path)
            if text is not None:
                return text[:FILE_READ_LIMIT], "ok"
            return _read_zip_xml_text(file_path, "word/document.xml")[:FILE_READ_LIMIT], "ok"

        if ext == ".odt":
            text = _read_odt_text(file_path)
            if text is not None:
                return text[:FILE_READ_LIMIT], "ok"
            return _read_zip_xml_text(file_path, "content.xml")[:FILE_READ_LIMIT], "ok"

        if ext == ".pdf":
            return _read_pdf_text(file_path)[:FILE_READ_LIMIT], "ok"

        return "", f"тип файла {ext or 'неизвестный'} не поддерживается"
    except Exception as exc:
        return "", f"не удалось извлечь текст ({exc.__class__.__name__})"
