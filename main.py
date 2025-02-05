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
                        df_unit.at[i, col] = val
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

            df_unit.sort_values(by=["Ala", "Cela", "Preso"], inplace=True)

            # 5) Salvar planilha com resultados da unidade
            excel_handler.create_unit_sheet(unit, df_unit)
            excel_handler.save()

        print("\nProcessamento concluído com sucesso!")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        Logger.capture_error(e)
        print("Erro fatal na execução.")
