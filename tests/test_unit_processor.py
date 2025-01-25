import pytest
import pandas as pd
from unittest.mock import MagicMock

from controllers.unit_controller import UnitProcessor, NEW_FIELDS

@pytest.fixture
def mock_page():
    """
    Cria um objeto de mock para a Page do Playwright.
    Podemos simular o comportamento dos métodos .goto(), .locator(), etc.
    """
    page = MagicMock()
    # page.goto(url, timeout=0) não precisa retornar nada específico,
    # pois estamos só verificando se não quebra.
    page.goto.return_value = None

    # Locator mock: simularemos que cada .locator(...) encontre 1 item
    # e retorne texto "MOCK_VALUE".
    locator_mock = MagicMock()
    locator_mock.count.return_value = 1
    locator_mock.text_content.return_value = "MOCK_VALUE"

    page.locator.return_value = locator_mock

    return page


def test_create_unit_list(mock_page):
    """
    Testa se create_unit_list retorna o DataFrame esperado.
    """
    # Supondo que a página .locator('.titulobkSingCAPS') retorne 2 itens
    # Precisamos ajustar o count()
    mock_page.locator.return_value.count.return_value = 2

    # Simulamos dois "text_contents" distintos para as entradas
    # ex.: "GS123\n\n\n\nALA:1/2" e "GS456\n\n\n\nALA:3/4"
    def side_effect_text_content(*args, **kwargs):
        # Cada chamada nth(i).text_content() devolve algo diferente
        i = mock_page.locator.call_args[0][0]  # A forma de capturar 'i' pode variar
        # Para simplificar, vamos só alternar manualmente:
        if mock_page.locator.call_args_list[-1][0][0].endswith('.titulobkSingCAPS'):
            # Se for a query de .titulobkSingCAPS, retorna algo
            # Mas isso fica complexo de controlar. Vamos simplificar:
            pass
        return "GS123\n\n\n\nALA:1/2"

    # Para simplificar, vamos criar um mock completamente manual:
    # - Precisamos diferenciar .nth(0) e .nth(1).
    #   Então podemos criar sub-mocks e trocar de acordo com nth(i).

    # Para não complicar muito, vamos assumir que cada nth(i).text_content()
    # retorna um valor fixo no test. Ajustaremos a "count" e "text_content" manualmente.
    # Assim testamos se a função gera 2 linhas no DF.
    all_entries_mock = MagicMock()
    all_entries_mock.count.return_value = 2

    # Duas entradas, para nth(0) e nth(1):
    nth_0 = MagicMock()
    nth_0.text_content.return_value = "GS123\n\n\n\nALA:1/2"
    nth_1 = MagicMock()
    nth_1.text_content.return_value = "GS456\n\n\n\nALA:3/4"

    # Faremos all_entries_mock.nth(i) -> nth_0 ou nth_1
    def nth_side_effect(i):
        if i == 0:
            return nth_0
        else:
            return nth_1

    all_entries_mock.nth.side_effect = nth_side_effect

    # E para os nomes:
    names_mock = MagicMock()
    names_mock.count.return_value = 2
    name_0 = MagicMock()
    name_0.text_content.return_value = "Fulano da Silva"
    name_1 = MagicMock()
    name_1.text_content.return_value = "Beltrano Pereira"

    def names_nth_side_effect(i):
        return name_0 if i == 0 else name_1

    names_mock.nth.side_effect = names_nth_side_effect

    # Agora, ajustamos mock_page.locator para retornar all_entries_mock ou names_mock
    # dependendo do seletor chamado:
    def locator_side_effect(selector):
        if selector == '.titulobkSingCAPS':
            return all_entries_mock
        elif selector == '.titulobkSingCAPS .titulo12bk':
            return names_mock
        return MagicMock()

    mock_page.locator.side_effect = locator_side_effect

    # Agora testamos create_unit_list
    processor = UnitProcessor(mock_page)
    df = processor.create_unit_list("PAMC")

    # Verificamos se o DF tem 2 linhas
    assert len(df) == 2

    # Verificamos colunas
    assert list(df.columns) == ["Ala", "Cela", "Código", "Preso"]

    # Verificamos valores esperados
    # 1ª linha
    assert df.iloc[0]["Código"] == "123"   # pois era "GS123", cortamos "GS"
    assert df.iloc[0]["Ala"] == "1"
    assert df.iloc[0]["Cela"] == "2"
    assert df.iloc[0]["Preso"] == "Fulano da Silva"

    # 2ª linha
    assert df.iloc[1]["Código"] == "456"
    assert df.iloc[1]["Ala"] == "3"
    assert df.iloc[1]["Cela"] == "4"
    assert df.iloc[1]["Preso"] == "Beltrano Pereira"


def test_enrich_unit_list(mock_page):
    """
    Testa se enrich_unit_list adiciona as novas colunas e preenche com "MOCK_VALUE"
    (pois mockamos a resposta).
    """
    # Vamos criar um DF inicial parecido com o que create_unit_list retorna
    df_initial = pd.DataFrame([
        {"Ala": "1", "Cela": "2", "Código": "123", "Preso": "Fulano da Silva"},
        {"Ala": "3", "Cela": "4", "Código": "456", "Preso": "Beltrano Pereira"},
    ])

    processor = UnitProcessor(mock_page)
    df_enriched = processor.enrich_unit_list(df_initial)

    # Agora esperamos que df_enriched tenha as colunas extras (Mãe, Pai, Sexo, etc.)
    # Verifiquemos, por exemplo:
    col_names = df_enriched.columns
    for field in NEW_FIELDS:
        assert field["column_name"] in col_names, f"{field['column_name']} não foi adicionada."

    # E cada valor deve ser "MOCK_VALUE" (default do mock), exceto as colunas originais
    for field in NEW_FIELDS:
        for row_idx in range(len(df_enriched)):
            val = df_enriched.loc[row_idx, field["column_name"]]
            assert val == "MOCK_VALUE", f"Esperava 'MOCK_VALUE' em {field['column_name']}"

    # Garante que não alteramos as colunas originais
    assert df_enriched.loc[0, "Código"] == "123"
    assert df_enriched.loc[0, "Preso"] == "Fulano da Silva"
    assert df_enriched.loc[1, "Ala"] == "3"
    assert df_enriched.loc[1, "Cela"] == "4"
