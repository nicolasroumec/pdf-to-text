import os
import sys
import json

# En modo --windowed no hay consola: pymupdf4llm imprime progreso y sys.stdout es None.
for _s in ("stdout", "stderr"):
    if getattr(sys, _s) is None:
        setattr(sys, _s, open(os.devnull, "w", encoding="utf-8"))

import threading
import tkinter as tk
from tkinter import ttk, filedialog
from pypdf import PdfReader
import pymupdf4llm

BASE = os.path.dirname(sys.executable if getattr(sys, "frozen", False) else __file__)
DEFAULT_SALIDA = os.path.join(BASE, "txts")  # por defecto: subcarpeta al lado del .exe
CONFIG = os.path.join(BASE, "config.json")


def cargar_config():
    try:
        with open(CONFIG, encoding="utf-8") as f:
            c = json.load(f)
    except (OSError, ValueError):
        c = {}
    return c.get("salida") or DEFAULT_SALIDA, c.get("formato") or "txt"


def guardar_config(ruta, formato):
    with open(CONFIG, "w", encoding="utf-8") as f:
        json.dump({"salida": ruta, "formato": formato}, f)


def convertir(pdf_path, salida, formato):
    os.makedirs(salida, exist_ok=True)
    if formato == "md":
        contenido = pymupdf4llm.to_markdown(pdf_path)  # títulos, listas, tablas
    else:
        reader = PdfReader(pdf_path)
        contenido = "\n".join((p.extract_text() or "") for p in reader.pages)
    nombre = os.path.splitext(os.path.basename(pdf_path))[0] + "." + formato
    out_path = os.path.join(salida, nombre)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(contenido)
    return out_path


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("PDF to Text")
        self.geometry("480x470")
        self.minsize(440, 430)
        self.configure(bg="#f4f4f5")
        self.salida, formato_ini = cargar_config()
        self.formato = tk.StringVar(value=formato_ini)

        st = ttk.Style(self)
        try:
            st.theme_use("vista")
        except tk.TclError:
            pass
        st.configure("TButton", padding=8, font=("Segoe UI", 10))
        st.configure("Big.TButton", padding=10, font=("Segoe UI", 11, "bold"))

        cont = ttk.Frame(self, padding=16)
        cont.pack(fill="both", expand=True)

        ttk.Label(cont, text="Convert PDF to Text",
                  font=("Segoe UI", 15, "bold")).pack(anchor="w")
        ttk.Label(cont, text="Pick one or more PDFs. Choose where the files are saved.",
                  font=("Segoe UI", 9), foreground="#666").pack(anchor="w", pady=(2, 12))

        # Fila de carpeta de salida
        dest = ttk.Frame(cont)
        dest.pack(fill="x", pady=(0, 10))
        ttk.Label(dest, text="Output folder:", font=("Segoe UI", 9, "bold")).pack(anchor="w")
        drow = ttk.Frame(dest)
        drow.pack(fill="x", pady=(2, 0))
        self.lbl_salida = ttk.Label(drow, text=self.salida, font=("Segoe UI", 9),
                                    foreground="#0a58ca")
        self.lbl_salida.pack(side="left", fill="x", expand=True)
        ttk.Button(drow, text="Change...", command=self.cambiar_salida).pack(side="left", padx=(6, 0))
        ttk.Button(drow, text="Default", command=self.reset_salida).pack(side="left", padx=(6, 0))

        # Formato de salida
        fmt = ttk.Frame(cont)
        fmt.pack(fill="x", pady=(0, 10))
        ttk.Label(fmt, text="Format:", font=("Segoe UI", 9, "bold")).pack(side="left")
        ttk.Radiobutton(fmt, text="Plain text (.txt)", value="txt",
                        variable=self.formato, command=self._save).pack(side="left", padx=(8, 0))
        ttk.Radiobutton(fmt, text="Markdown (.md)", value="md",
                        variable=self.formato, command=self._save).pack(side="left", padx=(8, 0))

        fila = ttk.Frame(cont)
        fila.pack(fill="x")
        self.btn = ttk.Button(fila, text="Choose PDF...", style="Big.TButton",
                              command=self.elegir)
        self.btn.pack(side="left")
        ttk.Button(fila, text="Open folder", command=self.abrir_carpeta).pack(
            side="left", padx=8)

        self.bar = ttk.Progressbar(cont, mode="determinate")
        self.bar.pack(fill="x", pady=(14, 4))
        self.estado = ttk.Label(cont, text="Ready.", font=("Segoe UI", 9),
                                foreground="#444")
        self.estado.pack(anchor="w")

        marco = ttk.Frame(cont)
        marco.pack(fill="both", expand=True, pady=(10, 0))
        self.log = tk.Text(marco, height=8, font=("Consolas", 9), state="disabled",
                           bg="#ffffff", relief="solid", borderwidth=1, wrap="none")
        sb = ttk.Scrollbar(marco, command=self.log.yview)
        self.log.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.log.pack(side="left", fill="both", expand=True)

    def escribir(self, linea):
        # ponytail: Tk no es thread-safe; el worker llama esto vía self.after
        self.log.configure(state="normal")
        self.log.insert("end", linea + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def _save(self):
        guardar_config(self.salida, self.formato.get())

    def _set_salida(self, ruta):
        self.salida = ruta
        self.lbl_salida.configure(text=ruta)
        self._save()

    def cambiar_salida(self):
        ruta = filedialog.askdirectory(title="Choose output folder", initialdir=self.salida)
        if ruta:
            self._set_salida(ruta)

    def reset_salida(self):
        self._set_salida(DEFAULT_SALIDA)

    def abrir_carpeta(self):
        os.makedirs(self.salida, exist_ok=True)
        os.startfile(self.salida)  # ponytail: solo Windows, que es el target del .exe

    def elegir(self):
        rutas = filedialog.askopenfilenames(
            title="Choose PDF(s)", filetypes=[("PDF", "*.pdf")])
        if rutas:
            self.btn.configure(state="disabled")
            threading.Thread(target=self.trabajar, args=(rutas,), daemon=True).start()

    def trabajar(self, rutas):
        total = len(rutas)
        fmt = self.formato.get()
        self.after(0, lambda: self.bar.configure(maximum=total, value=0))
        ok = 0
        for i, r in enumerate(rutas, 1):
            base = os.path.basename(r)
            self.after(0, lambda i=i, base=base:
                       self.estado.configure(text=f"Converting {i}/{total}: {base}"))
            try:
                convertir(r, self.salida, fmt)
                ok += 1
                self.after(0, lambda base=base: self.escribir(f"OK    {base}"))
            except Exception as e:
                self.after(0, lambda base=base, e=e: self.escribir(f"FAIL  {base}: {e}"))
            self.after(0, lambda i=i: self.bar.configure(value=i))
        self.after(0, lambda: self.estado.configure(text=f"Done: {ok}/{total} converted."))
        self.after(0, lambda: self.btn.configure(state="normal"))


if __name__ == "__main__":
    App().mainloop()
