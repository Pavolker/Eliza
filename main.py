import asyncio
import re
import random
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
import uvicorn
import os

from agent import OpenRouterAgent

app = FastAPI(title="ELIZA 2026")

@app.get("/")
async def get_index():
    return FileResponse("index.html")

@app.get("/style.css")
async def get_css():
    return FileResponse("style.css")

@app.get("/app.js")
async def get_js():
    return FileResponse("app.js")

async def analyze_emotion(text: str) -> str:
    text = text.lower()
    
    keywords = {
        "sadness": ["triste", "cansado", "exaurido", "desanimado", "chorar", "choro", "deprimido", "solitário", "sozinho", "dor", "sofrer", "frustrado", "frustração", "desespero", "infeliz", "exaust"],
        "joy": ["feliz", "alegre", "ótimo", "bom", "maravilhoso", "excelente", "animado", "sorrir", "gostar", "amor", "amar", "sucesso", "consegui", "contente"],
        "anger": ["bravo", "raiva", "irritado", "ódio", "odiar", "chateado", "nervoso", "injustiça", "briga", "discussão", "futo"],
        "anxiety": ["ansioso", "medo", "preocupado", "pânico", "angústia", "receio", "assustado", "terror", "nervosismo", "tensão", "tenso"]
    }
    
    for emotion, words in keywords.items():
        if any(word in text for word in words):
            return emotion
            
    return "calm"

REGRAS_FALLBACK = {
    r'.*mãe.*': [
        "Fale-me mais sobre sua família.",
        "Como é sua relação com sua mãe?"
    ],
    r'.*pai.*': [
        "Me fale mais sobre seu pai.",
        "Como você se sente em relação ao seu pai?"
    ],
    r'.*estou (deprimido|triste).*': [
        "Lamento ouvir que você está {0}. O que te deixa assim?",
        "Você acha que vir aqui te ajuda a não ficar {0}?"
    ],
    r'.*eu preciso de (.*)': [
        "Por que você precisa de {0}?",
        "Isso realmente te ajudaria?"
    ],
    r'.*por que você não (.*)': [
        "Você realmente acha que eu não {0}?",
        "Talvez no devido tempo eu vá {0}."
    ],
    r'.*talvez (.*)': [
        "Você parece um pouco incerto. Por que diz isso?",
        "Você acha que isso é provável?"
    ],
    r'.*não (.*)': [
        "Por que não?",
        "Você está sendo um pouco negativo.",
        "O que te faz dizer 'não'?"
    ],
    r'(.*)': [
        "Por favor, continue.",
        "Por que você diz isso?",
        "Compreendo. Diga-me mais."
    ]
}

def fallback_responder(texto_usuario: str) -> str:
    texto_usuario = texto_usuario.lower()
    for padrao, respostas in REGRAS_FALLBACK.items():
        match = re.match(padrao, texto_usuario)
        if match:
            resposta = random.choice(respostas)
            if '{0}' in resposta and match.groups():
                return resposta.format(match.group(1))
            return resposta
    return "Compreendo. Diga-me mais sobre isso."

@app.websocket("/ws/{conversation_id}")
async def websocket_endpoint(websocket: WebSocket, conversation_id: str):
    await websocket.accept()
    
    if conversation_id in ["null", "undefined", "new"]:
        conversation_id = None
        
    agent = OpenRouterAgent(conversation_id=conversation_id)
    
    try:
        await websocket.send_json({"type": "status", "content": "connected"})
        
        while True:
            user_message = await websocket.receive_text()
            
            emotion_task = asyncio.create_task(analyze_emotion(user_message))
            
            await websocket.send_json({"type": "typing", "content": True})
            
            try:
                async for token in agent.chat(user_message):
                    await websocket.send_json({"type": "token", "content": token})
                await websocket.send_json({"type": "typing", "content": False})
            except Exception as api_err:
                print(f"OpenRouter API falhou: {api_err}. Ativando fallback clássico...")
                await websocket.send_json({"type": "typing", "content": False})
                
                local_response = fallback_responder(user_message)
                for word in local_response.split(" "):
                    await websocket.send_json({"type": "token", "content": word + " "})
                    await asyncio.sleep(0.08)
            
            if agent.conversation_id:
                await websocket.send_json({"type": "session_id", "content": agent.conversation_id})
            
            try:
                emotion = await emotion_task
            except Exception:
                emotion = "calm"
            
            await websocket.send_json({"type": "emotion", "content": emotion})
            await websocket.send_json({"type": "end"})
            
    except WebSocketDisconnect:
        print(f"Sessão {conversation_id} desconectada do WebSocket.")
    except Exception as e:
        print(f"Erro no WebSocket para sessão {conversation_id}: {e}")
        try:
            await websocket.send_json({"type": "error", "content": "Desculpe, ocorreu um soluço na nossa conexão. Estou aqui ouvindo você."})
        except Exception:
            pass
    finally:
        await agent.close()

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)