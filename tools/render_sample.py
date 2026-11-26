#!/usr/bin/env python3
"""Draw one sample line in every Tamil font face found by list_fonts.py, with headless Google Chrome.

  python render_sample.py FONTS.json OUT_DIR

Chrome shapes Tamil with HarfBuzz on every system, so Windows, macOS and Linux draw the same way.
For each face it also draws the line in a font name that does not exist; if both pictures are the
same, Chrome fell back to another font and the face is marked "not used". Output: one PNG per face
and OUT_DIR/samples.json. The sample text is public-domain Sangam poetry (Purananuru 192) plus
digits, Tamil numerals and a few signs; nothing else is written.
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


def shot(exe, family, weight, italic, png, tmp):
    page = os.path.join(tmp, "p.html")
    with open(page, "w", encoding="utf-8") as f:
        f.write(f"""<!doctype html><meta charset="utf-8"><style>html,body{{margin:0;background:#fff}}
p{{margin:24px;font:{'italic ' if italic else ''}{weight} 40px '{html.escape(family)}';color:#000;white-space:nowrap}}</style>
<p>{html.escape(TEXT)}</p>""")
    subprocess.run([exe, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--no-first-run",
                    f"--user-data-dir={os.path.join(tmp, 'profile')}", "--window-size=1500,120",
                    f"--screenshot={png}", "file:///" + page.replace(os.sep, "/").lstrip("/")],
                   check=True, capture_output=True, timeout=120)
    return hashlib.sha256(open(png, "rb").read()).hexdigest()


def main():
    fonts = json.load(open(sys.argv[1], encoding="utf-8"))["fonts"]; out = sys.argv[2]
    os.makedirs(out, exist_ok=True); exe = chrome(); res = []
    with tempfile.TemporaryDirectory() as tmp:
        missing = shot(exe, "No Such Font 12345", 400, False, os.path.join(tmp, "fallback.png"), tmp)
        for r in fonts:
            if "error" in r: continue
            fam = r.get("typo_family") or r.get("family"); w = r.get("weight_class", 400); it = r.get("italic", False)
            name = "".join(ch if ch.isalnum() else "_" for ch in f"{fam}_{w}_{'italic' if it else 'upright'}")
            png = os.path.join(out, name + ".png")
            h = shot(exe, fam, w, it, png, tmp)
            res.append({"family": fam, "weight": w, "italic": it, "png": os.path.basename(png), "font_used": h != missing,
                        "font_file": os.path.basename(r["file"]), "face": r["face"]})
            print(f"  {'ok      ' if h != missing else 'NOT USED'} {fam} weight {w}{' italic' if it else ''} -> {os.path.basename(png)}")
    json.dump({"system": platform.platform(), "text": TEXT, "samples": res}, open(os.path.join(out, "samples.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(f"{sum(r['font_used'] for r in res)} of {len(res)} faces drawn in their own font")


if __name__ == "__main__":
    main()
