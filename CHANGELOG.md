# Changes

## 26 November 2026 (third version)

- **New: the side-check lines.** `tools/render_lines.py` draws, in every Tamil font face, up to 100 common
  lines and up to 30 lines with special characters (the 161 characters being added to the Tamil models,
  and Tamil numerals).
  - A line is used only if the face can draw every character in it, so Chrome never borrows another font.
    The one exception is the space: a few fonts have no space character, and such faces are marked
    `space_from_fallback`.
  - Each face's lines are drawn in one tall picture, one line per row, at 48 pixels, black on white. The same
    lines are also drawn in Chrome's default font, to check that the face was really used.
- **New: `text/lines.json` and `text/ATTRIBUTION.md`.** The lines are pieces of Tamil Wikipedia sentences (CC
  BY-SA 4.0, every article credited) and lines written for this project. None of them is ever used for training.
- **The workflow draws the side-check lines** after the sample line.

## 26 November 2026 (second version)

- **Each font face is now chosen by its own full name and PostScript name** (CSS `local()`).
  - The first version chose faces by family name, weight and italic flag. Three things went wrong:
    - a face whose family name was read in another language (macOS's InaiMathi) was not found;
    - bold and italic faces were checked against a regular-weight fallback picture, so a bold fallback
      looked like a success;
    - a face with a weight value outside the CSS range (some fonts store 17661) made Chrome ignore the
      whole style and draw small text in its default font.
- **Every face is now drawn at the same size and style**, so one picture in Chrome's default font is enough
  to compare with. If a face's picture is the same, the face is marked "not used".
- **Font names in English come first** when a font stores its names in several languages.
- **The PostScript name is now listed** for every face.
- **Each picture is named after the face's PostScript name.**
- **Pictures are saved with a full path.** On Windows, Chrome did not save a picture given a relative path,
  so the first run stopped at the first font.
- **The results are uploaded even when a step fails**, so the font list is never lost.

## 26 November 2026 (first version)

- **First version:** lists every Tamil font on GitHub's Windows and macOS runners, installs Windows'
  optional Tamil fonts, and draws one sample line in each font.
