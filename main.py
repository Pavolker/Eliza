import asyncio
import re
import random
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
import uvicorn
import os
import logging
from contextlib import asynccontextmanager
import asyncpg

from agent import OpenRouterAgent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("eliza.main")

# Dicionário global para rastrear conexões WebSocket ativas por session_id
active_connections = {}

OBJECTS_METADATA = {
    "limites": {
        "title": "Limites que reconhece",
        "icon": "💡",
        "foyer": "interne",
        "text": "Você tem refletido sobre seus limites pessoais e a dificuldade em dizer 'não' quando necessário.",
        "keywords": ["dizer não", "não consigo dizer não", "limite", "limites", "sempre aceito", "aceitar tudo"]
    },
    "reacoes": {
        "title": "Reações recorrentes",
        "icon": "🔄",
        "foyer": "interne",
        "text": "Padrões automáticos e comportamentos de resposta interpessoal que tendem a se repetir ciclicamente.",
        "keywords": ["de novo", "sempre faço isso", "padrão", "repetir", "recorrente"]
    },
    "sensacoes": {
        "title": "Sensações do corpo",
        "icon": "🫀",
        "foyer": "interne",
        "text": "A percepção de manifestações físicas, tensões ou batimentos cardíacos que revelam o estado emocional.",
        "keywords": ["meu corpo", "sinto no peito", "corporal", "tensão física", "dor no corpo", "físico", "física"]
    },
    "ritmos": {
        "title": "Ritmos do seu corpo",
        "icon": "⏰",
        "foyer": "interne",
        "text": "Seus ciclos biológicos, padrões de sono, fadiga crônica e como reage ao esgotamento físico.",
        "keywords": ["sono", "cansaço", "energia", "cansado", "cansada", "exaust", "dormir", "fadiga"]
    },
    "conflito": {
        "title": "Como entra em conflito",
        "icon": "⚔️",
        "foyer": "interne",
        "text": "Sua postura, gatilhos de agressividade ou recuo diante de desentendimentos e atritos.",
        "keywords": ["briga", "brigas", "discussão", "discussões", "conflito", "conflitos", "chefe", "atrito", "atritos", "discutir", "cobrança", "cobranças"]
    },
    "dependencias": {
        "title": "Dependências que te prendem",
        "icon": "🔗",
        "foyer": "interne",
        "text": "Apego a aprovações, hábitos ou dinâmicas emocionais que limitam sua autonomia e poder de escolha.",
        "keywords": ["não consigo sair", "preciso disso", "dependência", "dependências", "preso", "presa", "amarrado", "amarrada", "perfeccionismo", "aprovação"]
    },
    "praticas": {
        "title": "Práticas reflexivas",
        "icon": "🧘",
        "foyer": "interne",
        "text": "Hábitos e rotinas de autopercepção, pausas deliberadas ou momentos de escuta atenta a si mesmo.",
        "keywords": ["medito", "caminho", "escrevo", "pausa", "meditação", "respiro", "caminhada"]
    },
    "observar": {
        "title": "Capacidade de se observar",
        "icon": "👁️",
        "foyer": "interne",
        "text": "Capacidade de distanciar-se das reações automáticas e analisar os próprios comportamentos.",
        "keywords": ["percebi que", "me observei", "reparei", "notei em mim", "percepção"]
    },
    "raizes": {
        "title": "Raízes culturais",
        "icon": "🌳",
        "foyer": "externe",
        "text": "A herança familiar, o contexto social e as influências étnicas na sua formação como sujeito.",
        "keywords": ["minha família", "de onde venho", "minha terra", "minha criação", "origem", "origens"]
    },
    "comunicacao": {
        "title": "Jeito de se comunicar",
        "icon": "💬",
        "foyer": "externe",
        "text": "Estilo de expressão verbal, clareza ao comunicar necessidades e assertividade nas conversas.",
        "keywords": ["falo demais", "não consigo expressar", "falar", "comunicação", "expressar", "assertividade"]
    },
    "historias": {
        "title": "Histórias que te formaram",
        "icon": "📖",
        "foyer": "externe",
        "text": "Narrativas e memórias de infância, lições herdadas e papéis que assumiu na história familiar.",
        "keywords": ["quando era criança", "meu pai", "minha mãe", "em casa", "infância", "passado", "antigamente"]
    },
    "lacos": {
        "title": "Laços que te sustentam",
        "icon": "🤝",
        "foyer": "externe",
        "text": "Sua rede de suporte afetivo, amigos, parceiros e pessoas nas quais encontra segurança emocional.",
        "keywords": ["meus amigos", "minha parceira", "parceiro", "apoio", "suporte", "rede de apoio", "amizades", "amigo", "amiga"]
    },
    "valores": {
        "title": "Valores que te guiam",
        "icon": "⭐",
        "foyer": "externe",
        "text": "Crenças fundamentais, ética pessoal e ideais que direcionam suas decisões importantes.",
        "keywords": ["o que importa", "acredito", "valores", "justiça", "equilíbrio", "princípios", "ética"]
    },
    "emocoes": {
        "title": "Emoções que expressa",
        "icon": "😊",
        "foyer": "strategique",
        "text": "Seu repertório expressivo e o modo como as emoções são manifestadas nas relações cotidianas.",
        "keywords": ["sinto muito", "estou feliz", "emocional", "expressar o que sinto"]
    },
    "lidar_emocoes": {
        "title": "Como lida com emoções",
        "icon": "🎢",
        "foyer": "strategique",
        "text": "Como você regula sentimentos intensos, estresse, ansiedade e angústia.",
        "keywords": ["não sei lidar", "tento controlar", "regulação", "controlar minhas emoções"]
    },
    "habitos": {
        "title": "Hábitos do dia a dia",
        "icon": "📅",
        "foyer": "strategique",
        "text": "Suas rotinas práticas e o impacto delas na sua saúde, foco e estabilidade psíquica.",
        "keywords": ["todo dia", "minha rotina", "hábitos", "cotidiano", "diariamente"]
    },
    "saude": {
        "title": "Como está sua saúde",
        "icon": "🩺",
        "foyer": "strategique",
        "text": "Seu nível de vitalidade, sono, nutrição e o cuidado geral com a saúde física e mental.",
        "keywords": ["saúde", "médico", "médica", "dor", "dores", "doença", "doenças", "vitalidade", "corpo", "físico", "física"]
    },
    "decide": {
        "title": "Como decide",
        "icon": "⚖️",
        "foyer": "strategique",
        "text": "Processos cognitivos e emocionais na hora de fazer escolhas importantes.",
        "keywords": ["não sei decidir", "escolhas", "decidir", "decisão", "decisões", "escolha"]
    },
    "metacognicao": {
        "title": "Como pensa sobre pensar",
        "icon": "🧠",
        "foyer": "strategique",
        "text": "Suas habilidades de metacognição, ruminação mental ou observação dos próprios pensamentos.",
        "keywords": ["penso demais", "minha mente", "metacognição", "pensamentos", "ruminar", "ruminação"]
    }
}

