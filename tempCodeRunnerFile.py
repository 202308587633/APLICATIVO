import tkinter as tk
from tkinter import ttk, messagebox
import threading
import leitor_de_paginas

class AppPesquisa:
    def __init__(self, root):
        self.root = root
        self.root.title("Buscador Acadêmico RAG")
        self.root.geometry("800x500")

        # --- Elementos da Interface ---
        tk.Label(root, text="URL do BDTD:", font=("Arial", 10, "bold")).pack(pady=5)
        
        url = "https://bdtd.ibict.br/vufind/Search/Results?join=AND&bool0%5B%5D=AND&lookfor0%5B%5D=%22an%C3%A1lise+de+discurso%22&type0%5B%5D=AllFields&lookfor0%5B%5D=direito&type0%5B%5D=AllFields&illustration=-1&daterange%5B%5D=publishDate&publishDatefrom=2021&publishDateto=2021"

        self.ent_url = tk.Entry(root, width=80)
        self.ent_url.pack(pady=5)
        self.ent_url.insert(0, url)        

        self.btn_buscar = tk.Button(root, text="Iniciar Busca", command=self.disparar_busca, bg="green", fg="white")
        self.btn_buscar.pack(pady=10)

        self.lbl_status = tk.Label(root, text="Aguardando comando...", fg="blue")
        self.lbl_status.pack()

        # --- Tabela de Resultados (Treeview) ---
        self.tree = ttk.Treeview(root, columns=("Título", "Autor"), show='headings')
        self.tree.heading("Título", text="Título do Trabalho")
        self.tree.heading("Autor", text="Autor")
        self.tree.column("Título", width=500)
        self.tree.column("Autor", width=250)
        self.tree.pack(pady=10, fill="both", expand=True)

    def disparar_busca(self):
        url = self.ent_url.get()
        if not url:
            messagebox.showwarning("Aviso", "Insira uma URL válida!")
            return

        # Mudamos o estado da interface para o usuário saber que algo está acontecendo
        self.btn_buscar.config(state="disabled")
        self.lbl_status.config(text="Buscando dados no IBICT... aguarde.", fg="orange")
        
        # Criamos a Thread para não travar a janela
        thread = threading.Thread(target=self.processar_em_segundo_plano, args=(url,))
        thread.start()

    def processar_em_segundo_plano(self, url):
        try:
            dados = leitor_de_paginas.buscar_trabalhos(url)
            
            # Para atualizar a interface (Treeview), precisamos voltar para a Main Thread
            self.root.after(0, self.atualizar_tabela, dados)
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Erro", f"Falha na busca: {e}"))
            self.root.after(0, lambda: self.btn_buscar.config(state="normal"))

    def atualizar_tabela(self, dados):
        # Limpa a tabela anterior
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Insere os novos dados
        for d in dados:
            self.tree.insert("", "end", values=(d["Título"], d["Autor"]))

        self.lbl_status.config(text=f"Busca finalizada! {len(dados)} trabalhos encontrados.", fg="green")
        self.btn_buscar.config(state="normal")

if __name__ == "__main__":
    root = tk.Tk()
    app = AppPesquisa(root)
    root.mainloop()

