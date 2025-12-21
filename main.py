import tkinter as tk
from interface import InterfaceGrafica
import database
import leitor_de_paginas
import threading
import webbrowser
from tkinter import messagebox

class AppController:
    def __init__(self):
        self.root = tk.Tk()
        self.view = InterfaceGrafica(self.root, self)
        
        self.urls = [
            "URL_1_AQUI",
            "URL_2_AQUI"
        ]
        database.inicializar_banco()
        self.carregar_do_banco()

    def disparar_busca(self):
        self.view.btn_buscar.config(state="disabled")
        self.view.lbl_status.config(text="Iniciando busca múltipla...", fg="blue")
        threading.Thread(target=self._task_busca_BDTD, daemon=True).start()

    def _task_busca_BDTD(self):
        try:
            resultados_finais = []
            for i, url in enumerate(self.urls):
                msg = f"Processando busca {i+1}/{len(self.urls)}..."
                self.root.after(0, lambda m=msg: self.view.lbl_status.config(text=m))
                
                res = leitor_de_paginas.realizar_busca_recursiva(url, lambda m: None)
                resultados_finais.extend(res)

            novos = database.salvar_resultados(resultados_finais)
            self.root.after(0, self.carregar_do_banco)
            self.root.after(0, lambda: messagebox.showinfo("Sucesso", f"Busca finalizada! {novos} novos itens."))
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Erro", str(e)))
        finally:
            self.root.after(0, lambda: self.view.btn_buscar.config(state="normal"))

    def carregar_do_banco(self):
        dados = database.recuperar_todos()
        self.view.tree.delete(*self.view.tree.get_children())
        for d in dados:
            # d agora é um objeto Row ou dicionário dependendo do seu database.py
            tag = 'juridico' if "Jurídico" in str(d['classificacao']) else 'nao_juridico'
            self.view.tree.insert("", "end", values=(
                d['id'], d['titulo'], d['autor'], d['universidade'], 
                d['programa'], d['classificacao'], "🔍 Ler Resumo", d['link']
            ), tags=(tag,))

    def clique_na_tabela(self, event):
        region = self.view.tree.identify_region(event.x, event.y)
        if region == "cell":
            col = self.view.tree.identify_column(event.x)
            item_id = self.view.tree.identify_row(event.y)
            if col == "#7": # Coluna Ação
                valores = self.view.tree.item(item_id, "values")
                link = valores[7]
                self._processar_detalhes(link)

    def _processar_detalhes(self, link):
        dados = database.buscar_trabalho_por_link(link)
        if dados and dados['resumo']:
            info = f"IES: {dados['universidade']}\nResumo: {dados['resumo']}"
            self.view.exibir_resumo(info)
        else:
            self.view.lbl_status.config(text="Extraindo detalhes via Selenium...", fg="orange")
            threading.Thread(target=self._task_scrap_detalhado, args=(link,), daemon=True).start()

    def _task_scrap_detalhado(self, link):
        try:
            res = leitor_de_paginas.ler_detalhes_trabalho(link)
            database.salvar_detalhes_completos(link, res['resumo'], res['programa'], res['universidade'], res['classificacao'])
            self.root.after(0, self.carregar_do_banco)
            self.root.after(0, lambda: self.view.exibir_resumo(res['resumo']))
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Erro Scrap", str(e)))

    def abrir_link(self, event):
        item = self.view.tree.selection()
        if item:
            link = self.view.tree.item(item, "values")[7]
            webbrowser.open(link)

    def ordenar_coluna(self, col, reverse):
        """Ordena a tabela quando o cabeçalho é clicado."""
        # Obtém todos os itens da tabela (ID do item e os valores)
        l = [(self.view.tree.set(k, col), k) for k in self.view.tree.get_children('')]

        # Tenta converter para número se a coluna for ID, para evitar erro de '10' vir antes de '2'
        try:
            l.sort(key=lambda t: float(t[0]) if t[0].isdigit() else t[0], reverse=reverse)
        except ValueError:
            l.sort(reverse=reverse)

        # Rearranja os itens na interface na nova ordem
        for index, (val, k) in enumerate(l):
            self.view.tree.move(k, '', index)

        # Inverte a ordem para o próximo clique (Toggle)
        self.view.tree.heading(col, command=lambda: self.ordenar_coluna(col, not reverse))

    def iniciar(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = AppController()
    app.iniciar()