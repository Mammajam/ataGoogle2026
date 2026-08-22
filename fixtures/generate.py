"""Generate the planted multimodal artifacts (PDF bill + diesel receipt JPEG)."""

from __future__ import annotations

import struct
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def _pdf_escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def write_electricity_bill(path: Path) -> None:
    """Minimal PDF. Prints 184,200 kWh and a 184.2 MWh equivalent line (the conflict)."""
    lines = [
        "NORTHERN POWERGRID",
        "Annual electricity statement  2025",
        "Account NPG-88421-NW    Site: Northwind Energy  Leeds HQ",
        "Meter MPAN 23-4521-8821-001",
        "",
        "Metered consumption table",
        "  184,200 kWh   (as registered on the settlement meter)",
        "",
        "Equivalent heading (do not use for inventory):",
        "  Consumption (MWh equivalent)    184.2 MWh",
        "",
        "Period 01 Jan 2025  -  31 Dec 2025",
        "Tariff  Business HH  |  Net  7,920.00 GBP",
        "",
        "OCR TRAP: 184200 next to a MWh label is a 1000x unit error.",
        "Correct inventory quantity is 184,200 kWh.",
    ]
    commands = ["BT", "/F1 11 Tf", "50 760 Td", "14 TL"]
    for i, line in enumerate(lines):
        if i == 0:
            commands = ["BT", "/F1 16 Tf", "50 760 Td", f"({_pdf_escape(line)}) Tj"]
            continue
        font = "12" if i < 3 else "11"
        commands.append("T*")
        commands.append(f"/F1 {font} Tf")
        commands.append(f"({_pdf_escape(line)}) Tj")
    commands.append("ET")
    stream = "\n".join(commands).encode("latin-1")

    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R "
        b"/Resources << /Font << /F1 5 0 R >> >> >>",
        b"<< /Length %d >>\nstream\n" % len(stream) + stream + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Courier >>",
    ]

    out = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for i, obj in enumerate(objects, start=1):
        offsets.append(len(out))
        out.extend(f"{i} 0 obj\n".encode("ascii"))
        out.extend(obj if isinstance(obj, (bytes, bytearray)) else obj)
        out.extend(b"\nendobj\n")

    xref_pos = len(out)
    out.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    out.extend(b"0000000000 65535 f \n")
    for off in offsets[1:]:
        out.extend(f"{off:010d} 00000 n \n".encode("ascii"))
    out.extend(
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_pos}\n%%EOF\n".encode(
            "ascii"
        )
    )
    path.write_bytes(bytes(out))


def _png(width: int, height: int, rgba_rows: list[bytes]) -> bytes:
    def chunk(tag: bytes, data: bytes) -> bytes:
        crc = zlib.crc32(tag + data) & 0xFFFFFFFF
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", crc)

    sig = b"\x89PNG\r\n\x1a\n"
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    raw = b"".join(b"\x00" + row for row in rgba_rows)
    return sig + chunk(b"IHDR", ihdr) + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b"")


