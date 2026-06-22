import asyncio
import os
import sys
from agent import get_agent_config, ROGERIAN_PERSONA
from google.antigravity import Agent

async def run_test():
    print("==================================================")
    print("Iniciando testes de conversação da ELIZA 2026")
    print("==================================================")
    
    # 1. Verifica a chave de API
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("[AVISO] GEMINI_API_KEY não encontrada nas variáveis de ambiente.")
        print("Certifique-se de definir a chave no seu ambiente ou em um arquivo .env.")
        print("Tentando continuar (pode falhar se o SDK não encontrar credenciais)...")
    else:
        print("[OK] GEMINI_API_KEY detectada no ambiente.")

    # 2. Testa a inicialização e diálogo do agente
    conversation_id = "test_session_99"
    config = get_agent_config(conversation_id=conversation_id, save_dir="test_conversations")
    
    test_prompts = [
        "Estou muito cansado e triste com o meu trabalho hoje.",
        "Minha mãe sempre me disse que eu deveria ser mais forte.",
        "Você é um computador ou uma pessoa real?"
    ]
    
    try:
        async with Agent(config) as agent:
            print("\nSessão do agente iniciada com sucesso.")
            
            for i, prompt in enumerate(test_prompts, 1):
                print(f"\n[Usuário {i}]: {prompt}")
                print("[ELIZA 2026 (Pensamentos)]: ", end="", flush=True)
                
                # Realiza o chat e exibe pensamentos
                response = await agent.chat(prompt)
                
                # Exibe pensamentos se houver
                async for thought in response.thoughts:
                    print(thought, end="", flush=True)
                print()
                
                # Exibe resposta final
                print("[ELIZA 2026 (Resposta)]: ", end="")
                async for token in response:
                    print(token, end="", flush=True)
                print()
                
        print("\n==================================================")
        print("Testes concluídos com sucesso!")
        print("==================================================")
    except Exception as e:
        print(f"\n[ERRO] Ocorreu uma falha durante o teste do agente: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(run_test())
