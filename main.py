import sys
import time
from playwright.sync_api import sync_playwright
from controllers.login_controller import CanaimeLogin
from controllers.unit_controller import UnitProcessor
from views.excel_view import ExcelHandler
from config import units, excel_filename, current_version
from utils.logger import Logger
from utils.updater import check_and_update


def format_seconds_to_hhmmss(seconds: float) -> str:
    """Converte segundos em string no formato '00h:00min:00s'."""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    return f"{h:02d}h:{m:02d}min:{s:02d}s"


def main():
    """
    Função principal que executa:
      1) Login (Playwright)
      2) Para cada unidade:
         - Cria a lista de presos
         - Itera cada preso, pega as informações
         - Exibe status no formato:
           [unidade_atual/total_unidades][unit] [preso_atual/total_presos] NOME_PRESO | ...
         - Salva no Excel
    Exibe o "Tempo da Aplicação" (desde o início) e
    a "Estimativa Restante" (para terminar todas as unidades).
    """

    # 1) Verifica atualização
    if check_and_update(current_version):
        print("Atualização aplicada com sucesso! Reinicie o programa.")
        sys.exit(0)

    # 2) Inicia Playwright e faz login
    with sync_playwright() as p:
        login_controller = CanaimeLogin(p, headless=True)
        page = login_controller.login()

        # 3) Inicializa processor + Excel
        processor = UnitProcessor(page)
        excel_handler = ExcelHandler(excel_filename)

        # 3.1) Primeiro, descobrir total de presos em TODAS as units (para cálculo de ETA global).
        #     Faremos um "pré-passo" para ler APENAS o total de cada unidade, sem enriquecer ainda.
        global_total_inmates = 0
        unit_dfs = []  # armazenaremos (unit, df) para reutilizar depois
        for unit in units:
            try:
                df_tmp = processor.create_unit_list(unit)
            except Exception as e:
                Logger.capture_error(e)
                print(f"Erro ao obter lista de presos da unidade '{unit}'. Pulando...", flush=True)
                continue
            unit_dfs.append((unit, df_tmp))
            global_total_inmates += len(df_tmp)

        if global_total_inmates == 0:
            print("Nenhum preso encontrado em todas as unidades! Encerrando.")
            return

        # 4) Agora, processamos de fato (enriquece, salva Excel, etc.)
        global_start_time = time.time()   # momento em que começamos o "processamento global"
        global_processed = 0  # número de presos já enriquecidos

        total_units = len(unit_dfs)

        for unit_index, (unit, df_unit) in enumerate(unit_dfs, start=1):
            print("\n" + "="*60)
            print(f"[{unit_index}/{total_units}] Iniciando processamento da unidade: {unit}")
            total_inmates_unit = len(df_unit)
            print(f"Total de presos em {unit}: {total_inmates_unit}", flush=True)

            if total_inmates_unit == 0:
                continue  # nada a processar

            # Garante colunas extras (campos MAIN, REPORTS, CERTIDAO)
            processor.prepare_extra_columns(df_unit)

            # Loop nos presos da unidade
            for i, row in df_unit.iterrows():
                code = row["Código"]
                inmate_name = row["Preso"]

                iteration_start = time.time()
                try:
                    # Coleta dados extras e atualiza a row
                    extra_data = processor.get_inmate_full_info(code)
                    for col, val in extra_data.items():
                        df_unit.loc[i, col] = val  # Usar .loc em vez de .at para evitar warnings
                except Exception as e:
                    Logger.capture_error(e)
                    print(f"Erro ao processar preso '{inmate_name}' (código: {code}).", flush=True)

                # Contabiliza como processado
                global_processed += 1

                # Tempo decorrido desde o início da aplicação
                elapsed_app = time.time() - global_start_time

                # Calcula tempo médio (em segundos) por preso
                avg_time_per_inmate = elapsed_app / global_processed

                # Calcula estimativa de tempo restante (para TODOS que faltam, não só desta unit)
                remaining = global_total_inmates - global_processed
                eta_seconds = remaining * avg_time_per_inmate

                # Formata as strings de tempo
                elapsed_str = format_seconds_to_hhmmss(elapsed_app)
                eta_str = format_seconds_to_hhmmss(eta_seconds)

                # Monta a linha exata que você quer:
                # [unidade_atual/total_unidades][nome_unit] [i+1/total_inmates_unit] NOME_PRESO | Tempo da Aplicação: ... | Estimativa Restante: ...
                # Exemplo final:
                # [1/5][PAMC] [105/1763] ALISSANDRO ... | Tempo da Aplicação: 00h:00min:00s | Estimativa Restante: 00h:00min:00s
                print(
                    f"[{unit_index}/{total_units}][{unit}]"
                    f"[{i+1}/{total_inmates_unit}] {inmate_name} | "
                    f"Tempo da Aplicação: {elapsed_str} | "
                    f"Estimativa Restante: {eta_str}",
                    flush=True
                )

            # Ordenar os dados (sem usar inplace para evitar warnings)
            df_unit = df_unit.sort_values(by=["Ala", "Cela", "Preso"])

            # 5) Salvar planilha com resultados da unidade
            excel_handler.create_unit_sheet(unit, df_unit)
            excel_handler.save()

        print("\nProcessamento concluído com sucesso!")


