#!/usr/bin/env python3
"""Draw the font side-check lines in every Tamil font face found by list_fonts.py, with headless Chrome.

  python render_lines.py FONTS.json LINES.json OUT_DIR [--common 100] [--extra 30]

LINES.json holds two lists of lines, each {"id", "text", "source"}:
  "common": lines for every face (natural Tamil sentences, and our own lines with numbers and signs);
  "extra":  lines that hold the characters being checked (the 161 characters and Tamil numerals).
For each face:
  - its own character map (cmap) is read, and a line is used only if the face can draw every character
    in it, so Chrome never borrows another font;
  - the first --common lines it can draw are taken in order (so most faces get the same lines), and then
    up to --extra lines that add characters not yet covered, at most two lines per character;
  - the face is chosen by its own full name and PostScript name (CSS local()), as in render_sample.py;
  - all its lines are drawn in one tall picture, one line per fixed row, and the same lines are drawn
    again in Chrome's default font; if both pictures are the same, the face is marked "not used".
Output per face: <PostScriptName>.png and an entry in OUT_DIR/lines.json (the text of every row). The
lines are cut out of the pictures later, on the computer that scores them. Standard library only.
"""
import argparse, hashlib, html, json, os, platform, struct, subprocess, sys, tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import list_fonts as lf  # noqa: E402
from render_sample import chrome, css_string  # noqa: E402

SIZE, ROW, PAD, WIDTH = 48, 96, 32, 3600   # text size, row height, top/bottom margin, picture width (px);
                                            # 2,800 px was too narrow for the widest C-DAC fonts
MAX_ROWS = 160                              # keeps each picture under Chrome's size limit


def codepoints(path, face):
    b = open(path, "rb").read(); t = lf.tables(b, lf.faces(b)[face])
    o, _ = t["cmap"]; n = struct.unpack(">H", b[o + 2:o + 4])[0]; got = set()
    for i in range(n):
        _, _, so = struct.unpack(">HHI", b[o + 4 + 8 * i: o + 12 + 8 * i]); s = o + so
        fmt = struct.unpack(">H", b[s:s + 2])[0]
        if fmt == 4:
            segx2 = struct.unpack(">H", b[s + 6:s + 8])[0]; seg = segx2 // 2
            ends = struct.unpack(f">{seg}H", b[s + 14:s + 14 + segx2])
            starts = struct.unpack(f">{seg}H", b[s + 16 + segx2:s + 16 + 2 * segx2])
            for a, z in zip(starts, ends):
                if a != 0xFFFF: got.update(range(a, z + 1))
        elif fmt == 12:
            for g in range(struct.unpack(">I", b[s + 12:s + 16])[0]):
                a, z, _ = struct.unpack(">III", b[s + 16 + 12 * g: s + 28 + 12 * g]); got.update(range(a, z + 1))
    return got


def drawable(text, cps):
    # A space is always allowed: a few fonts (the Ranganathan-Neechalkaran fonts, for example) have no space
    # character, and Chrome then takes only the gap's width from another font. Such faces are marked
    # "space_from_fallback" in lines.json.
    return all(ord(ch) in cps or ch == " " for ch in text)


def choose(lines, cps, common, extra):
    got = [l for l in lines["common"] if drawable(l["text"], cps)][:common]
    seen = {}
    for l in got:
        for ch in set(l["text"]): seen[ch] = seen.get(ch, 0) + 1
    more = []
    for l in lines["extra"]:
        if len(more) >= extra: break
        if not drawable(l["text"], cps): continue
        if any(seen.get(ch, 0) < 2 for ch in set(l["text"]) if not ch.isspace()):
            more.append(l)
            for ch in set(l["text"]): seen[ch] = seen.get(ch, 0) + 1
    return got + more


def page(lines, names, path):
    face = ""
    if names:
        face = "@font-face{font-family:'Face Under Test';src:" + ",".join(f"local({css_string(n)})" for n in names) + "}"
    rows = "".join(f"<div>{html.escape(l['text'])}</div>" for l in lines)
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"""<!doctype html><meta charset="utf-8"><style>{face}html,body{{margin:0;background:#fff}}
body{{padding:{PAD}px 0}}div{{height:{ROW}px;line-height:{ROW}px;padding-left:32px;white-space:nowrap;overflow:hidden;
font:normal 400 {SIZE}px 'Face Under Test','No Such Font 12345';color:#000}}</style>{rows}""")


def shot(exe, html_path, png, rows, tmp):
    subprocess.run([exe, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--no-first-run",
                    f"--user-data-dir={os.path.join(tmp, 'profile')}", f"--window-size={WIDTH},{rows * ROW + 2 * PAD}",
                    f"--screenshot={png}", "file:///" + html_path.replace(os.sep, "/").lstrip("/")],
                   check=True, capture_output=True, timeout=300)
    return hashlib.sha256(open(png, "rb").read()).hexdigest()


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("fonts"); ap.add_argument("lines"); ap.add_argument("out")
    ap.add_argument("--common", type=int, default=100); ap.add_argument("--extra", type=int, default=30)
    a = ap.parse_args()
    fonts = json.load(open(a.fonts, encoding="utf-8"))["fonts"]; lines = json.load(open(a.lines, encoding="utf-8"))
    out = os.path.abspath(a.out); os.makedirs(out, exist_ok=True); exe = chrome(); res = []; used = set()
    with tempfile.TemporaryDirectory() as tmp:
        for r in fonts:
            if "error" in r: continue
            names = [n for n in dict.fromkeys((r.get("full_name"), r.get("postscript_name"))) if n]
            cps = codepoints(r["file"], r["face"])
            chosen = choose(lines, cps, a.common, a.extra)[:MAX_ROWS]
            base = r.get("postscript_name") or f"{r.get('family')}_{r.get('style')}"
            base = "".join(ch if ch.isascii() and ch.isalnum() or ch in "-_" else "_" for ch in base)
            while base in used: base += "_"
            used.add(base)
            if not chosen:
                res.append({"face": base, "full_name": r.get("full_name"), "font_used": False, "lines": [], "note": "no line drawable"}); continue
            hp = os.path.join(tmp, "p.html"); png = os.path.join(out, base + ".png")
            page(chosen, names, hp); h = shot(exe, hp, png, len(chosen), tmp)
            page(chosen, [], hp); h0 = shot(exe, hp, os.path.join(tmp, "fallback.png"), len(chosen), tmp)
            res.append({"face": base, "full_name": r.get("full_name"), "postscript_name": r.get("postscript_name"),
                        "font_file": os.path.basename(r["file"]), "face_index": r["face"], "font_used": h != h0, "png": base + ".png",
                        "space_from_fallback": 0x20 not in cps,
                        "lines": [{"row": i, "id": l["id"], "text": l["text"]} for i, l in enumerate(chosen)]})
            print(f"  {'ok      ' if h != h0 else 'NOT USED'} {r.get('full_name')}: {len(chosen)} lines -> {base}.png")
    json.dump({"system": platform.platform(), "size_px": SIZE, "row_px": ROW, "pad_px": PAD, "width_px": WIDTH,
               "chosen_by": "CSS local() with the full name and PostScript name", "faces": res},
              open(os.path.join(out, "lines.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"{sum(f['font_used'] for f in res)} of {len(res)} faces drawn in their own font; "
          f"{sum(len(f['lines']) for f in res)} lines")


if __name__ == "__main__":
    main()
