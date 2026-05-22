# Monitor Sistemas HTTP

## Conteúdo

Aplicação desenvolvida em Python para monitoramento contínuo de sistemas web institucionais, realizando validações HTTP/HTTPS automáticas e envio de alertas SMS em caso de indisponibilidade.

O sistema foi projetado para execução contínua em ambiente Windows Server, utilizando serviço Windows via NSSM e monitoramento resiliente com fallback PowerShell para ambientes com incompatibilidade SSL/TLS.

---

## Funcionalidades

- Monitoramento contínuo de sistemas HTTP/HTTPS;  
- Validação de disponibilidade por status HTTP; 
- Verificação de conteúdo esperado na página;
- Controle de falhas consecutivas;
- Envio automático de SMS em caso de indisponibilidade;
- Alerta automático de recuperação do sistema;
- Geração de logs automáticos;
- Fallback PowerShell para problemas TLS/SSL;
- Execução contínua como serviço Windows;
- Configuração simplificada via JSON.

---

## Tecnologias utilizadas

- Python 3  
- Requests  
- urllib3  
- PowerShell  
- JSON  
- Logging  
- NSSM (Windows Service)  
- Git e GitHub  

---

## Como rodar o projeto

### Execução em ambiente de desenvolvimento

```bash
python monitor.py
```

---

## Estrutura do projeto

```text
monitor-sistemas-http/
├── monitor.py
├── config.json
├── requirements.txt
├── README.md
├── logs/
│   └── monitor_sistemas.log
└── .venv/
```

---

## Requisitos do servidor

- Windows Server com acesso à internet;
- Python 3 instalado;
- PowerShell habilitado;
- Acesso liberado aos endpoints monitorados;
- Permissão de execução de serviços Windows; 
- NSSM instalado;
- Permissão de saída HTTPS para API SMS.

---

## Configuração de produção

Execução como serviço Windows via NSSM:

```powershell
C:\nssm-2.24\win64\nssm.exe install MonitorSistemas
```

---

## Configuração do serviço

### Application Path

```text
C:\MonitorSistemas\.venv\Scripts\python.exe
```

### Arguments

```text
monitor.py
```

### Startup Directory

```text
C:\MonitorSistemas
```

### Inicialização do serviço

```powershell
net start MonitorSistemas
```

O serviço deve estar configurado para iniciar automaticamente junto ao sistema operacional.

---

## Configuração do monitoramento

O arquivo `config.json` permite configurar:

- Intervalo entre verificações;
- Quantidade de falhas antes do alerta;
- URLs monitoradas;
- Métodos HTTP;
- Timeout das requisições;
- Validação SSL;
- Fallback PowerShell;
- Texto esperado no HTML.

---

## Logs

Arquivos gerados em:

```text
C:\MonitorSistemas\logs\
```

Arquivo principal:

```text
monitor_sistemas.log
```

---

## Segurança

- Controle de falhas consecutivas para evitar falso positivo;
- Validação de conteúdo HTML retornado;
- Monitoramento resiliente com fallback PowerShell;
- Execução restrita ao ambiente institucional;
- Possibilidade de integração futura com variáveis de ambiente (.env);
- Registro completo de eventos em log.

---

## Observações

- Aplicação desenvolvida para uso interno institucional;
- Projeto otimizado para baixa utilização de recursos;
- Compatível com execução contínua 24x7;
- Dependência de conectividade HTTPS externa;
- Possibilidade de expansão para monitoramento Oracle, portas TCP, containers e JMX.

---

## Autor

Valmir Moro  
Setor de TI – FEAS  

---

## Used IDE

Visual Studio Code.
