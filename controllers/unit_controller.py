import sys
import pandas as pd
from tqdm import tqdm
from playwright.sync_api import Page, TimeoutError
from utils.logger import Logger

# Exemplo de URLs (ajuste se necessário)
URL_CALL = "https://canaime.com.br/sgp2rr/areas/impressoes/UND_ChamadaFOTOS_todos2.php?id_und_prisional="
URL_MAIN = "https://canaime.com.br/sgp2rr/areas/unidades/cadastro.php?id_cad_preso="
URL_REPORTS = "https://canaime.com.br/sgp2rr/areas/unidades/Informes_LER.php?id_cad_preso="
URL_CERTIDAO = "https://canaime.com.br/sgp2rr/areas/impressoes/UND_CertidaoCarceraria.php?id_cad_preso="

# Mapeamento dos novos campos que você quer coletar:
# - "column_name": nome da coluna que você vai usar no DataFrame
# - "page": nome lógico da página (MAIN ou REPORTS)
# - "locator": seletor CSS do Playwright para achar o valor
# - "default": valor padrão caso não encontre
NEW_FIELDS = [
    {
        "column_name": "Mãe",
        "page": "MAIN",
        "locator": "tr:nth-child(3) .titulobk",
        "default": "NÃO INFORMADO"
    },
    {
        "column_name": "Pai",
        "page": "MAIN",
        "locator": "tr:nth-child(4) .titulobk",
        "default": "NÃO INFORMADO"
    },
    {
        "column_name": "Sexo",
        "page": "MAIN",
        "locator": "tr:nth-child(5) .titulobk:nth-child(2)",
        "default": "NÃO INFORMADO"
    },
    {
        "column_name": "Data Nasc.",
        "page": "MAIN",
        "locator": "tr:nth-child(5) .titulobk~ .titulobk",
        "default": "NÃO INFORMADO"
    },
    {
        "column_name": "Cidade Origem",
        "page": "MAIN",
        "locator": "tr:nth-child(8) .titulobk",
        "default": "NÃO INFORMADO"
    },
    {
        "column_name": "Estado",
        "page": "MAIN",
        "locator": "tr:nth-child(9) .titulobk",
        "default": "NÃO INFORMADO"
    },
    {
        "column_name": "País",
        "page": "MAIN",
        "locator": "tr:nth-child(10) .titulobk",
        "default": "NÃO INFORMADO"
    },
    {
        "column_name": "Estado Civil",
        "page": "REPORTS",
        "locator": "tr:nth-child(3) .titulo12bk+ .titulobk",
        "default": "NÃO INFORMADO"
    },
    {
        "column_name": "Qtd Filhos",
        "page": "REPORTS",
        "locator": ".titulobk~ .titulobk+ .titulobk",
        "default": "NÃO INFORMADO"
    },
    {
        "column_name": "Escolaridade",
        "page": "REPORTS",
        "locator": "tr:nth-child(4) .titulobk",
        "default": "NÃO INFORMADO"
    },
    {
        "column_name": "Religião",
        "page": "REPORTS",
        "locator": "tr:nth-child(8) .titulobk",
        "default": "NÃO INFORMADO"
    },
    {
        "column_name": "Profissão",
        "page": "REPORTS",
        "locator": "tr:nth-child(11) .titulobk",
        "default": "NÃO INFORMADO"
    },
    {
        "column_name": "Cor/Etnia",
        "page": "REPORTS",
        "locator": "tr:nth-child(16) .titulobk:nth-child(2)",
        "default": "NÃO INFORMADO"
    },
    {
        "column_name": "Altura",
        "page": "REPORTS",
        "locator": "tr:nth-child(19) .tituloVerde .titulobk",
        "default": "NÃO INFORMADO"
    },
    {
        "column_name": "Modus Operandi",
        "page": "REPORTS",
        "locator": "tr:nth-child(25) .titulobk",
        "default": "NÃO INFORMADO"
    },
    {
        "column_name": "Sentença Dias",
        "page": "CERTIDAO",
        "locator": "p+ table .titulobk+ .titulobk",
        "default": "NÃO INFORMADO"
    },
]

