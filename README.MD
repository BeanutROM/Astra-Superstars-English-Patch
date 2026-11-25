# Astra Superstars English Patch

An English translation patch for the Japanese Saturn and ST-V releases of **Astra Superstars**.
You need your own Japanese game bin/cue or mame rom zip set as no game files or copyrighted work is distributed here,

This was translated with the assistance of OpenAI Codex. The text was reviewed and edited by a human where necessary.

All text is translated in every screen, from the opening attract sequence to the final stories of each character -- except for the staff credits, I do not translate credit text.

This has been tested on Ymir and MiSTerFPGA Saturn and ST-V cores.

## Patching manually

### Saturn
Apply the xdelta patch to its matching original bin file

### ST-V
  - Apply the xdelta patch to each individual mame rom files
  - Use the included ST-V patcher script for windows:
    1. Unzip the ST-V patcher release to a directory
    2. Place your **astrass.zip** archive into this directory.
    3. Run **patch_stv.py** to create **astrassu.zip** in this directory

Q: Why a python script? I don't know what python is, and I can't run this!

A: You can patch manually with xdelta, you don't need this. It's also open source, and can be very easily audited to ensure it contains no malicious code.

## Source
Astra Superstars (Japan) (Track 1).bin

MD5 a8ca967f4cae449e8f1e32a65fb2d020

SHA1 929b608b3f8a9cf29e31c2e4590f386f1669f247

## Updates

- v2.0
  The previous release was absolute turbo garbage, and I apoligize for it. It should never have been released.
  - Fixed real hardware boot issue
  - Completed the Translation of all assets.
  - Fixed 2 graphical corruption issues, on the VS Player Selection Screen, and when fighting Sakamoto or My Devil.

- v1.0
  Initial, very broken release. Do not use.

## Support

If you enjoy this translation, please consider supporting me on Ko-fi:

[![Support me on Ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/beanutroms)
