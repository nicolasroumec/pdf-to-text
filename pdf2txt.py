import os
import sys
import json
import threading
import tkinter as tk
from tkinter import ttk, filedialog
from pypdf import PdfReader

BASE = os.path.dirname(sys.executable if getattr(sys, "frozen", False) else __file__)
DEFAULT_SALIDA = os.path.join(BASE, "txts")  # por defecto: subcarpeta al lado del .exe
CONFIG = os.path.join(BASE, "config.json")


def cargar_salida():
    try:
        with open(CONFIG, encoding="utf-8") as f:
            return json.load(f).get("salida") or DEFAULT_SALIDA
    except (OSError, ValueError):
        return DEFAULT_SALIDA


def guardar_salida(ruta):
    with open(CONFIG, "w", encoding="utf-8") as f:
        json.dump({"salida": ruta}, f)


def convertir(pdf_path, salida):
    os.makedirs(salida, exist_ok=True)
    reader = PdfReader(pdf_path)
    texto = "\n".join((p.extract_text() or "") for p in reader.pages)
    nombre = os.path.splitext(os.path.basename(pdf_path))[0] + ".txt"
    txt_path = os.path.join(salida, nombre)
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(texto)
    return txt_path


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("PDF to Text")
        self.geometry("480x420")
        self.minsize(440, 380)
        self.configure(bg="#f4f4f5")
        self.salida = cargar_salida()

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
        ttk.Label(cont, text="Pick one or more PDFs. Choose where the .txt files are saved.",
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
        self.log.configure(state="normal")
        self.log.insert("end", linea + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def _set_salida(self, ruta):
        self.salida = ruta
        self.lbl_salida.configure(text=ruta)
        guardar_salida(ruta)

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
        self.bar.configure(maximum=total, value=0)
        ok = 0
        for i, r in enumerate(rutas, 1):
            base = os.path.basename(r)
            self.estado.configure(text=f"Converting {i}/{total}: {base}")
            try:
                convertir(r, self.salida)
                ok += 1
                self.escribir(f"OK    {base}")
            except Exception as e:
                self.escribir(f"FAIL  {base}: {e}")
            self.bar.configure(value=i)
        self.estado.configure(text=f"Done: {ok}/{total} converted.")
        self.btn.configure(state="normal")


if __name__ == "__main__":
    App().mainloop()
