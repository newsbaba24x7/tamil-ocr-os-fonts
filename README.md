# Tamil OCR test files from Windows and macOS fonts

This repository draws test files for the open Tamil OCR models (tam_v3.2, from
[tamil-tess-trainer](https://github.com/newsbaba24x7/tamil-tess-trainer)) with the Tamil fonts that come
with Windows and macOS. It does this on GitHub's own Windows and macOS runners.

## Rules

- **No font file is stored in this repository.** The fonts come with the runners' operating systems,
  including Windows' optional Tamil fonts.
- **The fonts are used only to make test files.** They are never used to train a model.
- **Results are PNG images and JSON lists only.** There are no PDFs, because a PDF carries pieces of
  the fonts. Results are kept as workflow artifacts for one day.
- **Text is open or in the public domain.** The sample line is from Puṟanāṉūṟu 192, which is in the
  public domain.
- **Real scanned documents are never put here.**

## What runs

**Workflow:** `OS Tamil fonts` (`.github/workflows/os-fonts.yml`). It is run by hand from the Actions tab.

**What it does, on `windows-latest` and `macos-latest`:**
1. **Windows only:** installs the optional Windows feature "Tamil Supplemental Fonts" (Latha and Vijaya).
2. **Lists every Tamil font on the runner** (`tools/list_fonts.py`), with its version, maker, licence fields and checksum.
3. **Draws one sample line in each font face** with headless Google Chrome (`tools/render_sample.py`).
   - Each face is chosen by its own full name and PostScript name, so Chrome draws exactly that face.
   - It also checks that Chrome really used that face rather than its default font.

Both scripts use only the Python standard library.

## Licence

The code in this repository is under the Apache License 2.0, the same as tamil-tess-trainer.

Thank you to the Tamil Wikisource and Tamil Virtual Academy communities, whose open work makes these
models possible.
