#!/usr/bin/env python3
"""List every font on this computer that can draw Tamil. Standard library only.

  python list_fonts.py OUT.json [FONT_DIR ...]

Without FONT_DIR it scans the usual system font folders of Windows, macOS or Linux. Font collections
(.ttc) are read face by face. For each Tamil font it records: file, face index, family, typographic
family, style, full name, PostScript name, version, copyright, maker, licence text, vendor ID, embedding setting,
weight class, italic flag, how many Tamil code points (U+0B80-0BFF) it maps, glyph count and the
file's SHA-256. Fonts are only read, never copied.
"""
import hashlib, json, os, platform, struct, sys

NAME_IDS = {0: "copyright", 1: "family", 2: "style", 4: "full_name", 5: "version", 6: "postscript_name",
            8: "maker", 13: "licence", 14: "licence_url", 16: "typo_family", 17: "typo_style"}


def default_dirs():
    s = platform.system()
    if s == "Windows":
        return [os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts"),
                os.path.join(os.environ.get("LOCALAPPDATA", ""), "Microsoft", "Windows", "Fonts")]
    if s == "Darwin":
        return ["/System/Library/Fonts", "/Library/Fonts", os.path.expanduser("~/Library/Fonts"),
                "/System/Library/AssetsV2"]
    return ["/usr/share/fonts", "/usr/local/share/fonts", os.path.expanduser("~/.local/share/fonts")]


def faces(b):
    if b[:4] == b"ttcf":
        n = struct.unpack(">I", b[8:12])[0]
        return [struct.unpack(">I", b[12 + 4 * i:16 + 4 * i])[0] for i in range(n)]
    return [0]


def tables(b, off):
    n = struct.unpack(">H", b[off + 4:off + 6])[0]; t = {}
    for i in range(n):
        tag, _, o, ln = struct.unpack(">4sIII", b[off + 12 + 16 * i: off + 28 + 16 * i])
        t[tag.decode("latin-1")] = (o, ln)
    return t


def names(b, t):
    if "name" not in t: return {}
    o, _ = t["name"]; _, count, soff = struct.unpack(">HHH", b[o:o + 6]); best = {}
    for i in range(count):
        pid, eid, lid, nid, ln, so = struct.unpack(">HHHHHH", b[o + 6 + 12 * i: o + 18 + 12 * i])
        if nid not in NAME_IDS: continue
        raw = b[o + soff + so: o + soff + so + ln]
        # English names first, on any platform: a name in another language (InaiMathi's Hindi name on
        # macOS, for example) is not the name other programs use to find the font.
        if pid in (0, 3): s, rank = raw.decode("utf-16-be", "replace"), (0 if lid in (0x409, 0) else 2)
        elif pid == 1: s, rank = raw.decode("mac_roman", "replace"), (1 if lid == 0 else 3)
        else: continue
        if nid not in best or rank < best[nid][0]: best[nid] = (rank, s.strip())
    return {NAME_IDS[k]: v[1] for k, v in best.items()}


def tamil_count(b, t):
    if "cmap" not in t: return 0
    o, _ = t["cmap"]; n = struct.unpack(">H", b[o + 2:o + 4])[0]; got = set()
    for i in range(n):
        _, _, so = struct.unpack(">HHI", b[o + 4 + 8 * i: o + 12 + 8 * i]); s = o + so
        fmt = struct.unpack(">H", b[s:s + 2])[0]
        if fmt == 4:
            segx2 = struct.unpack(">H", b[s + 6:s + 8])[0]; seg = segx2 // 2
            ends = struct.unpack(f">{seg}H", b[s + 14:s + 14 + segx2])
            starts = struct.unpack(f">{seg}H", b[s + 16 + segx2:s + 16 + 2 * segx2])
            for a, z in zip(starts, ends): got.update(range(max(a, 0x0B80), min(z, 0x0BFF) + 1))
        elif fmt == 12:
            for g in range(struct.unpack(">I", b[s + 12:s + 16])[0]):
                a, z, _ = struct.unpack(">III", b[s + 16 + 12 * g: s + 28 + 12 * g])
                got.update(range(max(a, 0x0B80), min(z, 0x0BFF) + 1))
    return len(got)


def main():
    out, dirs = sys.argv[1], sys.argv[2:] or default_dirs()
    found, seen = [], set()
    for d in dirs:
        for root, _, files in os.walk(d):
            for fn in files:
                if not fn.lower().endswith((".ttf", ".otf", ".ttc", ".otc")): continue
                p = os.path.join(root, fn)
                try: b = open(p, "rb").read()
                except OSError: continue
                sha = hashlib.sha256(b).hexdigest()
                for idx, off in enumerate(faces(b)):
                    if (sha, idx) in seen: continue
                    seen.add((sha, idx))
                    try:
                        t = tables(b, off); n = tamil_count(b, t)
                        if n < 40: continue
                        r = {"file": p, "face": idx, "sha256": sha, "tamil_codepoints": n}
                        r.update(names(b, t))
                        if "OS/2" in t:
                            o = t["OS/2"][0]
                            r["weight_class"] = struct.unpack(">H", b[o + 4:o + 6])[0]
                            fs = struct.unpack(">H", b[o + 8:o + 10])[0]
                            r["embedding"] = "installable" if fs & 0xF == 0 else "restricted" if fs & 2 else "preview & print" if fs & 4 else "editable" if fs & 8 else hex(fs)
                            r["vendor_id"] = b[o + 58:o + 62].decode("latin-1", "replace").strip()
                            r["italic"] = bool(struct.unpack(">H", b[o + 62:o + 64])[0] & 1)
                        if "maxp" in t: r["glyphs"] = struct.unpack(">H", b[t["maxp"][0] + 4:t["maxp"][0] + 6])[0]
                        found.append(r)
                    except Exception as e:  # report and keep going
                        found.append({"file": p, "face": idx, "error": repr(e)})
    found.sort(key=lambda r: (r.get("typo_family") or r.get("family") or "", r.get("weight_class", 0), r.get("italic", False)))
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    json.dump({"system": platform.platform(), "dirs": dirs, "fonts": found}, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"{len(found)} Tamil font faces on {platform.platform()}")
    for r in found:
        print(f"  {r.get('full_name') or r.get('family')} | weight {r.get('weight_class')} | {'italic' if r.get('italic') else 'upright'}"
              f" | version {r.get('version')} | {r.get('embedding')} | {os.path.basename(r['file'])}#{r['face']}")


if __name__ == "__main__":
    main()
