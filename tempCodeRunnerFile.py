
    def solicitar_busca_sucupira(self):
        """Abre um diálogo para o usuário informar a sigla."""
        sigla = simpledialog.askstring("Plataforma Sucupira", "Informe a Sigla da Universidade:")
        if sigla:
            self.lbl_status.config(text=f"Buscando ID Sucupira para {sigla}...", fg="orange")
            # Dispara thread para não travar a UI
            threading.Thread(target=self.processar_sucupira, args=(sigla,), daemon=True).start()

    def processar_sucupira(self, sigla):
        """Executa a raspagem e salva no banco de dados."""
        id_sucupira = scraper_sucupira.buscar_id_sucupira(sigla)
        
        if id_sucupira:
            try:
                # Salva no banco usando a função que já temos no database.py
                salvar_id_sucupira(sigla, id_sucupira)
                
                msg = f"Sucesso! ID {id_sucupira} vinculado à {sigla}."
                self.root.after(0, lambda: messagebox.showinfo("Sucupira", msg))
                self.root.after(0, lambda: self.lbl_status.config(text=msg, fg="green"))
            except Exception as e:
                err = str(e)
                self.root.after(0, lambda: messagebox.showerror("Erro Banco", f"Falha ao salvar: {err}"))
        else:
            self.root.after(0, lambda: messagebox.showwarning("Sucupira", "Instituição não localizada na busca geral."))
            self.root.after(0, lambda: self.lbl_status.config(text="Busca Sucupira falhou.", fg="red"))