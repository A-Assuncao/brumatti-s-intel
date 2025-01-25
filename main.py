import time, sys
from tqdm import tqdm
from playwright.sync_api import sync_playwright
from controllers.unit_controller import UnitProcessor
from views.excel_view import ExcelHandler
from config import units, excel_filename, current_version
from utils.logger import Logger
from utils.updater import check_and_update
from controllers.login_controller import CanaimeLogin


def main():
    """
    Função principal que executa o fluxo de login, coleta de dados e geração do Excel.
    Inclui barra de progresso (tqdm), cálculo de tempo estimado (ETA) e integração com updater.
    """
    with sync_playwright() as p:
        # 1. Realiza o login no sistema
        login_controller = CanaimeLogin(p, headless=True)
        page = login_controller.login()

        # 2. Inicializa manipuladores de unidade e Excel
        processor = UnitProcessor(page)
        excel_handler = ExcelHandler(excel_filename)
        excel_handler.save_periodically(300)  # Salva o Excel a cada 5 minutos

        # 3. Processa cada unidade com feedback
        for unit in tqdm(units, desc="Unidades", leave=True):
            print(f"Processando unidade: {unit}", flush=True)

            # 3.1 Cria a lista de presos para a unidade
            try:
                df = processor.create_unit_list(unit)
            except Exception as e:
                Logger.capture_error(e)
                print(f"Erro ao processar a unidade {unit}. Pulando...", flush=True)
                continue

            total_inmates = len(df)
            if total_inmates == 0:
                print(f"Unidade {unit} não possui presos cadastrados.", flush=True)
                continue

            # Barra de progresso para presos na unidade
            inmate_pbar = tqdm(total=total_inmates, desc=f"Presos ({unit})", leave=False)
            times_per_inmate = []

            for index, row in df.iterrows():
                start_time = time.time()
                try:
                    # Preenche informações detalhadas de cada preso
                    df = processor.enrich_unit_list(df, inmate_pbar)
                except Exception as e:
                    Logger.capture_error(e)
                    print(f"Erro ao processar o preso: {row['Preso']}. Continuando...", flush=True)

                # Atualiza a barra de progresso
                elapsed_time = time.time() - start_time
                times_per_inmate.append(elapsed_time)

                # Cálculo de ETA (Tempo Estimado Restante)
                avg_time = sum(times_per_inmate) / len(times_per_inmate)
                remaining_inmates = total_inmates - (index + 1)
                eta_seconds = avg_time * remaining_inmates

                # Atualiza barra e exibe informações adicionais
                inmate_pbar.set_postfix({
                    "Preso": row["Preso"],
                    "ETA (s)": f"{eta_seconds:.1f}"
                })
                inmate_pbar.update(1)

            inmate_pbar.close()

            # 3.3 Salva dados no Excel
            excel_handler.create_unit_sheet(unit, df)
            excel_handler.save()

        print("Processamento concluído com sucesso!")


if __name__ == "__main__":
    # Verifica atualizações antes de iniciar o processamento
    if check_and_update(current_version):
        print("Atualização aplicada com sucesso! Reinicie o programa.")
        sys.exit(0)

    try:
        main()
    except Exception as e:
        Logger.capture_error(e)
        print("Erro fatal na execução.")
