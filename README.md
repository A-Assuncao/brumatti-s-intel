
# brumatti-s-intel

**brumatti-s-intel** é um projeto em Python destinado a coletar e gerar informações sobre detentos a partir do sistema Canaimé, utilizando a biblioteca Playwright para automação de navegação web. Os dados são então organizados e exportados para um arquivo Excel, facilitando o manuseio e análise das informações coletadas.

## Sumário

-   [Arquitetura do Projeto](#arquitetura-do-projeto)
-   [Requisitos](#requisitos)
-   [Instalação](#instala%C3%A7%C3%A3o)
-   [Estrutura de Pastas](#estrutura-de-pastas)
-   [Como Executar](#como-executar)
-   [Principais Arquivos e Funções](#principais-arquivos-e-fun%C3%A7%C3%B5es)
-   [Contribuição](#contribui%C3%A7%C3%A3o)
-   [Licença](#licen%C3%A7a)

## Arquitetura do Projeto

O projeto está estruturado seguindo o padrão **MVC (Model-View-Controller)** com algumas pastas de suporte:

1.  **Models**  
    Representa a camada de dados. Aqui, há classes para manipular e estruturar as informações de detentos, como `Inmate`.
    
2.  **Views**  
    Responsável pela apresentação ou saída dos dados. Neste caso, a classe `ExcelHandler` gera e gerencia o arquivo Excel.
    
3.  **Controllers**  
    Contém a lógica de aplicação e a ligação entre Model e View:
    
    -   `CanaimeLogin` cuida do login na plataforma Canaimé.
    -   `UnitProcessor` coleta listas de detentos e informações detalhadas de cada um.
4.  **Utils**  
    Pasta de utilitários, com classes auxiliares (`Utils`, `Logger` e `updater`) para facilitar tarefas como cálculo de idade, log de erros e atualização da aplicação.
    
5.  **main.py**  
    É o ponto de entrada da aplicação. Ele orquestra o fluxo, chamando o `CanaimeLogin` para autenticação, o `UnitProcessor` para processamento dos dados e o `ExcelHandler` para geração de planilhas.
    

## Requisitos

-   [Python 3.8+](https://www.python.org/) (recomendado Python 3.10 ou superior)
-   [Playwright](https://pypi.org/project/playwright/)
-   [pandas](https://pypi.org/project/pandas/)
-   [openpyxl](https://pypi.org/project/openpyxl/)

Além disso, o projeto utiliza outras bibliotecas padrão do Python, como `sys`, `os`, `time`, `datetime`, entre outras.

## Instalação

1.  **Clone** este repositório ou baixe o código-fonte:
    
    ```bash
    git clone https://github.com/A-Assuncao/brumatti-s-intel.git
    ```
    
2.  **Crie e ative** um ambiente virtual (opcional, mas recomendado):
	```bash
    python -m venv venv
 	```

    ```bash
    source venv/bin/activate  # Linux ou Mac
    ```
    
    ```bash
    venv\Scripts\activate     # Windows
    ``` 
    
4.  **Instale as dependências** listadas no arquivo `requirements.txt`:

    ```bash
    pip install -r requirements.txt
    ```
    
5.  **Instale o Playwright** e os navegadores necessários:
          
    ```bash
    playwright install
    ```

## Estrutura de Pastas

Abaixo, um exemplo de como o projeto pode estar organizado:

```markdown
📦 brumatti-s-intel/           # Diretório raiz do projeto
├── 🚀 main.py                 # Ponto de entrada da aplicação
├── ⚙️ config.py               # Configurações globais do projeto
├── 📋 requirements.txt        # Dependências do projeto
├── 🛡️ LICENSE                 # Licença do projeto
├── 📖 README.md               # Documentação do projeto

📂 models/                      # Módulo para representação de dados
│   ├── 📄 __init__.py          # Inicializa o módulo models
│   └── 📄 inmate_model.py      # Classe ou estrutura para o detento

📂 views/                       # Módulo de visualizações (output, relatórios etc.)
│   ├── 📄 __init__.py          # Inicializa o módulo views
│   └── 📄 excel_view.py        # Classe para manipulação de Excel

📂 controllers/                 # Módulo de lógica de controle (processamento principal)
│   ├── 📄 __init__.py          # Inicializa o módulo controllers
│   ├── 📄 login_controller.py  # Gerenciamento de login
│   └── 📄 unit_controller.py   # Processamento de unidades e scraping

📂 utils/                       # Utilitários e funções auxiliares
│   ├── 📄 __init__.py          # Inicializa o módulo utils
│   ├── 🔧 helper.py            # Funções auxiliares genéricas
│   ├── 📝 logger.py            # Logger centralizado para erros e eventos
│   └── 🔄 updater.py           # Lógica de atualização do aplicativo
``` 

-   **controllers/**: Camada de controle, manipulando o fluxo do projeto.
-   **models/**: Classes que definem o modelo de dados (ex.: `Inmate`).
-   **utils/**: Funções e classes auxiliares (ex.: logger de erros, funções de entrada/saída etc.).
-   **views/**: Apresentação dos dados (Excel, no caso).
-   **config.py**: Contém configurações e constantes como URLs.
-   **main.py**: Arquivo principal, ponto de execução da aplicação.
-   **requirements.txt**: Lista de dependências Python.

## Como Executar

Após instalar todas as dependências, execute o script principal:
```bash
python main.py
```

-   A aplicação solicitará seu **usuário** e **senha** do Canaimé.
-   Em seguida, irá percorrer as unidades configuradas em `config.py`, coletar dados e criar um arquivo Excel (por padrão, `Informacoes_Presos.xlsx`).
-   Durante o processo, o arquivo será salvo periodicamente para evitar perda de dados em caso de falhas.
-   Logs de erro são gravados em `error_log.log` e podem ser abertos automaticamente se ocorrer alguma exceção não tratada.

## Principais Arquivos e Funções

1.  
   **`main.py`**  
   - Função `main()`: ponto de entrada do script.  
   - Invoca `CanaimeLogin` (para login) e `UnitProcessor` (para coleta de dados), passando os resultados para o `ExcelHandler`.
  
2.  
   **`controllers/login_controller.py`**  
   - Classe `CanaimeLogin`: gerencia a autenticação no site Canaimé.
  
3.  
   **`controllers/unit_controller.py`**  
   - Classe `UnitProcessor`: obtém a lista de detentos e informa detalhadamente cada registro, criando objetos `Inmate`.
  
4.  
   **`models/inmate_model.py`**  
   - Classe `Inmate`: representa os dados de cada detento.

5.  
   **`views/excel_view.py`**  
   - Classe `ExcelHandler`: cria abas (sheets) no arquivo Excel e preenche as informações organizadas.

6.  
   **`utils/logger.py`**  
   - Classe `Logger`: para registrar e lidar com erros em arquivo de log.

7.  
   **`utils/helper.py`**  
   - Classe `Utils`: métodos utilitários diversos (ex.: cálculo de idade, timer etc.).

8.  
   **`utils/updater.py`**  
   - Lida com a checagem e aplicação de possíveis atualizações automáticas no sistema.


## Contribuição

Contribuições são sempre bem-vindas! Sinta-se à vontade para:

1.  Abrir _Issues_ relatando bugs ou sugerindo melhorias.
2.  Criar _Pull Requests_ com correções ou novas funcionalidades.
3.  Entrar em contato se quiser discutir algo antes de implementar.

## Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENÇA](LICENSE) para mais detalhes.

----------
**Desenvolvido com ♥ e Python.**
