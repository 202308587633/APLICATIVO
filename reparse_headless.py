import sys
import os
from datetime import datetime

# Garante que o Python encontre os módulos na pasta atual
sys.path.append(os.getcwd())

from database import ScraperDB
from services.strategies import BDTDStrategy

# Mapeamento dos índices conforme ordem do método fetch_all() no database.py
IDX_ID = 0
IDX_SIGLA = 5
IDX_UNIV = 6
IDX_PROG = 7
IDX_PDF = 8
IDX_REPO = 9

def run_reparse():
    print("="*80)
    print(f"REPROCESSAMENTO DE DADOS (HEADLESS) - {datetime.now().strftime('%H:%M:%S')}")
    print("="*80)

    # --- NOVO: Menu de Seleção de Filtro ---
    print("Selecione o critério para reprocessar os registros:")
    print("  [S] Apenas se a SIGLA estiver vazia/traço ('-')")
    print("  [N] Apenas se o NOME DA UNIVERSIDADE estiver vazio/traço ('-')")
    print("  [P] Apenas se o PROGRAMA estiver vazio/traço ('-')")
    print("  [ENTER] Se QUALQUER campo principal estiver pendente (Padrão)")
    
    opcao = input("\nSua escolha: ").strip().upper()
    
    campo_alvo = None
    desc_filtro = "Qualquer campo pendente"

    if opcao == 'S':
        campo_alvo = 'sigla'
        desc_filtro = "Apenas Sigla pendente"
    elif opcao == 'N':
        campo_alvo = 'universidade'
        desc_filtro = "Apenas Universidade pendente"
    elif opcao == 'P':
        campo_alvo = 'programa'
        desc_filtro = "Apenas Programa pendente"

    print(f"\n> Filtro Ativo: {desc_filtro}")
    print("-" * 80)

    try:
        # 1. Conexão
        db = ScraperDB()
        strategy = BDTDStrategy()
        
        # 2. Busca todos os registros
        all_rows = db.fetch_all()
        total_rows = len(all_rows)
        print(f"Banco conectado. Total de registros no banco: {total_rows}")

        relatorio_mudancas = []
        processados = 0
        erros = 0
        ignorados = 0

        print("Iniciando análise...")

        # 3. Loop de Processamento
        for row in all_rows:
            db_id = row[IDX_ID]
            link_repo = row[IDX_REPO]
            
            # Valores atuais no banco
            atual = {
                'sigla': row[IDX_SIGLA],
                'universidade': row[IDX_UNIV],
                'programa': row[IDX_PROG],
                'link_pdf': row[IDX_PDF]
            }

            # --- LÓGICA DE FILTRAGEM APRIMORADA ---
            valores_invalidos = ['-', '', None]
            deve_processar = False

            if not link_repo or len(link_repo) < 5:
                # Sem link do repositório, impossível reprocessar
                deve_processar = False
            elif campo_alvo:
                # Usuário escolheu um campo específico (S, N ou P)
                if atual.get(campo_alvo) in valores_invalidos:
                    deve_processar = True
            else:
                # Padrão: Processa se qualquer um dos campos principais for inválido
                if any(v in valores_invalidos for v in atual.values()):
                    deve_processar = True

            if not deve_processar:
                ignorados += 1
                continue

            try:
                # Recupera o HTML salvo
                html = db.get_specific_html(db_id, 'repo')
                
                if not html:
                    # Se não tem HTML salvo, pula
                    continue

                # --- EXTRAÇÃO ---
                novos_dados = strategy.parse_from_stored_html(html, link_repo)
                
                # --- COMPARAÇÃO E ATUALIZAÇÃO ---
                alteracoes = []
                dados_para_salvar = atual.copy() 
                houve_mudanca = False

                campos_chave = ['sigla', 'universidade', 'programa', 'link_pdf']

                for campo in campos_chave:
                    novo_valor = novos_dados.get(campo)
                    valor_antigo = atual.get(campo)

                    valido = novo_valor and novo_valor not in valores_invalidos
                    diferente = novo_valor != valor_antigo

                    # Só atualiza se o novo valor for válido E diferente do atual
                    # (Ou se o usuário mandou focar num campo e achamos algo para ele)
                    if valido and diferente:
                        dados_para_salvar[campo] = novo_valor
                        alteracoes.append(f"{campo.upper()}: '{valor_antigo}' -> '{novo_valor}'")
                        houve_mudanca = True
                    
                    # Mantém o valor antigo se o novo for ruim
                    elif (not valido) and valor_antigo:
                        dados_para_salvar[campo] = valor_antigo

                if houve_mudanca:
                    db.update_record_details(db_id, dados_para_salvar)
                    
                    relatorio_mudancas.append({
                        'id': db_id,
                        'mudancas': alteracoes
                    })
                    print(f"✅ ID {db_id}: {', '.join(alteracoes)}")
                    processados += 1
                
            except Exception as e:
                print(f"❌ Erro no ID {db_id}: {e}")
                erros += 1

        # 4. Exibição do Resumo
        print("\n" + "="*80)
        print("RESUMO DETALHADO DAS ALTERAÇÕES")
        print("="*80)
        
        if not relatorio_mudancas:
            print(f"Nenhuma alteração realizada com o filtro '{desc_filtro}'.")
        else:
            print(f"{'ID':<6} | {'ALTERAÇÕES REALIZADAS'}")
            print("-" * 80)
            for item in relatorio_mudancas:
                mudancas_str = " | ".join(item['mudancas'])
                print(f"{item['id']:<6} | {mudancas_str}")

        print("="*80)
        print(f"Total Registros:    {total_rows}")
        print(f"Filtro Aplicado:    {desc_filtro}")
        print(f"Ignorados (Filtro): {ignorados}")
        print(f"Atualizados:        {processados}")
        print(f"Erros:              {erros}")
        print("="*80)

    except Exception as main_e:
        print(f"Erro Crítico no Script: {main_e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_reparse()
    input("\nPressione ENTER para sair...")
    