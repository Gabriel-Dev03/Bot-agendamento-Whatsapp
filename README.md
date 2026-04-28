# 🤖 Bot de Agendamento — WhatsApp

Bot de agendamento automático via WhatsApp integrado ao Google Sheets. O cliente conversa com o bot, escolhe o serviço, a data e o horário — tudo sem o dono precisar responder manualmente.

---

## ✨ Como funciona

O cliente manda mensagem no WhatsApp → o bot responde com o menu de serviços → cliente escolhe data e horário disponível → bot verifica no Google Sheets se o horário está livre → confirma o agendamento e salva na planilha.

```
Cliente: "Oi"
Bot: "Bem-vindo ao Studio Karol! Nossos serviços: 1. Corte Feminino..."
Cliente: "1"
Bot: "Para qual data? 1. 28/04 2. 29/04..."
Cliente: "2"
Bot: "Horários disponíveis: 1. 09:00 2. 10:00..."
Cliente: "1"
Bot: "Qual seu nome?"
Cliente: "Maria Silva"
Bot: "✅ Agendamento confirmado! Corte Feminino — 29/04 às 09:00"
```

---

## 🛠️ Tecnologias

- **Python** — linguagem principal
- **FastAPI** — servidor web para receber o webhook
- **Evolution API** — integração com WhatsApp
- **Google Sheets** — agenda e histórico de agendamentos
- **gspread** — leitura e escrita na planilha
- **httpx** — envio de mensagens assíncronas

---

## 📋 Funcionalidades

- Menu interativo com serviços, preços e duração
- Listagem automática dos próximos 5 dias úteis
- Verificação de horários já ocupados em tempo real
- Confirmação com resumo completo do agendamento
- Salvamento automático no Google Sheets
- Suporte a múltiplas conversas simultâneas
- Comando `CANCELAR` para remarcar

---

## ⚙️ Configuração

### 1. Clone o repositório
```bash
git clone https://github.com/Gabriel-Dev03/Bot-agendamento-Whatsapp.git
cd Bot-agendamento-Whatsapp
```

### 2. Instale as dependências
```bash
pip install fastapi uvicorn httpx gspread oauth2client
```

### 3. Configure as variáveis no `bot.py`
```python
EVOLUTION_API_URL = "http://localhost:8080"  # URL da sua Evolution API
EVOLUTION_INSTANCE = "sua-instancia"
EVOLUTION_TOKEN = "seu_token"

SPREADSHEET_ID = "id_da_sua_planilha"
CREDS_FILE = "credentials.json"  # Credenciais Google Service Account
```

### 4. Configure seus serviços
```python
SERVICOS = {
    "1": {"nome": "Seu Serviço", "duracao": 60, "preco": "R$ 80"},
    ...
}
```

### 5. Rode o servidor
```bash
uvicorn bot:app --host 0.0.0.0 --port 8000
```

### 6. Configure o webhook na Evolution API
Aponte o webhook para: `http://seu-servidor:8000/webhook`

---

## 📊 Estrutura da Planilha Google Sheets

| telefone | nome | serviço | data | horário | status | criado_em |
|----------|------|---------|------|---------|--------|-----------|
| 5511999... | Maria Silva | Corte Feminino | 2025-04-28 | 09:00 | confirmado | 2025-04-27T... |

---

## 📁 Estrutura do projeto

```
Bot-agendamento-Whatsapp/
├── bot.py           # Código principal
├── credentials.json # Credenciais Google (não versionar!)
└── README.md
```

---

## ⚠️ Observações

- Nunca suba o `credentials.json` no GitHub — adicione ao `.gitignore`
- As conversas ficam em memória — reiniciar o servidor limpa conversas em andamento
- Compatível com qualquer negócio: salão, barbearia, clínica, etc. Basta editar `SERVICOS` e `NOME_NEGOCIO`

---

## 👤 Autor

**Gabriel Jesus** — [github.com/Gabriel-Dev03](https://github.com/Gabriel-Dev03)
