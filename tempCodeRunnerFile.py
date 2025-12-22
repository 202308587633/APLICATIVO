 Exception as e:
            # Captura a mensagem de erro imediatamente como string
            erro_texto = str(e)
            self.root.after(0, lambda: self.view.lbl_status.config(
                text="Erro ao extrair detalhes.", fg="red"
            ))
            # Usa o argumento padrão m=erro_texto para preservar o valor no lambda
            self.root.after(0, lambda m=erro_texto: messagebox.showerror(
                "Erro no Scrap Detalhado", f"Falha ao processar:\n{m}"
            ))