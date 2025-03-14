import sys
import pandas as pd
from playwright.sync_api import Page, TimeoutError
from utils.logger import Logger

# URLs base para cada tipo de página
URL_CALL = "https://canaime.com.br/sgp2rr/areas/impressoes/UND_ChamadaFOTOS_todos2.php?id_und_prisional="
URL_MAIN = "https://canaime.com.br/sgp2rr/areas/unidades/cadastro.php?id_cad_preso="
URL_REPORTS = "https://canaime.com.br/sgp2rr/areas/unidades/Informes_LER.php?id_cad_preso="
URL_CERTIDAO = "https://canaime.com.br/sgp2rr/areas/impressoes/UND_CertidaoCarceraria.php?id_cad_preso="

# Mapeamento dos novos campos. Ajuste conforme sua necessidade
FIELDS_BY_PAGE = {
    "MAIN": [
        {"column_name": "Mãe",           "locator": "tr:nth-child(3) .titulobk",              "default": "NÃO INFORMADO"},
        {"column_name": "Pai",           "locator": "tr:nth-child(4) .titulobk",              "default": "NÃO INFORMADO"},
        {"column_name": "Sexo",          "locator": "tr:nth-child(5) .titulobk:nth-child(2)", "default": "NÃO INFORMADO"},
        {"column_name": "Data Nasc.",    "locator": "tr:nth-child(5) .titulobk~ .titulobk",   "default": "NÃO INFORMADO"},
        {"column_name": "Cidade Origem", "locator": "tr:nth-child(8) .titulobk",              "default": "NÃO INFORMADO"},
        {"column_name": "Estado",        "locator": "tr:nth-child(9) .titulobk",              "default": "NÃO INFORMADO"},
        {"column_name": "País",          "locator": "tr:nth-child(10) .titulobk",             "default": "NÃO INFORMADO"},
        {"column_name": "Endereço",      "locator": "tr:nth-child(25) .titulobk",             "default": "NÃO INFORMADO"},
    ],
    "REPORTS": [
        {"column_name": "Estado Civil",  "locator": "tr:nth-child(3) .titulo12bk+ .titulobk", "default": "NÃO INFORMADO"},
        {"column_name": "Qtd Filhos",    "locator": ".titulobk~ .titulobk+ .titulobk",        "default": "NÃO INFORMADO"},
        {"column_name": "Escolaridade",  "locator": "tr:nth-child(4) .titulobk",              "default": "NÃO INFORMADO"},
        {"column_name": "Religião",      "locator": "tr:nth-child(8) .titulobk",              "default": "NÃO INFORMADO"},
        {"column_name": "Profissão",     "locator": "tr:nth-child(11) .titulobk",             "default": "NÃO INFORMADO"},
        {"column_name": "Cor/Etnia",     "locator": "tr:nth-child(16) .titulobk:nth-child(2)","default": "NÃO INFORMADO"},
        {"column_name": "Altura",        "locator": "tr:nth-child(19) .tituloVerde .titulobk","default": "NÃO INFORMADO"},
        {"column_name": "Modus Operandi","locator": "tr:nth-child(25) .titulobk",             "default": "NÃO INFORMADO"},
    ],
    "CERTIDAO": [
        {"column_name": "Sentença Dias", "locator": "p+ table .titulobk+ .titulobk",          "default": "NÃO INFORMADO"},
    ]
}