def test_with_limited_inmates(limit=5):
    """
    Função de teste que processa apenas um número limitado de presos por unidade.
    
    Parameters
    ----------
    limit : int
        Número máximo de presos a serem processados por unidade.
    """
    print(f"MODO DE TESTE: Processando até {limit} presos por unidade")
    
    # Inicia Playwright e faz login
    with sync_playwright() as p:
        login_controller = CanaimeLogin(p, headless=True)
        page = login_controller.login()

        # Inicializa processor + Excel
        processor = UnitProcessor(page)
        excel_handler = ExcelHandler(f"teste_{limit}_presos_por_unidade.xlsx")

        for unit_index, unit in enumerate(units, start=1):
            print("\n" + "="*60)
            print(f"[{unit_index}/{len(units)}] Iniciando processamento da unidade: {unit}")
            
            try:
                # Cria lista de presos para a unidade
                df_unit = processor.create_unit_list(unit)
                
                # Limita o número de presos a serem processados
                if len(df_unit) > limit:
                    print(f"Limitando de {len(df_unit)} para {limit} presos")
                    df_unit = df_unit.head(limit).copy()  # Criar uma cópia explicita
                
                total_inmates_unit = len(df_unit)
                print(f"Total de presos em {unit}: {total_inmates_unit}", flush=True)
                
                if total_inmates_unit == 0:
                    continue  # nada a processar
                
                # Prepara colunas extras
                processor.prepare_extra_columns(df_unit)
                
                # Processa cada preso
                for i, row in df_unit.iterrows():
                    code = row["Código"]
                    inmate_name = row["Preso"]
                    
                    try:
                        # Coleta dados extras e atualiza a row
                        extra_data = processor.get_inmate_full_info(code)
                        for col, val in extra_data.items():
                            df_unit.loc[i, col] = val  # Usar .loc em vez de .at
                    except Exception as e:
                        Logger.capture_error(e)
                        print(f"Erro ao processar preso '{inmate_name}' (código: {code}).", flush=True)
                    
                    print(f"[{unit_index}/{len(units)}][{unit}] [{i+1}/{total_inmates_unit}] {inmate_name}", flush=True)
                
                # Ordena os dados (sem usar inplace)
                df_unit = df_unit.sort_values(by=["Ala", "Cela", "Preso"])
                
                # Salva no Excel
                excel_handler.create_unit_sheet(unit, df_unit)
                excel_handler.save()
                
            except Exception as e:
                Logger.capture_error(e)
                print(f"Erro ao processar unidade '{unit}'. Pulando...", flush=True)
        
        print("\nTeste concluído com sucesso!")


def test_single_unit(unit_code, limit=5):
    """
    Função de teste que processa apenas uma unidade específica com um número limitado de presos.
    
    Parameters
    ----------
    unit_code : str
        Código da unidade a ser processada (ex: 'PAMC')
    limit : int
        Número máximo de presos a serem processados.
    """
    print(f"MODO DE TESTE: Processando a unidade {unit_code} com até {limit} presos")
    
    # Inicia Playwright e faz login
    with sync_playwright() as p:
        login_controller = CanaimeLogin(p, headless=True)
        page = login_controller.login()

        # Inicializa processor + Excel
        processor = UnitProcessor(page)
        excel_handler = ExcelHandler(f"teste_unidade_{unit_code}_{limit}_presos.xlsx")
            
        try:
            # Cria lista de presos para a unidade
            df_unit = processor.create_unit_list(unit_code)
            
            # Limita o número de presos a serem processados
            if len(df_unit) > limit:
                print(f"Limitando de {len(df_unit)} para {limit} presos")
                df_unit = df_unit.head(limit).copy()  # Criar uma cópia explicita
            
            total_inmates_unit = len(df_unit)
            print(f"Total de presos em {unit_code}: {total_inmates_unit}", flush=True)
            
            if total_inmates_unit == 0:
                print("Nenhum preso encontrado. Finalizando teste.")
                return
            
            # Prepara colunas extras
            processor.prepare_extra_columns(df_unit)
            
            # Processa cada preso
            for i, row in df_unit.iterrows():
                code = row["Código"]
                inmate_name = row["Preso"]
                
                try:
                    # Coleta dados extras e atualiza a row
                    extra_data = processor.get_inmate_full_info(code)
                    for col, val in extra_data.items():
                        df_unit.loc[i, col] = val  # Usar .loc em vez de .at
                except Exception as e:
                    Logger.capture_error(e)
                    print(f"Erro ao processar preso '{inmate_name}' (código: {code}).", flush=True)
                
                print(f"[{unit_code}] [{i+1}/{total_inmates_unit}] {inmate_name}", flush=True)
            
            # Ordena os dados (sem usar inplace)
            df_unit = df_unit.sort_values(by=["Ala", "Cela", "Preso"])
            
            # Adiciona uma coluna para testar se a nova coluna Foto está funcionando corretamente
            df_unit['Tem Foto'] = df_unit['Foto'].apply(lambda x: "SIM" if x != "SEM FOTO" else "NÃO")
            
            # Salva no Excel
            excel_handler.create_unit_sheet(unit_code, df_unit)
            excel_handler.save()
            
        except Exception as e:
            Logger.capture_error(e)
            print(f"Erro ao processar unidade '{unit_code}'.", flush=True)
    
    print("\nTeste concluído com sucesso!")


if __name__ == "__main__":
    try:
        # Para rodar o teste com 5 presos por unidade, descomente a linha abaixo:
        # test_with_limited_inmates(5)
        
        # Para testar apenas uma unidade específica, descomente a linha abaixo e ajuste os parâmetros:
        # test_single_unit('PAMC', 5)  # Substitua 'PAMC' pela unidade desejada
        
        # Para rodar o programa normal
        main()
    except Exception as e:
        Logger.capture_error(e)
        print("Erro fatal na execução.")
