"""
Bot de Agendamento WhatsApp
Autor: Gabriel-Dev03
GitHub: github.com/Gabriel-Dev03/bot-agendamento-whatsapp

Recebe mensagens, verifica disponibilidade no Google Sheets
e confirma agendamentos automaticamente.
"""

from fastapi import FastAPI, Request
import httpx
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timedelta
import json
import re

app = FastAPI(title="Bot de Agendamento WhatsApp")

# ─── Configurações ─────────────────────────────────────────
EVOLUTION_API_URL = "http://localhost:8080"  # URL da Evolution API
EVOLUTION_INSTANCE = "minha-instancia"
EVOLUTION_TOKEN = "seu_token_aqui"

SPREADSHEET_ID = "1aBcDeFgHiJkLmNo..."  # ID da planilha Google Sheets
CREDS_FILE = "credentials.json"          # Credenciais da service account Google

NOME_NEGOCIO = "Studio Karol"
SERVICOS = {
    "1": {"nome": "Corte Feminino", "duracao": 60, "preco": "R$ 80"},
    "2": {"nome": "Coloração",      "duracao": 120, "preco": "R$ 180"},
    "3": {"nome": "Escova",         "duracao": 45, "preco": "R$ 60"},
    "4": {"nome": "Hidratação",     "duracao": 30, "preco": "R$ 50"},
    "5": {"nome": "Manicure",       "duracao": 45, "preco": "R$ 35"},
}

HORARIOS_DISPONIVEIS = ["09:00","10:00","11:00","13:00","14:00","15:00","16:00","17:00"]

# Armazena conversas em andamento {telefone: {etapa, dados}}
conversas = {}


# ─── Google Sheets ─────────────────────────────────────────
def conectar_sheets():
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_name(CREDS_FILE, scope)
    client = gspread.authorize(creds)
    return client.open_by_key(SPREADSHEET_ID).sheet1


def horarios_ocupados(data: str) -> list[str]:
    """Retorna horários já agendados em uma data."""
    sheet = conectar_sheets()
    registros = sheet.get_all_records()
    ocupados = [r["horario"] for r in registros if r["data"] == data and r["status"] == "confirmado"]
    return ocupados


def salvar_agendamento(telefone: str, nome: str, servico: str, data: str, horario: str):
    sheet = conectar_sheets()
    sheet.append_row([telefone, nome, servico, data, horario, "confirmado", datetime.now().isoformat()])


# ─── Envio de mensagens ────────────────────────────────────
async def enviar_mensagem(telefone: str, texto: str):
    """Envia mensagem via Evolution API."""
    url = f"{EVOLUTION_API_URL}/message/sendText/{EVOLUTION_INSTANCE}"
    headers = {"apikey": EVOLUTION_TOKEN, "Content-Type": "application/json"}
    payload = {"number": telefone, "text": texto}
    
    async with httpx.AsyncClient() as client:
        await client.post(url, json=payload, headers=headers)