class UnitProcessor:
    """
    Classe responsável por criar a lista de detentos (DataFrame)
    e acrescentar as informações extras no mesmo DataFrame.
    """

    def __init__(self, page: Page):
        """
        Parameters
        ----------
        page : Page
            Página (Playwright) autenticada.
        """
        self.page = page

    def create_unit_list(self, unit: str) -> pd.DataFrame:
        """
        Cria um DataFrame com [Ala, Cela, Código, Preso].

        Parameters
        ----------
        unit : str
            Ex: 'PAMC', 'CPBV', etc.

        Returns
        -------
        pd.DataFrame
            DataFrame com as colunas ['Ala', 'Cela', 'Código', 'Preso'].
        """
        df = pd.DataFrame(columns=['Ala', 'Cela', 'Código', 'Preso'])
        try:
            self.page.goto(URL_CALL + unit, timeout=0)
            all_entries = self.page.locator('.titulobkSingCAPS')
            names = self.page.locator('.titulobkSingCAPS .titulo12bk')
            count = all_entries.count()

            for i in range(count):
                entry_text = all_entries.nth(i).text_content()
                entry_text = entry_text.replace(" ", "").strip()
                code, _, _, _, wing_cell = entry_text.split('\n')
                inmate_name = names.nth(i).text_content().strip()

                # Ajuste de ala e cela
                wing_cell = wing_cell.replace("ALA:", "")
                split_index = wing_cell.rfind('/')
                wing = wing_cell[:split_index].strip()
                cell = wing_cell[split_index + 1:].strip()

                # Insere no DataFrame
                df.loc[len(df)] = [wing, cell, code[2:], inmate_name]

        except Exception as e:
            Logger.capture_error(e)
            sys.exit(1)

        return df

    def enrich_unit_list(self, df: pd.DataFrame, pbar: tqdm) -> pd.DataFrame:
        """
        Acrescenta colunas extras (ex.: "Mãe", "Pai", etc.) ao DataFrame.

        Parameters
        ----------
        df : pd.DataFrame
            DataFrame original com [Ala, Cela, Código, Preso].
        pbar : tqdm
            Barra de progresso para feedback ao usuário.

        Returns
        -------
        pd.DataFrame
            Mesmo DataFrame, com colunas adicionais.
        """
        for field in NEW_FIELDS:
            col_name = field["column_name"]
            if col_name not in df.columns:
                df[col_name] = field["default"]  # Preenche com default no início

        for index, row in df.iterrows():
            code = row['Código']
            try:
                fields_by_page = {"MAIN": [], "REPORTS": [], "CERTIDAO": []}
                for field in NEW_FIELDS:
                    fields_by_page[field["page"]].append(field)

                # MAIN
                if fields_by_page["MAIN"]:
                    self.page.goto(f"{URL_MAIN}{code}", timeout=0)
                    for f in fields_by_page["MAIN"]:
                        locator_count = self.page.locator(f["locator"]).count()
                        if locator_count > 0:
                            text_val = self.page.locator(f["locator"]).text_content().strip()
                        else:
                            text_val = f["default"]
                        df.at[index, f["column_name"]] = text_val

                # REPORTS
                if fields_by_page["REPORTS"]:
                    self.page.goto(f"{URL_REPORTS}{code}", timeout=0)
                    for f in fields_by_page["REPORTS"]:
                        locator_count = self.page.locator(f["locator"]).count()
                        if locator_count > 0:
                            text_val = self.page.locator(f["locator"]).text_content().strip()
                        else:
                            text_val = f["default"]
                        df.at[index, f["column_name"]] = text_val

                # CERTIDAO
                if fields_by_page["CERTIDAO"]:
                    self.page.goto(f"{URL_CERTIDAO}{code}", timeout=0)
                    for f in fields_by_page["CERTIDAO"]:
                        locator = self.page.locator(f["locator"])
                        all_texts = locator.all_text_contents()
                        if len(all_texts) == 0:
                            text_val = f["default"]
                        else:
                            text_val = "\n".join(txt.strip() for txt in all_texts)
                        df.at[index, f["column_name"]] = text_val

                # Atualiza a barra de progresso
                pbar.set_postfix({"Preso": row["Preso"]})
                pbar.update(1)

            except TimeoutError as te:
                Logger.capture_error(te)
                print(f"Timeout ao coletar dados do código {code}")
            except Exception as e:
                Logger.capture_error(e)
                print(f"Erro ao coletar dados do código {code}, prosseguindo...")

        return df
