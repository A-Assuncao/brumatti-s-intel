import os
import pytest
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

# Importe suas classes conforme a organização do seu projeto:
from controllers.unit_controller import UnitProcessor
from views.excel_view import ExcelHandler

# Se você tiver algo como config.py com a lista de unidades:
# from config import units  # Exemplo
# Para fins de demonstração, definimos aqui manualmente:
units = ["PAMC"]  # ou qualquer outra unidade que exista no Canaimé

@pytest.mark.integration
def test_canaime_real_scraping():
    """
    Teste de integração que:
    1. Lê as credenciais CANAIME_USER e CANAIME_PASSWORD via variáveis de ambiente.
    2. Faz login no Canaimé.
    3. Processa 1 unidade (ex.: 'PAMC'), mas só coleta 5 presos para testar.
    4. Gera um Excel e verifica se ele foi criado.
    """

    # 1) Checa se temos credenciais
    user = '007msn88'
    password = 'warcraft2718'
    if not user or not password:
        pytest.skip("Credenciais não fornecidas. Defina as variáveis de ambiente CANAIME_USER e CANAIME_PASSWORD.")

    # 2) Inicia o Playwright e faz login no Canaimé
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # Mude para False se quiser ver o navegador
        context = browser.new_context(java_script_enabled=False)

        # Bloqueia imagens (opcional, para acelerar)
        context.set_extra_http_headers({"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"})
        context.route("**/*", lambda route: route.abort() if route.request.resource_type == "image" else route.continue_())

        page = context.new_page()

        # URL de login (ajuste conforme seu config)
        url_login = "https://canaime.com.br/sgp2rr/login/login_principal.php"
        page.goto(url_login, timeout=30 * 1000)

        page.locator("input[name='usuario']").fill(user)
        page.locator("input[name='senha']").fill(password)
        page.locator("input[name='senha']").press("Enter")

        # Aguarda um pouco para garantir login
        page.wait_for_timeout(5000)

        # Verifica se login deu certo
        # (exemplo: checa se existe um seletor ou alguma imagem)
        if page.locator("img").count() < 4:
            pytest.fail("Falha no login: usuário ou senha inválidos?")

        # 3) Testa o UnitProcessor
        processor = UnitProcessor(page)

        # Vamos criar um arquivo Excel e checar se ele é salvo
        excel_filename = "test_integration_canaime.xlsx"
        excel_handler = ExcelHandler(excel_filename)

        for unit in units:
            # Cria DF com todos presos
            df = processor.create_unit_list(unit)

            # Se quiser testar apenas 5 presos, cortamos o DF
            if len(df) > 5:
                df = df.head(5)  # Pega só os 5 primeiros

            # Agora enriquecemos com as informações extras
            df = processor.enrich_unit_list(df)

            # Cria a planilha
            excel_handler.create_unit_sheet(unit, df)

        # Salva e espera 2s
        excel_handler.save()
        time.sleep(2)

        # 4) Verifica se o arquivo foi criado
        excel_path = Path(excel_filename)
        assert excel_path.exists(), "O arquivo Excel não foi criado."
        assert excel_path.stat().st_size > 0, "O arquivo Excel está vazio."

        # Opcional: você pode abrir com openpyxl e checar se há conteúdo
        # from openpyxl import load_workbook
        # wb = load_workbook(excel_filename)
        # assert len(wb.sheetnames) == len(units), "Número de abas diferente do número de unidades."
        # ( etc. )

        # Fecha o browser
        context.close()
        browser.close()

    print("Teste de integração real finalizado com sucesso!")