# ─── Fluxo de conversa ─────────────────────────────────────
async def processar_mensagem(telefone: str, texto: str):
    texto = texto.strip()
    estado = conversas.get(telefone, {"etapa": "inicio", "dados": {}})
    etapa = estado["etapa"]
    dados = estado["dados"]
    
    # ETAPA 1: Menu inicial
    if etapa == "inicio" or texto.lower() in ["oi","olá","ola","menu","inicio"]:
        menu = f"""Olá! 😊 Bem-vindo ao *{NOME_NEGOCIO}*!

Sou o assistente virtual. Posso te ajudar a agendar um horário rapidinho!

*Nossos serviços:*
"""
        for num, s in SERVICOS.items():
            menu += f"{num}. {s['nome']} — {s['preco']} ({s['duracao']}min)\n"
        menu += "\nDigite o *número* do serviço desejado:"
        
        await enviar_mensagem(telefone, menu)
        conversas[telefone] = {"etapa": "escolher_servico", "dados": {}}
        return
    
    # ETAPA 2: Escolha do serviço
    if etapa == "escolher_servico":
        if texto in SERVICOS:
            servico = SERVICOS[texto]
            dados["servico"] = servico["nome"]
            dados["servico_num"] = texto
            conversas[telefone] = {"etapa": "escolher_data", "dados": dados}
            
            # Mostra próximos 5 dias úteis
            datas = []
            d = datetime.now()
            while len(datas) < 5:
                d += timedelta(days=1)
                if d.weekday() < 6:  # Seg a Sab
                    datas.append(d.strftime("%d/%m/%Y"))
            
            opcoes = "\n".join([f"{i+1}. {dt}" for i, dt in enumerate(datas)])
            await enviar_mensagem(telefone, f"Ótima escolha! ✂️\n\nPara qual data deseja agendar *{servico['nome']}*?\n\n{opcoes}\n\nDigite o número da data:")
            dados["datas_opcoes"] = datas
        else:
            await enviar_mensagem(telefone, "Por favor, escolha um número válido do cardápio (1 a 5).")
        return
    
    # ETAPA 3: Escolha da data
    if etapa == "escolher_data":
        opcoes = dados.get("datas_opcoes", [])
        if texto.isdigit() and 1 <= int(texto) <= len(opcoes):
            data_escolhida = opcoes[int(texto)-1]
            dados["data"] = data_escolhida
            
            # Mostra horários disponíveis
            data_fmt = datetime.strptime(data_escolhida, "%d/%m/%Y").strftime("%Y-%m-%d")
            ocupados = horarios_ocupados(data_fmt)
            disponiveis = [h for h in HORARIOS_DISPONIVEIS if h not in ocupados]
            
            if not disponiveis:
                await enviar_mensagem(telefone, f"Infelizmente não há horários disponíveis em {data_escolhida}. Tente outra data:\n\n" + "\n".join([f"{i+1}. {dt}" for i, dt in enumerate(opcoes)]))
                return
            
            opcoes_hora = "\n".join([f"{i+1}. {h}" for i, h in enumerate(disponiveis)])
            dados["horarios_opcoes"] = disponiveis
            conversas[telefone] = {"etapa": "escolher_horario", "dados": dados}
            await enviar_mensagem(telefone, f"📅 *{data_escolhida}*\n\nHorários disponíveis:\n{opcoes_hora}\n\nDigite o número do horário:")
        else:
            await enviar_mensagem(telefone, "Por favor, escolha um número válido para a data.")
        return
    
    # ETAPA 4: Horário
    if etapa == "escolher_horario":
        opcoes = dados.get("horarios_opcoes", [])
        if texto.isdigit() and 1 <= int(texto) <= len(opcoes):
            dados["horario"] = opcoes[int(texto)-1]
            conversas[telefone] = {"etapa": "pedir_nome", "dados": dados}
            await enviar_mensagem(telefone, "Perfeito! ⏰\n\nPor último, qual é o seu *nome completo*?")
        else:
            await enviar_mensagem(telefone, "Por favor, escolha um número válido de horário.")
        return
    
    # ETAPA 5: Nome e confirmação
    if etapa == "pedir_nome":
        dados["nome"] = texto.title()
        conversas[telefone] = {"etapa": "confirmado", "dados": dados}
        
        # Salva no Google Sheets
        data_fmt = datetime.strptime(dados["data"], "%d/%m/%Y").strftime("%Y-%m-%d")
        salvar_agendamento(telefone, dados["nome"], dados["servico"], data_fmt, dados["horario"])
        
        confirmacao = f"""✅ *Agendamento confirmado!*

*Nome:* {dados['nome']}
*Serviço:* {dados['servico']}
*Data:* {dados['data']}
*Horário:* {dados['horario']}
*Local:* {NOME_NEGOCIO}

Você receberá um lembrete 1 hora antes. 

Para cancelar ou remarcar, envie *CANCELAR*.

Até logo! 😊"""
        
        await enviar_mensagem(telefone, confirmacao)
        del conversas[telefone]
        return


# ─── Webhook da Evolution API ──────────────────────────────
@app.post("/webhook")
async def webhook(request: Request):
    body = await request.json()
    
    try:
        # Extrai telefone e mensagem do payload da Evolution API
        telefone = body["data"]["key"]["remoteJid"].replace("@s.whatsapp.net", "")
        texto = body["data"]["message"].get("conversation", "")
        
        if texto and not body["data"]["key"].get("fromMe"):
            await processar_mensagem(telefone, texto)
    
    except (KeyError, TypeError):
        pass
    
    return {"status": "ok"}


@app.get("/")
def status():
    return {"status": "Bot rodando", "conversas_ativas": len(conversas)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
