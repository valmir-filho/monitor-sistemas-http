"""
Monitor de Sistemas HTTP com Alerta via SMS.

Este script realiza o monitoramento contínuo de sistemas web configurados
em um arquivo config.json. Para cada sistema, ele executa uma requisição HTTP,
valida o status de resposta, opcionalmente verifica um texto esperado no HTML
e envia SMS em caso de indisponibilidade.

Também possui fallback via PowerShell para ambientes Windows onde determinados
endpoints HTTPS apresentam incompatibilidade TLS/SSL com a biblioteca requests.
"""

import json
import time
import logging
import subprocess
from pathlib import Path
from datetime import datetime

import requests
import urllib3
from requests.auth import HTTPBasicAuth


# Desativa avisos de SSL inseguro quando algum sistema estiver configurado
# com "verificar_ssl": false no config.json.
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


# ============================================================
# Configurações da API de SMS.
# ============================================================

API_SMS_URL = "https://api360.classeaservicos.com.br/api/send.php"
API_SMS_USUARIO = "ti@feas.curitiba.pr.gov.br"
API_SMS_SENHA = "SUA_SENHA_AQUI"

CODIGO_CARTEIRA = "124761724767135"
CODIGO_FORNECEDOR = "classea_token"


# ============================================================
# Configurações de diretórios e arquivos.
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
CONFIG_FILE = BASE_DIR / "config.json"
LOG_DIR = BASE_DIR / "logs"
LOG_FILE = LOG_DIR / "monitor_sistemas.log"

LOG_DIR.mkdir(exist_ok=True)


logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)


# Armazena o estado atual de cada sistema monitorado.
status_sistemas = {}


def carregar_configuracao():
    """
    Carrega as configurações do arquivo config.json.

    Returns:
        dict: Configurações gerais e lista de sistemas monitorados.
    """
    with open(CONFIG_FILE, "r", encoding="utf-8") as arquivo:
        return json.load(arquivo)


def enviar_sms(mensagem):
    """
    Envia uma mensagem SMS para a lista de telefones configurada.

    Args:
        mensagem (str): Texto que será enviado por SMS.
    """
    telefones = [
        "41991256214",
        "41996907249",
        "41999580050",
        "41996166090",
    ]

    sms_data = {
        "codigo_carteira": CODIGO_CARTEIRA,
        "codigo_fornecedor": CODIGO_FORNECEDOR,
        "envios": [],
    }

    for telefone in telefones:
        sms_data["envios"].append({
            "numero": telefone,
            "mensagem": mensagem,
        })

    try:
        response = requests.post(
            API_SMS_URL,
            json=sms_data,
            auth=HTTPBasicAuth(API_SMS_USUARIO, API_SMS_SENHA),
            timeout=10,
        )

        if response.status_code == 200:
            logging.info(f"SMS enviado com sucesso: {mensagem}")
            print("SMS enviado com sucesso.")
        else:
            logging.error(
                f"Falha ao enviar SMS. "
                f"Status: {response.status_code}. "
                f"Retorno: {response.text}"
            )
            print(f"Falha ao enviar SMS: {response.status_code}")

    except requests.exceptions.RequestException as erro:
        logging.error(f"Erro ao enviar SMS: {repr(erro)}")
        print(f"Erro ao enviar SMS: {erro}")


def testar_com_powershell(url, texto_esperado=None, timeout=10):
    """
    Testa a disponibilidade de uma URL usando PowerShell.

    Este fallback é útil em servidores Windows quando o requests apresenta
    erro de negociação SSL/TLS, mesmo com o endpoint acessível via navegador
    ou Invoke-WebRequest.

    Args:
        url (str): URL que será testada.
        texto_esperado (str, optional): Texto que deve existir no conteúdo.
        timeout (int): Tempo máximo, em segundos, para a requisição.

    Returns:
        dict: Resultado padronizado do teste.
    """
    try:
        inicio = time.time()

        comando = [
            "powershell",
            "-Command",
            (
                f"$r = Invoke-WebRequest '{url}' "
                f"-UseBasicParsing "
                f"-TimeoutSec {timeout}; "
                f"Write-Output $r.StatusCode; "
                f"Write-Output $r.Content"
            ),
        ]

        resultado = subprocess.run(
            comando,
            capture_output=True,
            text=True,
            timeout=timeout + 5,
        )

        tempo_resposta = round(time.time() - inicio, 2)

        if resultado.returncode != 0:
            return {
                "online": False,
                "status_code": None,
                "tempo_resposta": tempo_resposta,
                "erro": resultado.stderr.strip(),
            }

        saida = resultado.stdout.lower()

        if "200" not in saida:
            return {
                "online": False,
                "status_code": None,
                "tempo_resposta": tempo_resposta,
                "erro": "PowerShell não retornou HTTP 200",
            }

        if texto_esperado and texto_esperado.lower() not in saida:
            return {
                "online": False,
                "status_code": 200,
                "tempo_resposta": tempo_resposta,
                "erro": (
                    f"Texto esperado não encontrado via PowerShell: "
                    f"{texto_esperado}"
                ),
            }

        return {
            "online": True,
            "status_code": 200,
            "tempo_resposta": tempo_resposta,
            "erro": None,
        }

    except Exception as erro:
        return {
            "online": False,
            "status_code": None,
            "tempo_resposta": None,
            "erro": f"Erro PowerShell: {repr(erro)}",
        }