class UnitProcessor:
    """
    Classe responsável por:
      1) Criar uma lista de detentos (DataFrame) para determinada unidade.
      2) Enriquecer o DataFrame com campos extras, coletando informações
         de páginas distintas (MAIN, REPORTS, CERTIDAO).
    """

    def __init__(self, page: Page):
        """
        Parameters
        ----------
        page : Page (Playwright)
            Página já autenticada no sistema.
        """
        self.page = page


    def create_unit_list(self, unit: str) -> pd.DataFrame:
        """
        Acessa a página de chamada (URL_CALL + unit), coleta a lista de presos,
        retornando um DataFrame com colunas:
        ['Ala', 'Cela', 'Código', 'Foto', 'Preso'].

        Parameters
        ----------
        unit : str
            Ex: 'PAMC', 'CPBV', etc.

        Returns
        -------
        pd.DataFrame
        """
        df = pd.DataFrame(columns=['Ala', 'Cela', 'Código', 'Foto', 'Preso'])
        try:
            self.page.goto(URL_CALL + unit, timeout=0)
            all_entries = self.page.locator('.titulobkSingCAPS')
            names = self.page.locator('.titulobkSingCAPS .titulo12bk')
            count = all_entries.count()
            
            # Capturar todas as imagens da página
            inicio = 'https://canaime.com.br/sgp2rr/fotos/presos/'
            all_imgs = self.page.locator('img')
            img_count = all_imgs.count()
            print(f"Total de entradas: {count}, Total de imagens: {img_count}")
            
            # Criar lista de URLs de fotos
            foto_urls = []
            for i in range(img_count):
                foto_src = all_imgs.nth(i).get_attribute('src')
                if foto_src:
                    # Extrair o nome do arquivo da imagem (após a última barra)
                    nome_arquivo = foto_src.split('/')[-1]
                    link_foto = inicio + nome_arquivo
                    foto_urls.append(link_foto)
            
            # Se não temos fotos suficientes, preencher com "SEM FOTO"
            while len(foto_urls) < count:
                foto_urls.append("SEM FOTO")
            
            for i in range(count):
                # entry_text contem algo como:
                # "LS123456\n      \n      \n      \nALA: A1 / 01" (exemplo)
                entry_text = all_entries.nth(i).text_content()
                entry_text = entry_text.replace(" ", "").strip()
                code, _, _, _, wing_cell = entry_text.split('\n')
                inmate_name = names.nth(i).text_content().strip()
                
                # Usar a foto correspondente (se existir)
                link_foto = foto_urls[i] if i < len(foto_urls) else "SEM FOTO"
                
                # Ajuste de ala e cela
                wing_cell = wing_cell.replace("ALA:", "")
                split_index = wing_cell.rfind('/')

                if split_index != -1:
                    if unit in ['CME', 'DICAP']:
                        # Para CME e DICAP, a cela será a parte antes da barra.
                        cell = wing_cell[:split_index].strip()
                        wing = wing_cell[split_index + 1:].strip()
                    else:
                        # Caso padrão: wing é a parte antes da barra e cell a parte após a barra.
                        wing = wing_cell[:split_index].strip()
                        cell = wing_cell[split_index + 1:].strip()
                else:
                    wing = wing_cell.strip()
                    cell = ""

                # code[2:] para remover algum prefixo (ex: "LS123456" -> "123456")
                df.loc[len(df)] = [wing, cell, code[2:], link_foto, inmate_name]

        except Exception as e:
            Logger.capture_error(e)
            # Em caso de falha crítica, encerramos o programa.
            sys.exit(1)

        return df


    def prepare_extra_columns(self, df: pd.DataFrame) -> None:
        """
        Garante que todas as colunas definidas em FIELDS_BY_PAGE existam no DataFrame
        (preenchidas com 'NÃO INFORMADO').

        Parameters
        ----------
        df : pd.DataFrame
        """
        all_columns = set()
        for page_type, fields in FIELDS_BY_PAGE.items():
            for field_info in fields:
                all_columns.add(field_info["column_name"])

        for col_name in all_columns:
            if col_name not in df.columns:
                # Usar df.loc para evitar SettingWithCopyWarning
                df.loc[:, col_name] = "NÃO INFORMADO"

    def get_inmate_full_info(self, code: str) -> dict:
        """
        Coleta as informações completas de 1 detento (MAIN, REPORTS, CERTIDAO),
        retornando um dicionário {coluna: valor_coletado}.

        Parameters
        ----------
        code : str
            Código do preso, ex: "123456"

        Returns
        -------
        dict
            Ex: {
                "Mãe": "...",
                "Pai": "...",
                "Estado Civil": "...",
                ...
            }
        """
        all_data = {}
        try:
            # MAIN
            data_main = self._scrape_page(code, "MAIN")
            all_data.update(data_main)

            # REPORTS
            data_reports = self._scrape_page(code, "REPORTS")
            all_data.update(data_reports)

            # CERTIDAO
            data_cert = self._scrape_page(code, "CERTIDAO")
            all_data.update(data_cert)

        except TimeoutError as te:
            Logger.capture_error(te)
        except Exception as e:
            Logger.capture_error(e)

        return all_data

    def _scrape_page(self, code: str, page_type: str) -> dict:
        """
        Acessa a página correspondente (MAIN, REPORTS, CERTIDAO) e,
        para cada campo definido em FIELDS_BY_PAGE[page_type],
        tenta coletar via locator. Se não encontrar, utiliza o 'default'.

        Parameters
        ----------
        code : str
            Código do preso (ex: "123456")
        page_type : str
            'MAIN', 'REPORTS' ou 'CERTIDAO'

        Returns
        -------
        dict
            {nome_coluna: valor_coletado}
        """
        result = {}

        # Define a URL
        if page_type == "MAIN":
            url = f"{URL_MAIN}{code}"
        elif page_type == "REPORTS":
            url = f"{URL_REPORTS}{code}"
        elif page_type == "CERTIDAO":
            url = f"{URL_CERTIDAO}{code}"
        else:
            # Tipo de página inválido, retorna dicionário vazio
            return result

        # Acessa a página
        self.page.goto(url, timeout=0)

        # Para cada campo, coleta texto (ou default)
        for field_def in FIELDS_BY_PAGE[page_type]:
            col_name = field_def["column_name"]
            locator = field_def["locator"]
            default_val = field_def["default"]

            elements = self.page.locator(locator)
            count_elems = elements.count()

            if count_elems > 0:
                # Pode haver múltiplos matches (ex: Endereço em 2 locators).
                all_contents = elements.all_text_contents()
                # Junta tudo em uma única string (ou trate individualmente se necessário)
                combined_text = "\n".join(t.strip() for t in all_contents if t.strip())
                result[col_name] = combined_text
            else:
                result[col_name] = default_val

        return result

    def enrich_unit_list(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        (Opcional) Método para, dentro desta classe, enriquecer o DataFrame diretamente
        - Não é estritamente necessário, pois você pode fazer a iteração direto no main.py.

        Neste exemplo, simplesmente itera sobre df.iterrows() e chama get_inmate_full_info().

        Parameters
        ----------
        df : pd.DataFrame

        Returns
        -------
        pd.DataFrame
        """
        self.prepare_extra_columns(df)

        for i, row in df.iterrows():
            code = row["Código"]
            extra_data = self.get_inmate_full_info(code)

            # Atualiza no DataFrame
            for k, v in extra_data.items():
                df.at[i, k] = v

        return df
