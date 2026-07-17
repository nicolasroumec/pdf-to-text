import os
import sys
import threading
import tkinter as tk
from tkinter import ttk, filedialog
from pypdf import PdfReader

# Carpeta fija donde van todos los .txt: subcarpeta "txts" al lado del .exe
BASE = os.path.dirname(sys.executable if getattr(sys, "frozen", False) else __file__)
SALIDA = os.path.join(BASE, "txts")


def convertir(pdf_path):
    os.makedirs(SALIDA, exist_ok=True)
    reader = PdfReader(pdf_path)
    texto = "\n".join((p.extract_text() or "") for p in reader.pages)
    nombre = os.path.splitext(os.path.basename(pdf_path))[0] + ".txt"
    txt_path = os.path.join(SALIDA, nombre)
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(texto)
    return txt_path


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("PDF to Text")
        self.geometry("460x360")
        self.minsize(420, 320)
        self.configure(bg="#f4f4f5")

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
        ttk.Label(cont, text="Pick one or more PDFs. The .txt files go to the 'txts' folder.",
                  font=("Segoe UI", 9), foreground="#666").pack(anchor="w", pady=(2, 12))

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

    def abrir_carpeta(self):
        os.makedirs(SALIDA, exist_ok=True)
        os.startfile(SALIDA)  # ponytail: solo Windows, que es el target del .exe

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
                convertir(r)
                ok += 1
                self.escribir(f"OK    {base}")
            except Exception as e:
                self.escribir(f"FAIL  {base}: {e}")
            self.bar.configure(value=i)
        self.estado.configure(text=f"Done: {ok}/{total} converted.")
        self.btn.configure(state="normal")


if __name__ == "__main__":
    App().mainloop()
