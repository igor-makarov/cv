from pathlib import Path
import re
import sys
import uuid
import zipfile

source_dir = Path(sys.argv[1])
output_path = Path(sys.argv[2])
font_dir = Path(__file__).resolve().parent.parent / "fonts"

required_parts = {
    "[Content_Types].xml",
    "_rels/.rels",
    "word/document.xml",
    "word/fontTable.xml",
    "word/styles.xml",
}
fonts = {
    "Carlito": {
        "embedRegular": "Carlito-Regular.ttf",
        "embedItalic": "Carlito-Italic.ttf",
    },
    "Carlito Bold": {
        "embedRegular": "Carlito-Bold.ttf",
    },
    "Caladea": {
        "embedRegular": "Caladea-Regular.ttf",
    },
    "Caladea Bold": {
        "embedRegular": "Caladea-Bold.ttf",
    },
}
relationship_type = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/font"
relationship_namespace = "http://schemas.openxmlformats.org/package/2006/relationships"


def obfuscate(font: bytes, key: uuid.UUID) -> bytes:
    result = bytearray(font)
    reversed_key = key.bytes[::-1]
    for index in range(32):
        result[index] ^= reversed_key[index % 16]
    return bytes(result)


parts = {
    path.relative_to(source_dir).as_posix(): path.read_bytes()
    for path in source_dir.rglob("*")
    if path.is_file()
    and ".DS_Store" not in path.relative_to(source_dir).parts
}
missing_parts = required_parts.difference(parts)
if missing_parts:
    raise SystemExit(f"Reference source is missing: {', '.join(sorted(missing_parts))}")

font_entries = []
for family, styles in fonts.items():
    for element, filename in styles.items():
        key = uuid.uuid5(uuid.NAMESPACE_URL, f"cv-font:{family}:{element}")
        relationship_id = f"font{len(font_entries) + 1}"
        font_entries.append((family, element, filename, key, relationship_id))

font_table = parts["word/fontTable.xml"]
for family in fonts:
    pattern = rb'(<w:font\b[^>]*\bw:name="' + family.encode() + rb'"[^>]*>.*?</w:font>)'
    match = re.search(pattern, font_table, flags=re.DOTALL)
    if not match:
        raise SystemExit(f"Reference font table does not declare {family}")
    declarations = []
    for entry_family, element, _, key, relationship_id in font_entries:
        if entry_family == family:
            declarations.append(
                f'<w:{element} r:id="{relationship_id}" w:fontKey="{{{str(key).upper()}}}"/>'.encode()
            )
    block = match.group(1).replace(b"</w:font>", b"".join(declarations) + b"</w:font>")
    font_table = font_table[: match.start(1)] + block + font_table[match.end(1) :]
parts["word/fontTable.xml"] = font_table

relationships = [
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
    f'<Relationships xmlns="{relationship_namespace}">',
]
for _, _, filename, _, relationship_id in font_entries:
    target = f"fonts/{Path(filename).stem}.odttf"
    relationships.append(
        f'<Relationship Id="{relationship_id}" Type="{relationship_type}" Target="{target}"/>'
    )
relationships.append("</Relationships>")
parts["word/_rels/fontTable.xml.rels"] = "".join(relationships).encode()

content_types = parts["[Content_Types].xml"]
font_content_type = (
    b'<Default Extension="odttf" '
    b'ContentType="application/vnd.openxmlformats-officedocument.obfuscatedFont"/>'
)
parts["[Content_Types].xml"] = content_types.replace(
    b"</Types>", font_content_type + b"</Types>"
)

for _, _, filename, key, _ in font_entries:
    source_path = font_dir / filename
    if not source_path.is_file():
        raise SystemExit(f"Missing font: {source_path}")
    target = f"word/fonts/{source_path.stem}.odttf"
    parts[target] = obfuscate(source_path.read_bytes(), key)

output_path.parent.mkdir(parents=True, exist_ok=True)
tmp_path = output_path.with_suffix(".docx.tmp")
with zipfile.ZipFile(tmp_path, "w") as archive:
    for name in sorted(parts):
        info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
        info.compress_type = zipfile.ZIP_DEFLATED
        info.create_system = 3
        info.external_attr = 0o100644 << 16
        archive.writestr(info, parts[name], compresslevel=9)

tmp_path.replace(output_path)
