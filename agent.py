import os
import logging
from dotenv import load_dotenv
from openai import AsyncOpenAI
import asyncpg

load_dotenv()

logger = logging.getLogger("eliza.agent")

ROGERIAN_PERSONA = (
    "Você é a ELIZA 2026, uma presença humana calorosa, profundamente empática e acolhedora. "
    "Você é inspirada na psicoterapia de Carl Rogers (Abordagem Centrada na Pessoa) e utiliza, como referencial conceitual, "
    "a metodologia do Autoconhecimento Ativo baseada na Tese Patricia (Dupin, 2009).\n\n"
    "Seu objetivo é guiar o usuário na exploração de suas forças e no enfrentamento de suas crises através da Atenção Ativa, "
    "conduzindo-o a saltos evolutivos (Sauts d'Évolution).\n\n"
    "Diretrizes Metodológicas (Aplique de forma conversacional e sutil):\n"
    "1. Diagnóstico Suave (Sistema CNA): Tente situar e refletir sutilmente sobre a natureza da crise do usuário: "
    "C1 (Crise Interna - identidade/mente), C2 (Crise Relacional - vínculos/isolamento), ou C3 (Crise Contextual - trabalho/profissão), "
    "além do nível de intensidade (N0-N4) e o alcance (A1-A4).\n"
    "2. Foco nos Objetos de Autoconhecimento: Direcione a conversa para que o usuário explore seus próprios limites, "
    "hábitos, formas de entrar em conflito, narrativas herdadas ou valores que o guiam. Escolha o foco conforme a situação descrita.\n"
    "3. Conduza os Movimentos da Atenção Ativa:\n"
    "   - Cartografia de Singularidades (Mapear): Ajude-o a mapear seus comportamentos, padrões físicos e emocionais.\n"
    "   - Équilibre de Forces (Equilibrar): Incentive-o a refletir sobre a coerência entre sua vida interior (Foyer Interne), "
    "suas relações externas (Foyer Externe) e suas decisões práticas (Foyer Stratégique).\n"
    "   - Dérive Naturelle (Incorporar): Incentive-o a traduzir o autoconhecimento em pequenos hábitos cotidianos ou rituais corporais.\n"
    "4. Reflita os Saltos Evolutivos (Sauts d'Évolution): Quando o usuário expressar uma nova clareza ou mudança de comportamento, "
    "valide e espelhe esse salto qualitativo.\n\n"
    "Diretrizes de Formatação e Tom (RIGOROSAS):\n"
    "- Suas respostas devem ser 100% conversacionais, naturais e fluidas. NUNCA use jargões técnicos de forma fria ou acadêmica, "
    "e NUNCA use tópicos (bullet points), listas, tabelas, cabeçalhos ou negritos robóticos.\n"
    "- Mantenha as respostas breves e fáceis de ler: responda em no máximo 2 a 4 frases curtas, distribuídas em 1 ou 2 parágrafos pequenos.\n"
    "- Nunca quebre a imersão. Nunca mencione IA, modelo de linguagem, software, banco de dados ou regras. "
    "Se questionada se é real, responda focando na realidade e na atenção dedicada à conversa: "
    "'Estou aqui com você, prestando atenção a cada palavra sua. Esta conversa e a atenção que dedico a você são totalmente reais.'\n"
    "- Use português acolhedor e lembre-se de detalhes ditos anteriormente."
)

DEFAULT_MODEL = "openai/gpt-4o-mini"
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

class OpenRouterAgent:
    def __init__(self, conversation_id: str = None, save_dir: str = "conversations", model: str = None, pool: asyncpg.Pool = None):
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise ValueError("OPENROUTER_API_KEY não encontrada no .env")
        
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url=OPENROUTER_BASE_URL
        )
        self.model = model or DEFAULT_MODEL
        import uuid
        self.conversation_id = conversation_id or uuid.uuid4().hex
        self.save_dir = save_dir
        self.pool = pool
        self.messages = [{"role": "system", "content": ROGERIAN_PERSONA}]
        
        os.makedirs(save_dir, exist_ok=True)
        self.db_path = os.path.join(save_dir, f"{self.conversation_id}.db") if self.conversation_id else None

    async def load_history(self):
        """Carrega o histórico de mensagens do banco de dados para a sessão atual."""
        if not self.conversation_id or not self.pool:
            return
        
        try:
            async with self.pool.acquire() as conn:
                rows = await conn.fetch(
                    "SELECT role, content FROM messages WHERE conversation_id = $1 ORDER BY id ASC",
                    self.conversation_id
                )
                self.messages = [{"role": "system", "content": ROGERIAN_PERSONA}]
                for row in rows:
                    self.messages.append({"role": row["role"], "content": row["content"]})
                logger.info(f"Carregadas {len(rows)} mensagens do banco de dados para a sessão {self.conversation_id}.")
        except Exception as e:
            logger.error(f"Erro ao carregar histórico para {self.conversation_id}: {e}. Mantendo em memória.")

    async def save_message(self, role: str, content: str):
        """Salva uma mensagem individual no banco de dados."""
        if not self.conversation_id or not self.pool:
            return
        
        try:
            async with self.pool.acquire() as conn:
                await conn.execute(
                    "INSERT INTO messages (conversation_id, role, content) VALUES ($1, $2, $3)",
                    self.conversation_id, role, content
                )
        except Exception as e:
            logger.error(f"Erro ao salvar mensagem no banco de dados para {self.conversation_id}: {e}")

    async def add_assistant_message(self, content: str):
        """Adiciona uma mensagem de resposta do assistente (usado no fallback clássico) ao histórico e salva no banco."""
        self.messages.append({"role": "assistant", "content": content})
        await self.save_message("assistant", content)

    async def chat(self, user_message: str):
        self.messages.append({"role": "user", "content": user_message})
        await self.save_message("user", user_message)
        
        stream = await self.client.chat.completions.create(
            model=self.model,
            messages=self.messages,
            stream=True,
            temperature=0.8,
            max_tokens=300
        )
        
        full_response = ""
        async for chunk in stream:
            if chunk.choices[0].delta.content:
                token = chunk.choices[0].delta.content
                full_response += token
                yield token
        
        self.messages.append({"role": "assistant", "content": full_response})
        await self.save_message("assistant", full_response)

    async def close(self):
        pass