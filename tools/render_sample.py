#!/usr/bin/env python3
"""Draw one sample line in every Tamil font face found by list_fonts.py, with headless Google Chrome.

  python render_sample.py FONTS.json OUT_DIR

Chrome shapes Tamil with HarfBuzz on every system, so Windows, macOS and Linux draw the same way.
Each face is chosen by its own full name and PostScript name (CSS local()), so its weight value, its
italic flag and the language of its family name do not matter. Chrome draws exactly that face, without
making it bolder or slanted. If Chrome cannot find the face, it draws the line in its default font
instead; that picture is drawn once, and any face whose picture is the same is marked "not used".
Output: one PNG per face and OUT_DIR/samples.json. The sample text is public-domain Sangam poetry
(Purananuru 192) plus digits, Tamil numerals and a few signs; nothing else is written.
"""
import hashlib, html, json, os, platform, shutil, subprocess, sys, tempfile

TEXT = "யாதும் ஊரே யாவரும் கேளிர் ௧௨௩ 123 ₹ 45% 37°C Tamil OCR"


def chrome():
    for p in (os.environ.get("CHROME", ""),
              r"C:\Program Files\Google\Chrome\Application\chrome.exe",
              r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
              "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
              shutil.which("google-chrome") or "", shutil.which("chromium") or "", shutil.which("chrome") or ""):
        if p and os.path.exists(p): return p
    sys.exit("Google Chrome not found; set CHROME to its path")


def css_string(s):
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ") + '"'


def shot(exe, names, png, tmp):
    """Draw TEXT in the face with one of these unique names; with no names, in Chrome's default font."""
    face = ""
    if names:
        face = "@font-face{font-family:'Face Under Test';src:" + ",".join(f"local({css_string(n)})" for n in names) + "}"
    page = os.path.join(tmp, "p.html")
    with open(page, "w", encoding="utf-8") as f:
        f.write(f"""<!doctype html><meta charset="utf-8"><style>{face}html,body{{margin:0;background:#fff}}
p{{margin:24px;font:normal 400 40px 'Face Under Test','No Such Font 12345';color:#000;white-space:nowrap}}</style>
<p>{html.escape(TEXT)}</p>""")
    subprocess.run([exe, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--no-first-run",
                    f"--user-data-dir={os.path.join(tmp, 'profile')}", "--window-size=1500,120",
                    f"--screenshot={png}", "file:///" + page.replace(os.sep, "/").lstrip("/")],
                   check=True, capture_output=True, timeout=120)
    return hashlib.sha256(open(png, "rb").read()).hexdigest()


def main():
    # A full path: Chrome on Windows does not save a screenshot given a relative path.
    fonts = json.load(open(sys.argv[1], encoding="utf-8"))["fonts"]; out = os.path.abspath(sys.argv[2])
    os.makedirs(out, exist_ok=True); exe = chrome(); res = []; used_names = set()
    with tempfile.TemporaryDirectory() as tmp:
        missing = shot(exe, [], os.path.join(tmp, "fallback.png"), tmp)
        for r in fonts:
            if "error" in r: continue
            names = [n for n in dict.fromkeys((r.get("full_name"), r.get("postscript_name"))) if n]
            base = r.get("postscript_name") or f"{r.get('family')}_{r.get('style')}"
            base = "".join(ch if ch.isascii() and ch.isalnum() or ch in "-_" else "_" for ch in base)
            while base in used_names: base += "_"
            used_names.add(base)
            png = os.path.join(out, base + ".png")
            ok = shot(exe, names, png, tmp) != missing
            res.append({"family": r.get("typo_family") or r.get("family"), "style": r.get("typo_style") or r.get("style"),
                        "full_name": r.get("full_name"), "postscript_name": r.get("postscript_name"),
                        "weight": r.get("weight_class"), "italic": r.get("italic", False), "png": os.path.basename(png),
                        "font_used": ok, "font_file": os.path.basename(r["file"]), "face": r["face"]})
            print(f"  {'ok      ' if ok else 'NOT USED'} {' / '.join(names)} -> {os.path.basename(png)}")
    json.dump({"system": platform.platform(), "text": TEXT, "chosen_by": "CSS local() with the full name and PostScript name",
               "samples": res}, open(os.path.join(out, "samples.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"{sum(r['font_used'] for r in res)} of {len(res)} faces drawn in their own font")


if __name__ == "__main__":
    main()
