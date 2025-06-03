import tkinter as tk
from tkinter import ttk
import csv

class CSVViewerApp:
    def __init__(self, caminho_csv):
        root = tk.Tk()
        self.root = root
        self.root.title("AgNose")
        self.root.geometry("600x400")

        # ======= ESTILO PARA A TABELA ========
        style = ttk.Style()
        style.theme_use("default")  # você pode usar 'clam' ou outro se preferir

        style.configure("Treeview",
                        background="#f8f8f8",
                        foreground="#333333",
                        rowheight=25,
                        fieldbackground="#f8f8f8",
                        font=("Segoe UI", 10))

        style.configure("Treeview.Heading",
                        background="#4a7a8c",
                        foreground="white",
                        font=("Segoe UI", 10, "bold"))

        style.map("Treeview",
                  background=[("selected", "#6fa3bf")],
                  foreground=[("selected", "white")])

        # Frame de controle
        frame_topo = ttk.Frame(root)
        frame_topo.pack(fill="x", padx=10, pady=5)

        self.entrada_busca = ttk.Entry(frame_topo)
        self.entrada_busca.pack(side="left", expand=True, fill="x", padx=5)
        self.entrada_busca.insert(0, "Buscar...")

        botao_filtrar = ttk.Button(frame_topo, text="Filtrar", command=self.filtrar_linhas)
        botao_filtrar.pack(side="left", padx=5)

        # Frame da tabela e scroll
        frame_tabela = ttk.Frame(root)
        frame_tabela.pack(expand=True, fill="both", padx=10, pady=5)

        self.scroll_y = ttk.Scrollbar(frame_tabela, orient="vertical")
        self.scroll_x = ttk.Scrollbar(frame_tabela, orient="horizontal")

        self.tree = ttk.Treeview(
            frame_tabela,
            yscrollcommand=self.scroll_y.set,
            xscrollcommand=self.scroll_x.set,
            show="headings"
        )

        self.scroll_y.config(command=self.tree.yview)
        self.scroll_y.pack(side="right", fill="y")

        self.scroll_x.config(command=self.tree.xview)
        self.scroll_x.pack(side="bottom", fill="x")

        self.tree.pack(expand=True, fill="both")

        self.linhas_originais = []

        # Carrega o CSV assim que o app inicia
        self.carregar_csv(caminho_csv)
        root.mainloop()

    def carregar_csv(self, caminho):
        try:
            with open(caminho, newline='', encoding='utf-8') as csvfile:
                leitor = csv.reader(csvfile)
                colunas = next(leitor)

                self.tree.delete(*self.tree.get_children())
                self.tree["columns"] = colunas
                self.tree["show"] = "headings"

                for col in colunas:
                    self.tree.heading(col, text=col)
                    self.tree.column(col, anchor="center", width=120)

                self.linhas_originais = list(leitor)
                self.preencher_tabela(self.linhas_originais)

        except Exception as e:
            print(f"Erro ao abrir o CSV: {e}")

    def preencher_tabela(self, linhas):
        self.tree.delete(*self.tree.get_children())
        for i, linha in enumerate(linhas):
            tag = "par" if i % 2 == 0 else "impar"
            self.tree.insert("", "end", values=linha, tags=(tag,))

        # Estilo alternado de linhas
        self.tree.tag_configure("par", background="#ffffff")
        self.tree.tag_configure("impar", background="#e6f2f5")

    def filtrar_linhas(self):
        termo = self.entrada_busca.get().lower().strip()
        if not termo or termo == "buscar...":
            self.preencher_tabela(self.linhas_originais)
            return

        linhas_filtradas = [
            linha for linha in self.linhas_originais
            if any(termo in str(celula).lower() for celula in linha)
        ]
        self.preencher_tabela(linhas_filtradas)
