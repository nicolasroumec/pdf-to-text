# PDF to Text

Small desktop app (Tkinter) to convert PDFs to `.txt`. Pick one or more PDFs
and the text files are written to a `txts/` folder next to the app.

## Run from source

```bash
pip install -r requirements.txt
python pdf2txt.py
```

## Build the .exe (Windows)

```bash
python -m PyInstaller --onefile --windowed --name PDFtoText pdf2txt.py
```

The executable ends up in `dist/PDFtoText.exe`. Share that single file — it
runs without Python installed.

## Notes

- Scanned/image-only PDFs come out empty (no OCR).
