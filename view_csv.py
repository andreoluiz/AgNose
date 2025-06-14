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
        # Atualiza a tabela ao digitar (sem botão)
        self.entrada_busca.bind("<KeyRelease>", lambda event: self.filtrar_linhas())

        # Botão removido (não usamos mais)
        # botao_filtrar = ttk.Button(frame_topo, text="Filtrar", command=self.filtrar_linhas)
        # botao_filtrar.pack(side="left", padx=(5, 0))

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
