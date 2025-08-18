import tkinter as tk
from tkinter import ttk
import csv

class PlaceholderEntry(ttk.Entry):
    def __init__(self, master=None, placeholder="", style_normal="TEntry", style_placeholder="Placeholder.TEntry", **kwargs):
        self.placeholder = placeholder
        self.style_normal = style_normal
        self.style_placeholder = style_placeholder

        style = ttk.Style(master)
        style.configure(style_normal, foreground="black")
        style.configure(style_placeholder, foreground="grey")

        super().__init__(master, style=style_placeholder, **kwargs)

        self.insert(0, self.placeholder)
        self._has_placeholder = True

        self.bind("<FocusIn>", self._on_focus_in)
        self.bind("<FocusOut>", self._on_focus_out)

    def _on_focus_in(self, event):
        if self._has_placeholder:
            self.delete(0, tk.END)
            self.configure(style=self.style_normal)
            self._has_placeholder = False

    def _on_focus_out(self, event):
        if not self.get():
            self.insert(0, self.placeholder)
            self.configure(style=self.style_placeholder)
            self._has_placeholder = True

    def get(self):
        if self._has_placeholder:
            return ""
        else:
            return super().get()

class CSVViewerApp:
    def __init__(self, caminho_csv, caminho_icon):
        root = tk.Tk()
        self.root = root
        self.root.iconbitmap(rf"{caminho_icon[:-3]}ico")
        self.root.title("AgNose")
        self.root.geometry("600x400")
        style = ttk.Style()
        style.theme_use("clam")

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

        frame_topo = ttk.Frame(root)
        frame_topo.pack(fill="x", padx=10, pady=5)

        self.imagem_info = tk.PhotoImage(file=caminho_icon)
        label_imagem = ttk.Label(frame_topo, image=self.imagem_info)
        label_imagem.pack(side="left", padx=(0, 5))

        self.entrada_busca = PlaceholderEntry(frame_topo, placeholder="Buscar...")
        self.entrada_busca.pack(side="left", expand=True, fill="x", padx=5)
        self.entrada_busca.bind("<KeyRelease>", lambda event: self.filtrar_linhas())

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
        self.ordem_colunas = {}  # ← Novo: estado de ordenação por coluna
        self.colunas = []

        self.carregar_csv(caminho_csv)
        root.mainloop()

    def carregar_csv(self, caminho):
        try:
            with open(caminho, newline='', encoding='utf-8') as csvfile:
                leitor = csv.reader(csvfile)
                self.colunas = next(leitor)

                self.tree.delete(*self.tree.get_children())
                self.tree["columns"] = self.colunas
                self.tree["show"] = "headings"

                for col in self.colunas:
                    self.tree.heading(col, text=col, command=lambda c=col: self.ordenar_por_coluna(c))
                    self.tree.column(col, anchor="center", width=120)

                self.linhas_originais = list(leitor)
                self.preencher_tabela(self.linhas_originais)

        except Exception as e:
            print(f"Erro ao abrir o CSV: {e}")

    def preencher_tabela(self, linhas):
        self.tree.delete(*self.tree.get_children())

        for i, linha in enumerate(linhas):
            # alterna fundo da linha (par/impar)
            tag = "par" if i % 2 == 0 else "impar"

            # insere a linha
            item_id = self.tree.insert("", "end", values=linha, tags=(tag,))

            # Agora percorre célula por célula para aplicar destaque
            for j, valor in enumerate(linha):
                if str(valor).lower() == "yes" or (str(valor).isdigit() and int(valor) != 0):
                    # cria uma tag única para essa célula
                    tag_name = f"cell_{i}_{j}"
                    self.tree.tag_configure(tag_name, foreground="red")
                    self.tree.item(item_id, tags=(tag, tag_name))

        # mantém estilo de zebra
        self.tree.tag_configure("par", background="#ffffff")
        self.tree.tag_configure("impar", background="#e6f2f5")


    def filtrar_linhas(self):
        termo = self.entrada_busca.get().lower().strip()
        if not termo:
            self.preencher_tabela(self.linhas_originais)
            return

        linhas_filtradas = [
            linha for linha in self.linhas_originais
            if any(termo in str(celula).lower() for celula in linha)
        ]
        self.preencher_tabela(linhas_filtradas)

    def ordenar_por_coluna(self, coluna):
        try:
            idx_coluna = self.colunas.index(coluna)
            ordem_atual = self.ordem_colunas.get(coluna, "asc")

            linhas = self.tree.get_children()
            dados = [self.tree.item(linha)["values"] for linha in linhas]

            try:
                dados.sort(key=lambda x: float(x[idx_coluna]), reverse=(ordem_atual == "desc"))
            except ValueError:
                dados.sort(key=lambda x: str(x[idx_coluna]).lower(), reverse=(ordem_atual == "desc"))

            nova_ordem = "desc" if ordem_atual == "asc" else "asc"
            self.ordem_colunas[coluna] = nova_ordem

            # Atualiza título do cabeçalho com a seta
            for col in self.colunas:
                seta = ""
                if col == coluna:
                    seta = " ↓" if nova_ordem == "desc" else " ↑"
                self.tree.heading(col, text=col + seta, command=lambda c=col: self.ordenar_por_coluna(c))

            self.preencher_tabela(dados)

        except Exception as e:
            print(f"Erro ao ordenar a coluna {coluna}: {e}")
