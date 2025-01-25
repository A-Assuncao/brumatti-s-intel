import sys
import os
from playwright.sync_api import sync_playwright, Page, TimeoutError
from utils.logger import Logger
from config import url_login_canaime

class CanaimeLogin:
    """
    Controller responsável pelo login no site do Canaimé.

    Methods
    -------
    __init__(p: Any, headless: bool = True)
        Inicializa o handler de login com instância do Playwright.
    login() -> Page
        Executa o login e retorna a página autenticada.
    """

    def __init__(self, p, headless: bool = True):
        """
        Parâmetros
        ----------
        p : Playwright
            Instância do Playwright.
        headless : bool, optional
            Se True, executa o browser em modo headless (padrão).
        """
        self.p = p
        self.headless = headless
        self.page = None

    def login(self) -> Page:
        """
        Executa o login e retorna a página autenticada.

        Returns
        -------
        Page
            Página do Playwright já autenticada.
        """
        os.system('cls' if os.name == 'nt' else 'clear')

        print('Você precisará digitar seu usuário e senha do Canaimé. Os dados não serão gravados.')
        user = input('Digite seu login: ')
        password = input('Digite sua senha: ')

        os.system('cls' if os.name == 'nt' else 'clear')
        browser = self.p.chromium.launch(headless=self.headless)
        context = browser.new_context(java_script_enabled=False)

        # Bloqueia carregamento de imagens para otimizar
        context.set_extra_http_headers({
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        })
        context.route("**/*", lambda route: route.abort() if route.request.resource_type == "image" else route.continue_())

        self.page = context.new_page()
        self.page.goto(url_login_canaime, timeout=0)
        self.page.locator("input[name=\"usuario\"]").click()
        self.page.locator("input[name=\"usuario\"]").fill(user)
        self.page.locator("input[name=\"senha\"]").fill(password)
        self.page.locator("input[name=\"senha\"]").press("Enter")

        self.page.wait_for_timeout(5000)
        try:
            # Checa se logou com sucesso
            if self.page.locator('img').count() < 4:
                print('Usuário ou senha inválidos')
                sys.exit(1)
            else:
                print('Login efetuado com sucesso!')
        except Exception as e1:
            Logger.capture_error(e1, self.page)
            sys.exit(1)

        return self.page