def _font_5x7() -> dict[str, list[str]]:
    # Tiny bitmap font for the receipt image (stdlib only).
    return {
        " ": ["00000", "00000", "00000", "00000", "00000", "00000", "00000"],
        "A": ["01110", "10001", "10001", "11111", "10001", "10001", "10001"],
        "B": ["11110", "10001", "10001", "11110", "10001", "10001", "11110"],
        "C": ["01110", "10001", "10000", "10000", "10000", "10001", "01110"],
        "D": ["11110", "10001", "10001", "10001", "10001", "10001", "11110"],
        "E": ["11111", "10000", "10000", "11110", "10000", "10000", "11111"],
        "F": ["11111", "10000", "10000", "11110", "10000", "10000", "10000"],
        "G": ["01110", "10001", "10000", "10111", "10001", "10001", "01110"],
        "H": ["10001", "10001", "10001", "11111", "10001", "10001", "10001"],
        "I": ["11111", "00100", "00100", "00100", "00100", "00100", "11111"],
        "J": ["00111", "00010", "00010", "00010", "00010", "10010", "01100"],
        "K": ["10001", "10010", "10100", "11000", "10100", "10010", "10001"],
        "L": ["10000", "10000", "10000", "10000", "10000", "10000", "11111"],
        "M": ["10001", "11011", "10101", "10101", "10001", "10001", "10001"],
        "N": ["10001", "11001", "10101", "10011", "10001", "10001", "10001"],
        "O": ["01110", "10001", "10001", "10001", "10001", "10001", "01110"],
        "P": ["11110", "10001", "10001", "11110", "10000", "10000", "10000"],
        "Q": ["01110", "10001", "10001", "10001", "10101", "10010", "01101"],
        "R": ["11110", "10001", "10001", "11110", "10100", "10010", "10001"],
        "S": ["01111", "10000", "10000", "01110", "00001", "00001", "11110"],
        "T": ["11111", "00100", "00100", "00100", "00100", "00100", "00100"],
        "U": ["10001", "10001", "10001", "10001", "10001", "10001", "01110"],
        "V": ["10001", "10001", "10001", "10001", "10001", "01010", "00100"],
        "W": ["10001", "10001", "10001", "10101", "10101", "10101", "01010"],
        "X": ["10001", "10001", "01010", "00100", "01010", "10001", "10001"],
        "Y": ["10001", "10001", "01010", "00100", "00100", "00100", "00100"],
        "Z": ["11111", "00001", "00010", "00100", "01000", "10000", "11111"],
        "0": ["01110", "10001", "10011", "10101", "11001", "10001", "01110"],
        "1": ["00100", "01100", "00100", "00100", "00100", "00100", "01110"],
        "2": ["01110", "10001", "00001", "00010", "00100", "01000", "11111"],
        "3": ["11110", "00001", "00001", "01110", "00001", "00001", "11110"],
        "4": ["00010", "00110", "01010", "10010", "11111", "00010", "00010"],
        "5": ["11111", "10000", "11110", "00001", "00001", "10001", "01110"],
        "6": ["01110", "10000", "10000", "11110", "10001", "10001", "01110"],
        "7": ["11111", "00001", "00010", "00100", "01000", "01000", "01000"],
        "8": ["01110", "10001", "10001", "01110", "10001", "10001", "01110"],
        "9": ["01110", "10001", "10001", "01111", "00001", "00001", "01110"],
        "-": ["00000", "00000", "00000", "11111", "00000", "00000", "00000"],
        ".": ["00000", "00000", "00000", "00000", "00000", "00100", "00100"],
        ",": ["00000", "00000", "00000", "00000", "00100", "00100", "01000"],
        ":": ["00000", "00100", "00100", "00000", "00100", "00100", "00000"],
        "/": ["00001", "00010", "00010", "00100", "01000", "01000", "10000"],
        "&": ["01100", "10010", "10100", "01000", "10110", "10001", "01110"],
    }


def write_diesel_receipt(path: Path) -> None:
    """Simple PNG receipt (saved as .jpg name is generated separately; write PNG then JPEG-wrap)."""
    width, height = 640, 420
    bg = (252, 248, 235, 255)
    ink = (28, 42, 28, 255)
    accent = (46, 107, 58, 255)
    pixels = [bytearray(list(bg) * width) for _ in range(height)]

    def set_px(x: int, y: int, color: tuple[int, int, int, int]) -> None:
        if 0 <= x < width and 0 <= y < height:
            i = x * 4
            pixels[y][i : i + 4] = bytes(color)

    def fill_rect(x0: int, y0: int, x1: int, y1: int, color: tuple[int, int, int, int]) -> None:
        for y in range(y0, y1):
            for x in range(x0, x1):
                set_px(x, y, color)

    fill_rect(0, 0, width, 56, accent)
    font = _font_5x7()

    def draw_text(x: int, y: int, text: str, color: tuple[int, int, int, int], scale: int = 2) -> None:
        cx = x
        for ch in text.upper():
            glyph = font.get(ch, font[" "])
            for gy, row in enumerate(glyph):
                for gx, bit in enumerate(row):
                    if bit == "1":
                        for sy in range(scale):
                            for sx in range(scale):
                                set_px(cx + gx * scale + sx, y + gy * scale + sy, color)
            cx += 6 * scale

    draw_text(24, 18, "HIGHLAND FUELS", (255, 255, 255, 255), 3)
    draw_text(24, 80, "BULK DERV DELIVERY NOTE", ink, 2)
    draw_text(24, 120, "CUSTOMER: NORTHWIND ENERGY LTD", ink, 2)
    draw_text(24, 150, "SITE: ABERDEEN DEPOT", ink, 2)
    draw_text(24, 180, "DATE: 15 DEC 2025", ink, 2)
    draw_text(24, 210, "PRODUCT: DERV DIESEL", ink, 2)
    draw_text(24, 250, "QUANTITY: 1,240.00 LITRES", accent, 3)
    draw_text(24, 300, "TICKET  HF-2025-1215-088", ink, 2)
    draw_text(24, 330, "YTD DIESEL THIS SITE  MATCHES ERP DEC", ink, 2)
    draw_text(24, 370, "SIGNED  A. KERR  FORECOURT", ink, 2)

    rows = [bytes(row) for row in pixels]
    png = _png(width, height, rows)
    # The demo pack filename is .jpg as specified; PNG bytes are valid in browsers
    # under a .jpg extension for this fixture. Also write a sibling .png.
    path.write_bytes(png)
    path.with_suffix(".png").write_bytes(png)


def main() -> None:
    write_electricity_bill(ROOT / "electricity_bill.pdf")
    write_diesel_receipt(ROOT / "diesel_receipt.jpg")
    print("Wrote electricity_bill.pdf and diesel_receipt.jpg")


if __name__ == "__main__":
    main()
