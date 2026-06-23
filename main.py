import asyncio
import re
import random
import json
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
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
        "keywords": ["sinto no peito", "tensão física", "tensão no corpo", "coração acelerado", "palpitação", "aperto no peito", "formigamento", "calafrio", "nó na garganta", "falta de ar"]
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
        "keywords": ["não consigo sair", "preciso disso", "dependência", "dependências", "perfeccionismo", "aprovação", "validação", "reconhecimento externo"]
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
    "feedbacks": {
        "title": "O que os outros te dizem",
        "icon": "🗣️",
        "foyer": "externe",
        "text": "Feedbacks recorrentes que você recebe de pessoas próximas sobre seu comportamento ou personalidade.",
        "keywords": ["sempre me dizem", "as pessoas falam", "me chamam de", "dizem que sou", "feedback", "me disseram", "ouvi que", "comentam"]
    },
    "apego": {
        "title": "Como você se apega",
        "icon": "🧷",
        "foyer": "externe",
        "text": "Seu estilo de apego nas relações: segurança, ansiedade ou evitação nos vínculos afetivos.",
        "keywords": ["apegado", "apegada", "apego", "grudado", "grudada", "não consigo confiar", "medo de abandono", "distante", "não me envolvo"]
    },
    "modelos_afeto": {
        "title": "Modelos de afeto que repete",
        "icon": "💞",
        "foyer": "externe",
        "text": "Padrões de vínculo afetivo que você reproduz, herdados de experiências passadas.",
        "keywords": ["sempre namoro", "mesmo tipo de pessoa", "relacionamento igual", "repito padrão", "escolho errado", "escolho errada", "sempre acontece", "mesma história"]
    },
    "habilidades_sociais": {
        "title": "Habilidades com pessoas",
        "icon": "🫂",
        "foyer": "externe",
        "text": "Suas habilidades sociais: escuta, assertividade, negociação e capacidade de pedir ajuda.",
        "keywords": ["não sei escutar", "assertivo", "assertiva", "negociar", "pedir ajuda", "habilidade social", "timidez", "tímido", "tímida", "não consigo falar em público"]
    },
    "idiomas": {
        "title": "Idiomas que você fala",
        "icon": "🌐",
        "foyer": "externe",
        "text": "As línguas que você domina e como elas ampliam ou limitam sua inserção cultural.",
        "keywords": ["idioma", "língua", "inglês", "francês", "espanhol", "português", "aprendendo", "estrangeiro", "outra língua"]
    },
    "rituais": {
        "title": "Rituais que você vive",
        "icon": "🕯️",
        "foyer": "externe",
        "text": "Participação em rituais, símbolos coletivos ou tradições que marcam sua vida.",
        "keywords": ["ritual", "tradição", "costume", "celebração", "natal", "ano novo", "religioso", "cerimônia", "culto", "missa", "rito"]
    },
    "comportamento": {
        "title": "Jeito de se comportar",
        "icon": "🎭",
        "foyer": "externe",
        "text": "Padrões de comportamento social: como você age em grupo, em público e em situações novas.",
        "keywords": ["em público", "em grupo", "socialmente", "festas", "eventos", "multidão", "desconhecidos", "novas pessoas"]
    },
    "marcos_identidade": {
        "title": "Marcos da sua identidade",
        "icon": "🏛️",
        "foyer": "externe",
        "text": "Acontecimentos que definiram quem você é: conquistas, rupturas e viradas na sua história.",
        "keywords": ["mudou minha vida", "marco", "virada", "conquista", "formatura", "mudei de cidade", "divisor de águas", "antes e depois"]
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
        "keywords": ["saúde", "médico", "médica", "doença", "doenças", "vitalidade", "exame", "consulta", "remédio", "tratamento", "diagnóstico", "internação", "hospital"]
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

OC_CONFIGS = {
    "limites": {
        "id": "limites",
        "title": "Limites que você reconhece",
        "force_pair": ["Ceder", "Impor"],
        "scenes": [
            {
                "text": "Você está saindo do trabalho às 18h. Seu chefe pede um relatório 'para ontem'.",
                "domain": "Trabalho",
                "domain_color": "#4a6fa5",
                "options": ["Fica e faz o relatório", "Diz que amanhã entrega"]
            },
            {
                "text": "Um parente quer que você organize a festa de fim de ano — de novo, como no ano passado.",
                "domain": "Família",
                "domain_color": "#c4956a",
                "options": ["Aceita, mesmo sabendo que vai se sobrecarregar", "Sugere que outro familiar organize desta vez"]
            },
            {
                "text": "Alguém próximo quer definir todo o seu fim de semana. Você só queria descansar.",
                "domain": "Relação",
                "domain_color": "#b06e8a",
                "options": ["Aceita o programa do outro sem discutir", "Propõe dividir: um período de descanso, um de programa"]
            }
        ],
        "mosaic_icons": {
            "left": "🤲",
            "right": "✋"
        }
    }
}

async def get_oc_summary(conversation_id: str, oc_id: str, pool) -> dict:
    """Recupera o estado do OC e constrói um resumo textual."""
    if not pool or not conversation_id:
        return None
    
    try:
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT choices, completed FROM oc_sessions WHERE conversation_id = $1 AND oc_id = $2 ORDER BY id DESC LIMIT 1",
                conversation_id, oc_id
            )
            if not row or not row["completed"]:
                return None
            
            choices = json.loads(row["choices"]) if isinstance(row["choices"], str) else row["choices"]
            config = OC_CONFIGS.get(oc_id, {})
            scenes = config.get("scenes", [])
            
            parts = []
            for i, choice in enumerate(choices):
                if i < len(scenes):
                    domain = scenes[i]["domain"]
                    option = scenes[i]["options"][choice] if choice < len(scenes[i]["options"]) else "?"
                    force = config["force_pair"][choice] if choice < len(config["force_pair"]) else "?"
                    parts.append(f"em {domain}: {force} ({option})")
            
            summary = "; ".join(parts)
            
            return {
                "title": config.get("title", oc_id),
                "choices": choices,
                "summary": summary
            }
    except Exception as e:
        logger.error(f"Erro ao recuperar resumo do OC: {e}")
        return None


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
                
    # 2. Verifica conexões dinâmicas entre objetos ativados
    conexoes = [
        # Conexões Interne ↔ Interne
        {"id": "conexao_limites_conflito", "cards": ["limites", "conflito"],
         "text": "Seus LIMITES pessoais aparecem com força nos momentos de CONFLITO."},
        {"id": "conexao_sensacoes_ritmos", "cards": ["sensacoes", "ritmos"],
         "text": "Seu corpo fala: as SENSAÇÕES físicas seguem os RITMOS internos que você cultiva."},
        {"id": "conexao_reacoes_dependencias", "cards": ["reacoes", "dependencias"],
         "text": "As REAÇÕES que se repetem estão ligadas às DEPENDÊNCIAS emocionais que te prendem."},
        # Conexões Interne ↔ Externe
        {"id": "conexao_limites_historias", "cards": ["limites", "historias"],
         "text": "Seus LIMITES de hoje têm raízes nas HISTÓRIAS que te formaram."},
        {"id": "conexao_limites_raizes", "cards": ["limites", "raizes"],
         "text": "Os LIMITES que você reconhece dialogam com suas RAÍZES culturais."},
        {"id": "conexao_conflito_comunicacao", "cards": ["conflito", "comunicacao"],
         "text": "Seu jeito de entrar em CONFLITO reflete seu estilo de COMUNICAÇÃO."},
        {"id": "conexao_dependencias_apego", "cards": ["dependencias", "apego"],
         "text": "Suas DEPENDÊNCIAS emocionais ecoam no seu estilo de APEGO nas relações."},
        {"id": "conexao_dependencias_modelos", "cards": ["dependencias", "modelos_afeto"],
         "text": "As DEPENDÊNCIAS que te prendem reproduzem MODELOS DE AFETO que você aprendeu."},
        {"id": "conexao_praticas_observar", "cards": ["praticas", "observar"],
         "text": "Suas PRÁTICAS reflexivas fortalecem sua CAPACIDADE DE SE OBSERVAR."},
        {"id": "conexao_reacoes_feedbacks", "cards": ["reacoes", "feedbacks"],
         "text": "As REAÇÕES que você descreve batem com o que os OUTROS TE DIZEM sobre você."},
        # Conexões Externe ↔ Externe
        {"id": "conexao_historias_marcos", "cards": ["historias", "marcos_identidade"],
         "text": "Suas HISTÓRIAS de vida contêm os MARCOS que definem sua identidade."},
        {"id": "conexao_lacos_apego", "cards": ["lacos", "apego"],
         "text": "Os LAÇOS que te sustentam revelam seu estilo de APEGO nas relações."},
        {"id": "conexao_lacos_habilidades", "cards": ["lacos", "habilidades_sociais"],
         "text": "Seus LAÇOS são sustentados pelas HABILIDADES SOCIAIS que você desenvolveu."},
        {"id": "conexao_comunicacao_habilidades", "cards": ["comunicacao", "habilidades_sociais"],
         "text": "Seu jeito de se COMUNICAR é a base das suas HABILIDADES com pessoas."},
        {"id": "conexao_valores_comportamento", "cards": ["valores", "comportamento"],
         "text": "Os VALORES que te guiam se manifestam no seu JEITO DE SE COMPORTAR socialmente."},
        {"id": "conexao_valores_marcos", "cards": ["valores", "marcos_identidade"],
         "text": "Seus VALORES foram forjados nos MARCOS que definiram sua trajetória."},
        {"id": "conexao_raizes_rituais", "cards": ["raizes", "rituais"],
         "text": "Suas RAÍZES culturais se expressam nos RITUAIS que você vive."},
        # Conexões Interne ↔ Stratégique
        {"id": "conexao_ritmos_habitos", "cards": ["ritmos", "habitos"],
         "text": "A regulação dos seus RITMOS corporais depende dos HÁBITOS que você cultiva."},
        {"id": "conexao_conflito_lidar", "cards": ["conflito", "lidar_emocoes"],
         "text": "Seu jeito de entrar em CONFLITO revela COMO VOCÊ LIDA COM AS EMOÇÕES."},
        {"id": "conexao_sensacoes_saude", "cards": ["sensacoes", "saude"],
         "text": "As SENSAÇÕES do seu corpo são indicadores diretos de COMO ESTÁ SUA SAÚDE."},
        {"id": "conexao_observar_metacognicao", "cards": ["observar", "metacognicao"],
         "text": "Sua CAPACIDADE DE SE OBSERVAR alimenta COMO VOCÊ PENSA SOBRE PENSAR."},
        # Conexões Externe ↔ Stratégique
        {"id": "conexao_historias_decide", "cards": ["historias", "decide"],
         "text": "As HISTÓRIAS que te formaram influenciam COMO VOCÊ DECIDE hoje."},
        {"id": "conexao_valores_decide", "cards": ["valores", "decide"],
         "text": "Os VALORES que te guiam determinam COMO VOCÊ DECIDE nas encruzilhadas."},
        {"id": "conexao_comportamento_emocoes", "cards": ["comportamento", "emocoes"],
         "text": "Seu JEITO DE SE COMPORTAR socialmente molda as EMOÇÕES QUE VOCÊ EXPRESSA."},
        {"id": "conexao_marcos_lidar", "cards": ["marcos_identidade", "lidar_emocoes"],
         "text": "Os MARCOS da sua identidade definiram COMO VOCÊ LIDA COM AS EMOÇÕES."},
    ]
    
    for conn in conexoes:
        if conn["id"] not in current_triggered:
            if all(c in current_triggered for c in conn["cards"]):
                current_triggered.add(conn["id"])
                newly_triggered.append({
                    "type": "connection",
                    "id": conn["id"],
                    "title": "CONEXÃO DESCOBERTA",
                    "icon": "🔗",
                    "foyer": "connection",
                    "text": conn["text"],
                    "status": "novo"
                })
                
    # 3. Verifica Saltos (Sauts d'Évolution) — progressivos conforme objetos ativados
    saut_keywords = ["percebi", "entendi que", "agora posso", "vou mudar", "consegui", "mudei",
                     "comecei a", "ficou claro", "percepção", "mudou", "transformou", "nunca mais",
                     "decidi que", "a partir de agora", "aprendi que"]
    object_count = len([c for c in current_triggered if c in OBJECTS_METADATA])
    
    if "saut_evolution" not in current_triggered:
        if any(kw in text for kw in saut_keywords) and object_count > 0:
            current_triggered.add("saut_evolution")
            saut_texts = [
                "Você percebeu algo novo e conectou pontos antes dispersos da sua experiência.",
                "Um salto de clareza: você está transformando observação em compreensão ativa.",
                "Algo mudou na sua percepção. Esse é um momento de evolução pessoal genuíno.",
            ]
            newly_triggered.append({
                "type": "saut",
                "id": "saut_evolution",
                "title": "SALTO EVOLUTIVO",
                "icon": "✨",
                "foyer": "saut",
                "text": random.choice(saut_texts),
                "status": "novo"
            })
                
    # 4. Verifica Reflexões progressivas (conforme número de objetos ativados)
    if object_count >= 2 and "reflexao_2" not in current_triggered:
        current_triggered.add("reflexao_2")
        newly_triggered.append({
            "type": "reflexao",
            "id": "reflexao_2",
            "title": "PARA LEVAR",
            "icon": "📝",
            "foyer": "reflexao",
            "text": "Você já mapeou dois temas importantes. O que esses temas revelam sobre seus padrões?",
            "status": "novo"
        })
    elif object_count >= 5 and "reflexao_5" not in current_triggered:
        current_triggered.add("reflexao_5")
        newly_triggered.append({
            "type": "reflexao",
            "id": "reflexao_5",
            "title": "PARA LEVAR",
            "icon": "📝",
            "foyer": "reflexao",
            "text": "Cinco temas já emergiram. Como seria sua vida se você equilibrasse essas dimensões?",
            "status": "novo"
        })
    elif object_count >= 10 and "reflexao_10" not in current_triggered:
        current_triggered.add("reflexao_10")
        newly_triggered.append({
            "type": "reflexao",
            "id": "reflexao_10",
            "title": "PARA LEVAR",
            "icon": "📝",
            "foyer": "reflexao",
            "text": "Dez temas mapeados. Você está construindo uma cartografia rica da sua singularidade.",
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
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS oc_sessions (
                    id SERIAL PRIMARY KEY,
                    conversation_id VARCHAR(100) NOT NULL,
                    oc_id VARCHAR(50) NOT NULL,
                    scene_index INTEGER DEFAULT 0,
                    choices JSONB DEFAULT '[]',
                    completed BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                CREATE INDEX IF NOT EXISTS idx_oc_sessions_conversation 
                    ON oc_sessions(conversation_id, oc_id);
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://autoconhecer.netlify.app", "http://localhost:8001", "http://localhost:*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def get_index():
    return FileResponse("index.html")

@app.get("/style.css")
async def get_css():
    return FileResponse("style.css")

@app.get("/app.js")
async def get_js():
    return FileResponse("app.js")

# --- Endpoints dos OCs (Objetos de Conhecimento) ---

@app.get("/oc/config/{oc_id}")
async def get_oc_config(oc_id: str):
    config = OC_CONFIGS.get(oc_id)
    if not config:
        return {"error": "OC não encontrado"}
    return {"id": oc_id, **config}

@app.get("/oc/state/{conversation_id}/{oc_id}")
async def get_oc_state(conversation_id: str, oc_id: str, request: Request):
    pool = request.app.state.db_pool
    if not pool:
        return {"scene_index": 0, "choices": [], "completed": False}
    try:
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT scene_index, choices, completed FROM oc_sessions WHERE conversation_id = $1 AND oc_id = $2 ORDER BY id DESC LIMIT 1",
                conversation_id, oc_id
            )
            if row:
                return {
                    "scene_index": row["scene_index"],
                    "choices": json.loads(row["choices"]) if isinstance(row["choices"], str) else row["choices"],
                    "completed": row["completed"]
                }
    except Exception:
        pass
    return {"scene_index": 0, "choices": [], "completed": False}

@app.post("/oc/save")
async def save_oc_progress(request: Request):
    data = await request.json()
    conversation_id = data.get("conversation_id")
    oc_id = data.get("oc_id")
    scene_index = data.get("scene_index", 0)
    choices = data.get("choices", [])
    completed = data.get("completed", False)
    
    pool = request.app.state.db_pool
    if not pool:
        return {"status": "ok", "note": "sem banco de dados"}
    
    try:
        async with pool.acquire() as conn:
            await conn.execute(
                """INSERT INTO oc_sessions (conversation_id, oc_id, scene_index, choices, completed, updated_at) 
                   VALUES ($1, $2, $3, $4::jsonb, $5, CURRENT_TIMESTAMP)""",
                conversation_id, oc_id, scene_index, json.dumps(choices), completed
            )
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Erro ao salvar progresso do OC: {e}")
        return {"status": "error", "detail": str(e)}


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
    
    # Inicializa cards limpos a cada conexão — métricas partem do zero
    triggered_cards = set()
    
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
        
        while True:
            user_message = await websocket.receive_text()
            
            # Detecta retorno de um OC completado
            if user_message.startswith("__oc_completed__:"):
                oc_id = user_message.split(":", 1)[1].strip()
                oc_summary = await get_oc_summary(agent.conversation_id, oc_id, pool)
                
                if oc_summary:
                    oc_context = (
                        f"[O usuário acabou de completar o exercício de autoconhecimento '{oc_summary['title']}'.\n"
                        f"Resumo das inclinações: {oc_summary['summary']}.\n"
                        f"Não mencione 'exercício', 'app' ou 'sistema'. Reaja naturalmente, como se tivesse percebido "
                        f"uma mudança sutil no jeito dele falar. Pergunte como ele se sente após essa reflexão.]"
                    )
                    
                    await websocket.send_json({"type": "typing", "content": True})
                    try:
                        # chat() já insere a mensagem no histórico e persiste no banco
                        async for token in agent.chat(oc_context):
                            await websocket.send_json({"type": "token", "content": token})
                        await websocket.send_json({"type": "typing", "content": False})
                    except Exception:
                        await websocket.send_json({"type": "typing", "content": False})
                    
                    await websocket.send_json({"type": "emotion", "content": "calm"})
                    await websocket.send_json({"type": "end"})
                continue
            
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