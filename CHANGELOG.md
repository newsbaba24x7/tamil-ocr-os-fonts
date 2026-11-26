# Changes

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
