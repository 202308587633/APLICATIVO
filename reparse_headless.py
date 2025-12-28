import sys
import os
from datetime import datetime
from bs4 import BeautifulSoup

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

def is_valid_url(url):
    """
    Verifica se uma URL é válida para ser considerada um repositório.
    Ignora links vazios, Lattes e Busca Textual.
    """
    if not url or len(url) < 5:
        return False
    url_lower = url.lower()
    if "lattes.cnpq.br" in url_lower:
        return False
    if "buscatextual" in url_lower:
        return False
    return True

def run_reparse():
    print("="*80)
    print(f"REPROCESSAMENTO DE DADOS (HEADLESS) - {datetime.now().strftime('%H:%M:%S')}")
    print("="*80)

    # --- Menu de Seleção de Filtro ---
    print("Selecione o critério para reprocessar os registros:")
    print("  [S] Apenas se a SIGLA estiver vazia/traço ('-')")
    print("  [N] Apenas se o NOME DA UNIVERSIDADE estiver vazio/traço ('-')")
    print("  [P] Apenas se o PROGRAMA estiver vazio/traço ('-')")
    print("  [U] Apenas se a URL DO REPOSITÓRIO estiver vazia/traço ('-')")
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
    elif opcao == 'U':
        campo_alvo = 'link_repo'
        desc_filtro = "Apenas URL Repositório pendente"

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

        # Lista expandida de valores considerados inválidos
        valores_invalidos = ['-', '', None, 'None', '[s.n.]', 'Não Informado pela instituição']

        # 3. Loop de Processamento
        for row in all_rows:
            db_id = row[IDX_ID]
            link_repo_atual = row[IDX_REPO]
            
            # Valores atuais no banco
            atual = {
                'sigla': row[IDX_SIGLA],
                'universidade': row[IDX_UNIV],
                'programa': row[IDX_PROG],
                'link_pdf': row[IDX_PDF],
                'link_repo': link_repo_atual
            }

            # --- LÓGICA DE FILTRAGEM ---
            deve_processar = False
            link_invalido = not is_valid_url(link_repo_atual)

            if campo_alvo == 'link_repo':
                if link_invalido or link_repo_atual in valores_invalidos:
                    deve_processar = True
            elif link_invalido:
                # Se não temos link do repo, verificamos se temos o HTML da BDTD para tentar recuperar
                if db.get_specific_html(db_id, 'bdtd'):
                     deve_processar = True
                else:
                     deve_processar = False
            elif campo_alvo:
                if atual.get(campo_alvo) in valores_invalidos:
                    deve_processar = True
            else:
                if any(v in valores_invalidos for v in atual.values()):
                    deve_processar = True

            if not deve_processar:
                ignorados += 1
                continue

            try:
                alteracoes = []
                dados_para_salvar = atual.copy() 
                houve_mudanca = False

                # ==============================================================================
                # ETAPA 1: Processar HTML da BDTD (Recuperar Link, Sigla e Universidade)
                # ==============================================================================
                html_bdtd = db.get_specific_html(db_id, 'bdtd')
                if html_bdtd:
                    try:
                        soup_bdtd = BeautifulSoup(html_bdtd, 'html.parser')
                        found_link = None
                        
                        # --- 1.1 Recuperação de Link do Repositório ---
                        # Estratégia A: Tabela de metadados
                        for th in soup_bdtd.find_all('th'):
                            if any(x in th.get_text() for x in ["Link de acesso", "Texto completo", "URI", "Online"]):
                                td = th.find_next_sibling('td')
                                if td:
                                    for link in td.find_all('a', href=True):
                                        href = link['href']
                                        if is_valid_url(href):
                                            found_link = href
                                            break
                            if found_link: break

                        # Estratégia B: Botão Online
                        if not found_link:
                            access = soup_bdtd.select_one('.onlineUrl')
                            if access:
                                for link in access.find_all('a', href=True):
                                    href = link['href']
                                    if is_valid_url(href):
                                        found_link = href
                                        break
                        
                        # Atualiza link se encontrou um válido e diferente/novo
                        if found_link and found_link != link_repo_atual and "bdtd.ibict.br" not in found_link:
                             link_repo_atual = found_link
                             dados_para_salvar['link_repo'] = found_link
                             alteracoes.append(f"URL: Recuperada da BDTD -> '{found_link}'")
                             houve_mudanca = True

                        # --- 1.2 Recuperação de Sigla e Universidade (Metadados Ocultos) ---
                        
                        # Verifica Sigla (se inválida ou vazia)
                        if dados_para_salvar.get('sigla') in valores_invalidos:
                            # Busca por "instacron_str" na tabela
                            th_sigla = soup_bdtd.find('th', string=lambda t: t and 'instacron_str' in t)
                            if th_sigla:
                                td = th_sigla.find_next_sibling('td')
                                if td:
                                    nova_sigla = td.get_text(strip=True)
                                    if nova_sigla and nova_sigla not in valores_invalidos:
                                        dados_para_salvar['sigla'] = nova_sigla
                                        alteracoes.append(f"SIGLA: Recuperada da BDTD (Técnico) -> '{nova_sigla}'")
                                        houve_mudanca = True

                        # Verifica Universidade (se inválida, vazia ou [s.n.])
                        if dados_para_salvar.get('universidade') in valores_invalidos:
                            # Busca por "instname_str"
                            th_univ = soup_bdtd.find('th', string=lambda t: t and 'instname_str' in t)
                            if th_univ:
                                td = th_univ.find_next_sibling('td')
                                if td:
                                    nova_univ = td.get_text(strip=True)
                                    # Limpeza: "Universidade (SIGLA)" -> "Universidade"
                                    if '(' in nova_univ:
                                        nova_univ = nova_univ.split('(')[0].strip()
                                    
                                    if nova_univ and nova_univ not in valores_invalidos:
                                        dados_para_salvar['universidade'] = nova_univ
                                        alteracoes.append(f"UNIV: Recuperada da BDTD (Técnico) -> '{nova_univ}'")
                                        houve_mudanca = True

                    except Exception as e_bdtd:
                        print(f"Aviso: Erro ao processar HTML da BDTD (ID {db_id}): {e_bdtd}")

                # ==============================================================================
                # ETAPA 2: Processar HTML do Repositório (Programa, PDF, Validações Finais)
                # ==============================================================================
                html_repo = db.get_specific_html(db_id, 'repo')
                
                if html_repo:
                    # Usa o link atualizado (ou o antigo) para ajudar no parse
                    novos_dados = strategy.parse_from_stored_html(html_repo, link_repo_atual if link_repo_atual else "-")
                    
                    # Campos que o parser do repositório costuma extrair melhor
                    campos_repo = ['sigla', 'universidade', 'programa', 'link_pdf']

                    for campo in campos_repo:
                        novo_valor = novos_dados.get(campo)
                        valor_antigo = dados_para_salvar.get(campo) # Usa o que já temos (pode ter vindo da BDTD)

                        # Verifica se o novo valor é válido
                        valido = novo_valor and novo_valor not in valores_invalidos
                        
                        # Verifica se é diferente (e se o antigo era inválido, sempre atualiza)
                        antigo_invalido = valor_antigo in valores_invalidos
                        diferente = novo_valor != valor_antigo

                        if valido and (diferente or antigo_invalido):
                            dados_para_salvar[campo] = novo_valor
                            alteracoes.append(f"{campo.upper()}: '{valor_antigo}' -> '{novo_valor}'")
                            houve_mudanca = True

                # ==============================================================================
                # ETAPA 3: Persistência
                # ==============================================================================
                if houve_mudanca:
                    db.update_record_details(db_id, dados_para_salvar)
                    
                    relatorio_mudancas.append({
                        'id': db_id,
                        'mudancas': alteracoes
                    })
                    print(f"✅ ID {db_id}: {', '.join(alteracoes)}")
                    processados += 1
                
            except Exception as e:
                print(f"❌ Erro crítico no ID {db_id}: {e}")
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
                # Formata para não ficar muito longo na tela
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