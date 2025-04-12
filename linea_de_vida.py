import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import reportlab
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import os

# Clase principal
class LineaDeVidaApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Diseñador de Línea de Vida Avanzado")
        self.root.geometry("1000x600")

        self.puntos = []  # Lista de puntos de la silueta

        self.crear_widgets()

    def crear_widgets(self):
        self.frame_izq = ttk.Frame(self.root, padding=10)
        self.frame_izq.pack(side=tk.LEFT, fill=tk.Y)

        ttk.Label(self.frame_izq, text="Altura libre (m):").pack()
        self.altura_entry = ttk.Entry(self.frame_izq)
        self.altura_entry.insert(0, "6")
        self.altura_entry.pack()

        ttk.Label(self.frame_izq, text="Usuarios simultáneos:").pack()
        self.combo_usuarios = ttk.Combobox(self.frame_izq, values=[1, 2, 3], state="readonly")
        self.combo_usuarios.current(0)
        self.combo_usuarios.pack()

        ttk.Button(self.frame_izq, text="Calcular y Dibujar", command=self.calcular).pack(pady=10)
        ttk.Button(self.frame_izq, text="Exportar PDF", command=self.exportar_pdf).pack()
        ttk.Button(self.frame_izq, text="Borrar todo", command=self.borrar_todo).pack(pady=10)

        # Canvas de dibujo
        self.fig, self.ax = plt.subplots()
        self.ax.set_title("Dibuja la silueta (clic para añadir puntos)")
        self.ax.set_xlim(0, 50)
        self.ax.set_ylim(0, 30)
        self.ax.grid(True)

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.root)
        self.canvas.get_tk_widget().pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        self.canvas.mpl_connect("button_press_event", self.on_click)

    def on_click(self, event):
        if event.inaxes:
            self.puntos.append((event.xdata, event.ydata))
            self.ax.plot(event.xdata, event.ydata, 'bo')
            self.redibujar()

    def redibujar(self):
        self.ax.clear()
        self.ax.set_title("Silueta y línea de vida")
        self.ax.set_xlim(0, 50)
        self.ax.set_ylim(0, 30)
        self.ax.grid(True)
        if len(self.puntos) > 1:
            xs, ys = zip(*self.puntos)
            self.ax.plot(xs, ys, 'b-', label="Silueta")
        for x, y in self.puntos:
            self.ax.plot(x, y, 'bo')
        self.canvas.draw()

    def calcular(self):
        try:
            altura_libre = float(self.altura_entry.get())
            usuarios = int(self.combo_usuarios.get())
            if len(self.puntos) < 2:
                messagebox.showwarning("Atención", "Dibuja al menos dos puntos.")
                return

            # Calcular longitud total de la línea de vida
            longitud_total = sum(
                ((self.puntos[i+1][0]-self.puntos[i][0])**2 + (self.puntos[i+1][1]-self.puntos[i][1])**2)**0.5
                for i in range(len(self.puntos)-1))

            distancia_anclajes = 10
            num_anclajes = max(2, round(longitud_total / distancia_anclajes) + 1)
            tipo_linea = "Cable de acero" if longitud_total > 10 else "Cuerda flexible"
            carga = usuarios * 6
            altura_ok = altura_libre >= 6

            # Dibujar anclajes en la línea
            self.ax.clear()
            self.ax.set_xlim(0, 50)
            self.ax.set_ylim(0, 30)
            self.ax.grid(True)
            xs, ys = zip(*self.puntos)
            self.ax.plot(xs, ys, 'b-', label="Silueta")
            self.ax.plot(xs, ys, 'g--', label="Línea de vida")

            # Repartir anclajes equidistantes
            anclajes = [self.puntos[0]]
            acumulado = 0
            i = 0
            while len(anclajes) < num_anclajes:
                seg_len = ((self.puntos[i+1][0] - self.puntos[i][0])**2 + (self.puntos[i+1][1] - self.puntos[i][1])**2)**0.5
                acumulado += seg_len
                if acumulado >= distancia_anclajes:
                    anclajes.append(self.puntos[i+1])
                    acumulado = 0
                i += 1
                if i >= len(self.puntos)-1:
                    break

            for idx, (x, y) in enumerate(anclajes):
                self.ax.plot(x, y, 'ro')
                self.ax.text(x, y + 0.5, f"A{idx+1}", color='red')

            self.ax.legend()
            self.canvas.draw()

            # Guardar resultados para PDF
            self.resultado_pdf = {
                "longitud": round(longitud_total, 2),
                "anclajes": len(anclajes),
                "tipo": tipo_linea,
                "carga": carga,
                "altura_ok": altura_ok,
                "usuarios": usuarios,
                "altura": altura_libre,
                "anclajes_coords": anclajes
            }

        except Exception as e:
            messagebox.showerror("Error", str(e))

    def exportar_pdf(self):
        if not hasattr(self, 'resultado_pdf'):
            messagebox.showwarning("Primero calcula", "Realiza un cálculo antes de exportar.")
            return
        filepath = filedialog.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF files", "*.pdf")])
        if not filepath:
            return

        c = canvas.Canvas(filepath, pagesize=A4)
        c.setFont("Helvetica", 12)
        c.drawString(50, 800, "Informe de Línea de Vida")
        y = 770
        for key, val in self.resultado_pdf.items():
            if key != 'anclajes_coords':
                c.drawString(50, y, f"{key.capitalize()}: {val}")
                y -= 20

        c.drawString(50, y, "Coordenadas de Anclajes:")
        y -= 20
        for i, (x, yy) in enumerate(self.resultado_pdf['anclajes_coords']):
            c.drawString(60, y, f"A{i+1}: ({round(x,2)}, {round(yy,2)})")
            y -= 15

        # Exportar dibujo
        imagen_temp = "temp_figura.png"
        self.fig.savefig(imagen_temp)
        c.drawImage(imagen_temp, 50, 100, width=500, height=300)
        os.remove(imagen_temp)

        c.save()
        messagebox.showinfo("Éxito", f"PDF exportado a: {filepath}")

    def borrar_todo(self):
        self.puntos.clear()
        self.ax.clear()
        self.ax.set_title("Dibuja la silueta (clic para añadir puntos)")
        self.ax.set_xlim(0, 50)
        self.ax.set_ylim(0, 30)
        self.ax.grid(True)
        self.canvas.draw()

if __name__ == '__main__':
    root = tk.Tk()
    app = LineaDeVidaApp(root)
    root.mainloop()