def testar_sistema(sistema):
    """
    Testa um sistema configurado no config.json.

    O teste pode ser feito via GET ou POST. Além do status HTTP, a função
    também pode validar se determinado texto existe no conteúdo retornado.

    Args:
        sistema (dict): Configuração individual do sistema.

    Returns:
        dict: Resultado padronizado contendo status, tempo e erro.
    """
    url = sistema["url"]
    metodo = sistema.get("metodo", "GET").upper()
    headers = sistema.get("headers", {})
    payload = sistema.get("payload", {})
    status_esperado = sistema.get("status_esperado", [200])
    timeout = sistema.get("timeout_segundos", 10)
    verificar_ssl = sistema.get("verificar_ssl", True)

    try:
        inicio = time.time()

        if metodo == "GET":
            resposta = requests.get(
                url,
                headers=headers,
                timeout=timeout,
                verify=verificar_ssl,
                allow_redirects=True,
            )

        elif metodo == "POST":
            resposta = requests.post(
                url,
                json=payload,
                headers=headers,
                timeout=timeout,
                verify=verificar_ssl,
                allow_redirects=True,
            )

        else:
            raise ValueError(f"Método HTTP não suportado: {metodo}")

        tempo_resposta = round(time.time() - inicio, 2)
        conteudo = resposta.text.lower()
        texto_esperado = sistema.get("texto_esperado")

        if resposta.status_code not in status_esperado:
            return {
                "online": False,
                "status_code": resposta.status_code,
                "tempo_resposta": tempo_resposta,
                "erro": f"Status HTTP inesperado: {resposta.status_code}",
            }

        if texto_esperado and texto_esperado.lower() not in conteudo:
            return {
                "online": False,
                "status_code": resposta.status_code,
                "tempo_resposta": tempo_resposta,
                "erro": f"Texto esperado não encontrado: {texto_esperado}",
            }

        return {
            "online": True,
            "status_code": resposta.status_code,
            "tempo_resposta": tempo_resposta,
            "erro": None,
        }

    except requests.exceptions.ConnectionError:
        if sistema.get("usar_powershell_fallback", False):
            return testar_com_powershell(
                url=url,
                texto_esperado=sistema.get("texto_esperado"),
                timeout=timeout,
            )

        return {
            "online": False,
            "status_code": None,
            "tempo_resposta": None,
            "erro": "Erro de conexão",
        }

    except requests.exceptions.SSLError:
        if sistema.get("usar_powershell_fallback", False):
            return testar_com_powershell(
                url=url,
                texto_esperado=sistema.get("texto_esperado"),
                timeout=timeout,
            )

        return {
            "online": False,
            "status_code": None,
            "tempo_resposta": None,
            "erro": "Erro SSL",
        }

    except requests.exceptions.Timeout:
        return {
            "online": False,
            "status_code": None,
            "tempo_resposta": None,
            "erro": "Timeout",
        }

    except Exception as erro:
        return {
            "online": False,
            "status_code": None,
            "tempo_resposta": None,
            "erro": f"Erro: {repr(erro)}",
        }


def inicializar_status(config):
    """
    Inicializa o controle de falhas de cada sistema.

    Args:
        config (dict): Configuração carregada do config.json.
    """
    for sistema in config["sistemas"]:
        nome = sistema["nome"]

        status_sistemas[nome] = {
            "falhas_consecutivas": 0,
            "alerta_enviado": False,
        }


def processar_resultado(sistema, resultado, config):
    """
    Processa o resultado de uma verificação.

    Esta função decide se deve apenas registrar log, enviar alerta de queda
    ou enviar alerta de recuperação.

    Args:
        sistema (dict): Configuração do sistema monitorado.
        resultado (dict): Resultado retornado por testar_sistema().
        config (dict): Configuração geral.
    """
    nome = sistema["nome"]
    url = sistema["url"]
    falhas_para_alertar = config.get("falhas_para_alertar", 3)

    estado = status_sistemas[nome]

    if resultado["online"]:
        logging.info(
            f"{nome} ONLINE | "
            f"HTTP {resultado['status_code']} | "
            f"{resultado['tempo_resposta']}s | "
            f"{url}"
        )

        print(
            f"[OK] {nome} | "
            f"HTTP {resultado['status_code']} | "
            f"{resultado['tempo_resposta']}s"
        )

        if estado["alerta_enviado"]:
            mensagem = (
                f"RECUPERADO: {nome} voltou a responder em "
                f"{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}."
            )
            enviar_sms(mensagem)

        estado["falhas_consecutivas"] = 0
        estado["alerta_enviado"] = False

    else:
        estado["falhas_consecutivas"] += 1

        logging.warning(
            f"{nome} FORA | "
            f"Falha {estado['falhas_consecutivas']} | "
            f"Erro: {resultado['erro']} | "
            f"URL: {url}"
        )

        print(
            f"[FALHA] {nome} | "
            f"Falha {estado['falhas_consecutivas']} | "
            f"{resultado['erro']}"
        )

        if (
            estado["falhas_consecutivas"] >= falhas_para_alertar
            and not estado["alerta_enviado"]
        ):
            mensagem = (
                f"ALERTA: {nome} fora do ar. "
                f"Falhas consecutivas: {estado['falhas_consecutivas']}. "
                f"Erro: {resultado['erro']}. "
                f"Horário: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}."
            )

            enviar_sms(mensagem)
            estado["alerta_enviado"] = True


def monitorar():
    """
    Executa o loop principal de monitoramento.

    A cada ciclo, todos os sistemas configurados são verificados. Após isso,
    o script aguarda o intervalo definido no config.json.
    """
    config = carregar_configuracao()
    inicializar_status(config)

    intervalo = config.get("intervalo_segundos", 60)

    logging.info("Monitoramento iniciado.")
    print("Monitoramento iniciado.")

    while True:
        print(f"\nVerificação em {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")

        for sistema in config["sistemas"]:
            resultado = testar_sistema(sistema)
            processar_resultado(sistema, resultado, config)

        time.sleep(intervalo)


if __name__ == "__main__":
    monitorar()
