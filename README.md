# Monitor de Sistemas HTTP com SMS

Sistema de monitoramento contínuo de aplicações web utilizando Python.

## Funcionalidades

- Monitoramento HTTP/HTTPS
- Envio de SMS
- Logs automáticos
- Fallback PowerShell
- Serviço Windows via NSSM
- Monitoramento contínuo

## Tecnologias

- Python
- Requests
- PowerShell
- NSSM

## Estrutura

```text
monitor.py
config.json
requirements.txt
```

## Instalação

```bash
pip install -r requirements.txt
```

## Execução

```bash
python monitor.py
```

## Serviço Windows

```powershell
nssm install MonitorSistemas
```