def detect_card_triggers(text: str, current_triggered: set) -> list:
    text = text.lower()
    newly_triggered = []
    
    # 1. Verifica os 27 objetos (mapeados no dicionário)
    for card_id, metadata in OBJECTS_METADATA.items():
        if card_id not in current_triggered:
            if any(kw in text for kw in metadata["keywords"]):
                current_triggered.add(card_id)
                newly_triggered.append({
                    "type": "card",
                    "id": card_id,
                    "title": metadata["title"],
                    "icon": metadata["icon"],
                    "foyer": metadata["foyer"],
                    "text": metadata["text"],
                    "status": "novo"
                })
                
    # 2. Verifica conexões
    # Exemplo: Conexão entre Limites e Histórias
    if "conexao_limites_historias" not in current_triggered:
        if "limites" in current_triggered and ("historias" in current_triggered or "raizes" in current_triggered):
            current_triggered.add("conexao_limites_historias")
            newly_triggered.append({
                "type": "connection",
                "id": "conexao_limites_historias",
                "title": "🔗 CONEXÃO DESCOBERTA",
                "icon": "🔗",
                "foyer": "connection",
                "text": "Seus LIMITES aparecem quando você fala de suas HISTÓRIAS e origens familiares.",
                "status": "novo"
            })
    # Exemplo: Conexão entre Ritmos e Hábitos
    if "conexao_ritmos_habitos" not in current_triggered:
        if "ritmos" in current_triggered and "habitos" in current_triggered:
            current_triggered.add("conexao_ritmos_habitos")
            newly_triggered.append({
                "type": "connection",
                "id": "conexao_ritmos_habitos",
                "title": "🔗 CONEXÃO DESCOBERTA",
                "icon": "🔗",
                "foyer": "connection",
                "text": "A regulação dos seus RITMOS corporais está ligada aos seus HÁBITOS diários.",
                "status": "novo"
            })
            
    # 3. Verifica Saltos (Sauts d'Évolution)
    saut_keywords = ["percebi", "entendi que", "agora posso", "vou mudar", "consegui", "mudei", "comecei a", "ficou claro", "percepção"]
    if "saut_evolution" not in current_triggered:
        if any(kw in text for kw in saut_keywords):
            if len(current_triggered) > 0:
                current_triggered.add("saut_evolution")
                newly_triggered.append({
                    "type": "saut",
                    "id": "saut_evolution",
                    "title": "✨ SALTO EVOLUTIVO",
                    "icon": "✨",
                    "foyer": "saut",
                    "text": "Você percebeu algo novo: conectou seus limites a escolhas mais conscientes.",
                    "status": "novo"
                })
                
    # 4. Verifica Reflexão (após múltiplos objetos ativados)
    if "reflexao" not in current_triggered:
        # Se o usuário já ativou pelo menos 2 objetos, sugere reflexão
        if len([c for c in current_triggered if c in OBJECTS_METADATA]) >= 2:
            current_triggered.add("reflexao")
            newly_triggered.append({
                "type": "reflexao",
                "id": "reflexao",
                "title": "📝 PARA LEVAR",
                "icon": "📝",
                "foyer": "reflexao",
                "text": "O que aconteceria se você experimentasse dizer 'não' uma vez essa semana?",
                "status": "novo"
            })
            
    return newly_triggered

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Conexão com o banco de dados PostgreSQL
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        # Fallback local se não configurado
        database_url = "postgresql://eliza:Eliza2026DB!@localhost:5432/eliza"
        
    app.state.db_pool = None
    try:
        # O driver asyncpg necessita do prefixo postgresql:// puro
        connection_url = database_url.replace("postgresql+asyncpg://", "postgresql://")
        logger.info(f"Conectando ao banco de dados: {connection_url}")
        pool = await asyncpg.create_pool(connection_url)
        app.state.db_pool = pool
        logger.info("Conexão ao PostgreSQL realizada com sucesso.")
        
        # Inicializa a tabela se não existir
        async with pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id SERIAL PRIMARY KEY,
                    conversation_id VARCHAR(100) NOT NULL,
                    role VARCHAR(20) NOT NULL,
                    content TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON messages(conversation_id);
            """)
            logger.info("Tabela de mensagens verificada/criada.")
    except Exception as e:
        logger.warning(f"Erro ao inicializar banco de dados: {e}. Executando com histórico em memória.")
        
    yield
    
    # Encerra pool de conexões
    if app.state.db_pool:
        await app.state.db_pool.close()
        logger.info("Pool de conexões com o banco encerrado.")

app = FastAPI(title="ELIZA 2026", lifespan=lifespan)

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
    # Remove pontuação para separar palavras de forma limpa
    text_clean = re.sub(r'[^\w\s]', ' ', text)
    words_list = text_clean.split()
    
    negations = {"não", "nunca", "jamais", "nem", "sem", "nada"}
    
    keywords = {
        "sadness": ["triste", "cansado", "cansada", "exaurido", "exaurida", "desanimado", "desanimada", "chorar", "choro", "deprimido", "deprimida", "solitário", "solitária", "sozinho", "sozinha", "dor", "sofrer", "frustrado", "frustrada", "frustração", "desespero", "infeliz", "exaust"],
        "joy": ["feliz", "alegre", "ótimo", "bom", "maravilhoso", "excelente", "animado", "animada", "sorrir", "gostar", "amor", "amar", "sucesso", "consegui", "contente"],
        "anger": ["bravo", "brava", "raiva", "irritado", "irritada", "ódio", "odiar", "chateado", "chateada", "nervoso", "nervosa", "injustiça", "briga", "discussão", "futo"],
        "anxiety": ["ansioso", "ansiosa", "medo", "preocupado", "preocupada", "pânico", "angústia", "receio", "assustado", "assustada", "terror", "nervosismo", "tensão", "tenso", "tensa"]
    }
    
    for emotion, words in keywords.items():
        for word in words:
            if word in text:
                # Se a palavra-chave foi encontrada no texto, vamos inspecionar as palavras limpas
                for idx, clean_word in enumerate(words_list):
                    if word in clean_word:
                        # Verifica se há negação nas 3 posições anteriores
                        start_idx = max(0, idx - 3)
                        if any(words_list[prev_idx] in negations for prev_idx in range(start_idx, idx)):
                            # Encontrou uma negação próxima, portanto ignora esta palavra-chave
                            break
                else:
                    # Se saiu do loop sem o break (ou seja, nenhuma ocorrência foi negada), retorna a emoção
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
        
    pool = websocket.app.state.db_pool
    agent = OpenRouterAgent(conversation_id=conversation_id, pool=pool)
    
    # Carrega histórico existente se houver
    await agent.load_history()
    
    # Reconstrói os cards disparados a partir do histórico de mensagens
    triggered_cards = set()
    historical_triggers = []
    for msg in agent.messages:
        if msg["role"] in ["user", "assistant"]:
            triggers = detect_card_triggers(msg["content"], triggered_cards)
            for t in triggers:
                t["status"] = "ativo" # marca como ativo na carga histórica
                historical_triggers.append(t)
    
    # Gerenciamento de conexões concorrentes/abertura de múltiplas abas
    if agent.conversation_id:
        if agent.conversation_id in active_connections:
            old_ws = active_connections[agent.conversation_id]
            try:
                logger.info(f"Conexão concorrente detectada para sessão {agent.conversation_id}. Desconectando aba antiga.")
                await old_ws.send_json({
                    "type": "error", 
                    "content": "Sessão iniciada em outra aba. Esta aba foi desconectada para evitar conflitos."
                })
                await old_ws.close()
            except Exception as e:
                logger.warning(f"Erro ao desconectar WebSocket antigo: {e}")
        
        active_connections[agent.conversation_id] = websocket
    
    try:
        await websocket.send_json({"type": "status", "content": "connected"})
        
        # Envia os cards históricos acumulados para o frontend iniciar com eles carregados
        for trigger in historical_triggers:
            await websocket.send_json({"type": "card_trigger", "content": trigger})
        
        while True:
            user_message = await websocket.receive_text()
            
            # 1. Verifica gatilhos de cards no prompt do usuário
            user_triggers = detect_card_triggers(user_message, triggered_cards)
            for trigger in user_triggers:
                await websocket.send_json({"type": "card_trigger", "content": trigger})
            
            emotion_task = asyncio.create_task(analyze_emotion(user_message))
            
            await websocket.send_json({"type": "typing", "content": True})
            
            full_response_or_fallback = ""
            try:
                async for token in agent.chat(user_message):
                    await websocket.send_json({"type": "token", "content": token})
                    full_response_or_fallback += token
                await websocket.send_json({"type": "typing", "content": False})
            except Exception as api_err:
                logger.error(f"OpenRouter API falhou: {api_err}. Ativando fallback clássico...")
                await websocket.send_json({"type": "typing", "content": False})
                
                local_response = fallback_responder(user_message)
                full_response_or_fallback = local_response
                
                # Registra o fallback clássico no histórico e banco de dados
                await agent.add_assistant_message(local_response)
                
                for word in local_response.split(" "):
                    await websocket.send_json({"type": "token", "content": word + " "})
                    await asyncio.sleep(0.08)
            
            # 2. Verifica gatilhos de cards na resposta da ELIZA (seja LLM ou fallback)
            assistant_triggers = detect_card_triggers(full_response_or_fallback, triggered_cards)
            for trigger in assistant_triggers:
                await websocket.send_json({"type": "card_trigger", "content": trigger})
            
            # Sincroniza o session_id caso tenha sido gerado um novo pelo backend
            if agent.conversation_id:
                await websocket.send_json({"type": "session_id", "content": agent.conversation_id})
            
            try:
                emotion = await emotion_task
            except Exception:
                emotion = "calm"
            
            await websocket.send_json({"type": "emotion", "content": emotion})
            await websocket.send_json({"type": "end"})
            
    except WebSocketDisconnect:
        logger.info(f"Sessão {agent.conversation_id} desconectada do WebSocket.")
    except Exception as e:
        logger.error(f"Erro no WebSocket para sessão {agent.conversation_id}: {e}")
        try:
            await websocket.send_json({"type": "error", "content": "Desculpe, ocorreu um soluço na nossa conexão. Estou aqui ouvindo você."})
        except Exception:
            pass
    finally:
        # Remove a conexão do mapeamento se for a conexão atual
        if agent.conversation_id and active_connections.get(agent.conversation_id) == websocket:
            active_connections.pop(agent.conversation_id, None)
        await agent.close()

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)