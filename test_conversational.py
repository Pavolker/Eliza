import asyncio
import os
import sys
from dotenv import load_dotenv
import asyncpg
from agent import OpenRouterAgent

load_dotenv()

async def test_agent():
    print("==================================================")
    print("Iniciando testes de conversação da ELIZA 2026 (OpenRouter)")
    print("==================================================")
    
    # 1. Verifica chave de API do OpenRouter
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("[ERRO] OPENROUTER_API_KEY não encontrada no ambiente ou .env.")
        sys.exit(1)
    else:
        print("[OK] OPENROUTER_API_KEY detectada.")
        
    # 2. Configura banco de dados (se disponível)
    database_url = os.getenv("DATABASE_URL") or "postgresql://eliza:Eliza2026DB!@localhost:5432/eliza"
    pool = None
    try:
        connection_url = database_url.replace("postgresql+asyncpg://", "postgresql://")
        print(f"Tentando conectar ao banco de dados para testes: {connection_url}")
        pool = await asyncpg.create_pool(connection_url, timeout=3.0)
        
        # Cria a tabela de teste
        async with pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id SERIAL PRIMARY KEY,
                    conversation_id VARCHAR(100) NOT NULL,
                    role VARCHAR(20) NOT NULL,
                    content TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
        print("[OK] Conexão com o banco de dados realizada com sucesso.")
    except Exception as e:
        print(f"[AVISO] Não foi possível conectar ao banco de dados ({e}). Executando testes sem banco.")
        
    # 3. Inicializa o agente
    session_id = "test_or_session_123"
    print(f"\nInicializando OpenRouterAgent com session_id: {session_id}")
    agent = OpenRouterAgent(conversation_id=session_id, pool=pool)
    
    # Carrega histórico
    await agent.load_history()
    print(f"Histórico inicial carregado: {len(agent.messages)} mensagens (incluindo persona).")
    
    # 4. Envia prompts de teste
    test_prompts = [
        "Estou muito cansado hoje. Sinto que meu trabalho está me esgotando completamente.",
        "Sim, tenho muitos conflitos com meu chefe porque ele cobra metas absurdas que vão contra o que eu acredito.",
        "Gostei dessa ideia de equilibrar. Como posso colocar isso em prática no meu dia a dia?",
        "Fez sentido. Acho que posso começar definindo um limite de horário para responder e-mails e respirar um pouco antes de responder a cobranças."
    ]
    
    try:
        for i, prompt in enumerate(test_prompts, 1):
            print(f"\n[Usuário {i}]: {prompt}")
            print("[ELIZA 2026 (Resposta streaming)]: ", end="", flush=True)
            
            # Executa chat com streaming
            response_tokens = []
            async for token in agent.chat(prompt):
                print(token, end="", flush=True)
                response_tokens.append(token)
            print()
            
        print("\n[OK] Diálogo de teste concluído com sucesso.")
        
        # 5. Verifica persistência no banco (se pool estiver conectado)
        if pool:
            print("\nVerificando mensagens salvas no banco de dados...")
            async with pool.acquire() as conn:
                rows = await conn.fetch(
                    "SELECT role, content FROM messages WHERE conversation_id = $1 ORDER BY id ASC",
                    session_id
                )
                print(f"Total de mensagens no banco para {session_id}: {len(rows)}")
                for row in rows:
                    print(f" - [{row['role'].upper()}]: {row['content']}")
                
                # Opcional: Limpar as mensagens de teste
                await conn.execute("DELETE FROM messages WHERE conversation_id = $1", session_id)
                print("Mensagens de teste limpas do banco.")
                
        else:
            print("\n[AVISO] Pulando verificação do banco de dados (banco offline).")
            print("Mensagens em memória do agente:")
            for msg in agent.messages[1:]:  # Ignora a persona rogeriana
                print(f" - [{msg['role'].upper()}]: {msg['content']}")
                
        print("\n==================================================")
        print("Testes concluídos com sucesso!")
        print("==================================================")
        
    except Exception as e:
        print(f"\n[ERRO] Ocorreu uma falha durante os testes do agente: {e}")
        if pool:
            await pool.close()
        sys.exit(1)
    finally:
        if pool:
            await pool.close()

if __name__ == "__main__":
    asyncio.run(test_agent())
