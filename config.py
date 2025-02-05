url_login_canaime = 'https://canaime.com.br/sgp2rr/login/login_principal.php'
url_reports = "https://canaime.com.br/sgp2rr/areas/unidades/Informes_LER.php?id_cad_preso="
url_certificate = "https://canaime.com.br/sgp2rr/areas/impressoes/UND_CertidaoCarceraria.php?id_cad_preso="
url_call = 'https://canaime.com.br/sgp2rr/areas/impressoes/UND_ChamadaFOTOS_todos2.php?id_und_prisional='
url_main = 'https://canaime.com.br/sgp2rr/areas/unidades/cadastro.php?id_cad_preso='

# Lista de unidades prisionais a serem processadas
# coloque um "#" na frente da unidade para ignorar-la
units = (
    'PAMC',  # Penitenciária Agrícola do Monte Cristo
    'CPBV',  # Cadeia Pública Masculina de Boa Vista
    'CPFBV', # Cadeia Pública Feminina de Boa Vista
    'CPP',   # Centro de Progressão Penitenciária
    'CABV',  # Casa do Albergado de Boa Vista
    'UPPRO', # Unidade Prisional de Rorainópolis
    'CME',   # Central de Monitoração Eletrônica
    'DICAP'  # Divisão de Inteligência e Captura
)

# Versão atual do aplicativo (para uso no updater)
current_version = 'v0.1.0'

# Nome padrão do arquivo Excel de saída
excel_filename = 'Informacoes_Presos-02.xlsx'
