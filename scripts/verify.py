from pathlib import Path
import re
import sys
import zipfile
import zlib
import xml.etree.ElementTree as ET

pdf_path = Path(sys.argv[1])
docx_path = Path(sys.argv[2])
html_path = Path(sys.argv[3])

pdf = pdf_path.read_bytes()
searchable_pdf = bytearray(pdf)
for stream in re.finditer(rb"stream\r?\n(.*?)\r?\nendstream", pdf, re.DOTALL):
    try:
        searchable_pdf.extend(zlib.decompress(stream.group(1)))
    except zlib.error:
        pass
page_count = len(re.findall(rb"/Type\s*/Page\b", searchable_pdf))
if page_count != 1:
    raise SystemExit(f"PDF contains {page_count} pages, expected 1")
media_box = re.search(rb"/MediaBox\s*\[\s*0\s+0\s+([0-9.]+)\s+([0-9.]+)\s*\]", searchable_pdf)
if not media_box:
    raise SystemExit("PDF has no readable MediaBox")
width_pt, height_pt = map(float, media_box.groups())
width_mm = width_pt * 25.4 / 72
height_mm = height_pt * 25.4 / 72
if abs(width_mm - 210) > 0.2 or abs(height_mm - 297) > 0.2:
    raise SystemExit(f"PDF page is {width_mm:.1f} × {height_mm:.1f} mm, expected A4")

with zipfile.ZipFile(docx_path) as archive:
    root = ET.fromstring(archive.read("word/document.xml"))
    font_table = archive.read("word/fontTable.xml")
    styles = archive.read("word/styles.xml")
    expected_fonts = {
        "word/fonts/Carlito-Regular.odttf",
        "word/fonts/Carlito-Italic.odttf",
        "word/fonts/Carlito-Bold.odttf",
        "word/fonts/Caladea-Regular.odttf",
        "word/fonts/Caladea-Bold.odttf",
    }
    missing_fonts = expected_fonts.difference(archive.namelist())
    if missing_fonts:
        raise SystemExit(f"DOCX is missing embedded fonts: {', '.join(sorted(missing_fonts))}")
    for family in (b"Carlito", b"Carlito Bold", b"Caladea", b"Caladea Bold"):
        if family not in font_table:
            raise SystemExit(f"DOCX font table does not declare {family.decode()}")
    if not re.search(rb"<w:b\s*/>", styles) or not re.search(rb"<w:bCs\s*/>", styles):
        raise SystemExit("DOCX styles do not declare semantic bold formatting")

ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
page_size = root.find(".//w:sectPr/w:pgSz", ns)
if page_size is None:
    raise SystemExit("DOCX has no page-size declaration")
w = int(page_size.attrib[f"{{{ns['w']}}}w"])
h = int(page_size.attrib[f"{{{ns['w']}}}h"])
if (w, h) not in {(11906, 16838), (11907, 16840)}:
    raise SystemExit(f"DOCX page is {w} × {h} twips, expected A4")
page_margins = root.find(".//w:sectPr/w:pgMar", ns)
if page_margins is None:
    raise SystemExit("DOCX has no page-margin declaration")
top = int(page_margins.attrib[f"{{{ns['w']}}}top"])
bottom = int(page_margins.attrib[f"{{{ns['w']}}}bottom"])
if (top, bottom) != (1559, 1135):
    raise SystemExit(f"DOCX margins are {top}/{bottom} twips, expected 1559/1135")

for path in (pdf_path, docx_path, html_path):
    if not path.is_file() or path.stat().st_size == 0:
        raise SystemExit(f"Missing or empty output: {path}")

print(f"Verified one-page A4 PDF ({width_mm:.1f} × {height_mm:.1f} mm) and A4 DOCX")
