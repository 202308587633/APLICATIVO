import sys
import os

# Garante que o Python encontre os módulos na pasta atual
sys.path.append(os.getcwd())

from database import ScraperDB
from services.strategies import BDTDStrategy

def run_reparse():
    print("="*60)
    print("INICIANDO REPROCESSAMENTO DE PROGRAMAS (MODO TEXTO)")
    print("="*60)

    try:
        # 1. Conecta ao Banco de Dados
        db = ScraperDB()
        print("Banco de dados conectado.")

        # 2. Busca todos os registros
        all_rows = db.fetch_all()
        
        # 3. Filtra itens sem programa (Coluna 6 = Programa)
        # Ajuste o índice 6 se a ordem das colunas no seu banco for diferente
        pendentes = [row for row in all_rows if row[6] == '-' or row[6] is None or row[6] == '']
        
        total = len(pendentes)
        if total == 0:
            print("Nenhum registro com programa pendente ('-') encontrado.")
            return

        print(f"Encontrados {total} itens para reprocessar.")
        print("-" * 60)

        # 4. Instancia a estratégia de parsers
        strategy = BDTDStrategy()
        
        atualizados = 0
        erros = 0

        # 5. Loop de Processamento
        for i, row in enumerate(pendentes):
            db_id = row[0]
            link_repo = row[8] # Coluna do Link do Repositório
            sigla_atual = row[4]

            print(f"[{i+1}/{total}] Processando ID {db_id} ({sigla_atual})... ", end='', flush=True)

            try:
                # Recupera o HTML salvo (tipo 'repo')
                html = db.get_specific_html(db_id, 'repo')
                
                if not html:
                    print("PULADO (HTML vazio).")
                    continue

                # Reprocessa usando o parser adequado para o link_repo
                # Passa None no on_progress para não poluir o terminal, ou print se quiser detalhes
                data = strategy.parse_from_stored_html(html, link_repo)
                
                novo_programa = data.get('programa')
                nova_universidade = data.get('universidade')

                # Verifica se houve melhoria na extração
                if novo_programa and novo_programa not in ['-', 'None', '']:
                    # Atualiza no banco
                    db.update_record_details(db_id, data)
                    print(f"SUCESSO -> {novo_programa}")
                    atualizados += 1
                else:
                    print("SEM MUDANÇA.")

            except Exception as e:
                print(f"ERRO: {e}")
                erros += 1

        print("="*60)
        print("RESUMO DO PROCESSAMENTO")
        print(f"Total Processado: {total}")
        print(f"Atualizados:      {atualizados}")
        print(f"Erros:            {erros}")
        print("="*60)

    except Exception as main_e:
        print(f"Erro Crítico no Script: {main_e}")

if __name__ == "__main__":
    run_reparse()
    input("\nPressione ENTER para sair...")