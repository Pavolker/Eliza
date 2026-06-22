# ELIZA 2026 — Registro de Estágio

**Data:** 22 de Junho de 2026
**Versão:** 2.1 — Deploy Hetzner + Docker + PostgreSQL

---

## 1. Visão Geral

ELIZA 2026 é um chatbot terapêutico empático inspirado na ELIZA original (1964) de Joseph Weizenbaum, com persona centrada na abordagem rogeriana de Carl Rogers. O app responde com escuta ativa, sem julgamentos, focado em criar um espaço seguro de diálogo.

---

## 2. Arquitetura Atual

```
┌──────────────────────────────────────────────┐
│                 Frontend                      │
│  HTML/CSS/JS vanilla + WebSocket              │
│  Glassmorphism + transições emocionais de cor │
└──────────────────┬───────────────────────────┘
                   │ ws://
┌──────────────────▼───────────────────────────┐
│            Backend (FastAPI)                   │
│                                                │
│  ┌──────────────────────┐                     │
│  │   OpenRouter Agent    │  API primária       │
│  │   (gpt-4o-mini)      │                     │
│  └──────────────────────┘                     │
│              │ (se falhar)                     │
│  ┌───────────▼──────────┐                     │
│  │  Fallback Regex Local │  Resposta garantida │
│  │  (regras ELIZA pt-BR) │                     │
│  └──────────────────────┘                     │
│                                                │
│  ┌──────────────────────┐                     │
│  │  Análise de Sentimento│  Zero consumo API   │
│  │  (keywords local)     │                     │
│  └──────────────────────┘                     │
└──────────────────────────────────────────────┘
```

---

## 3. Stack Tecnológica

| Camada | Tecnologia | Versão |
|--------|------------|--------|
| Linguagem | Python | 3.11+ |
| Servidor | FastAPI + Uvicorn | — |
| LLM | OpenRouter (OpenAI SDK) | `openai` |
| Modelo padrão | `openai/gpt-4o-mini` | — |
| Streaming | WebSocket token-a-token assíncrono | — |
| Frontend | HTML5 + CSS3 + JS (vanilla) | — |
| Fontes | Inter (texto), Outfit (títulos) | Google Fonts |
| Persistência | localStorage (session_id) | Navegador |

---

## 4. Migração Gemini → OpenRouter

### O que mudou (21/06/2026)

| Antes | Depois |
|-------|--------|
| `google-antigravity` SDK | `openai` SDK |
| Gemini Flash (Antigravity wrapper) | Qualquer modelo via OpenRouter |
| `Agent(config)` context manager | `OpenRouterAgent()` async generator |
| SQLite persistido pelo Antigravity | Histórico em memória (via `self.messages`) |
| `GEMINI_API_KEY` | `OPENROUTER_API_KEY` |
| Conversas em `conversations/*.db` | Sem persistência de disco (por enquanto) |

### Arquivos modificados
- `requirements.txt` — trocou `google-antigravity` por `openai`
- `agent.py` — reescrito com `AsyncOpenAI`, mantendo mesma persona e interface `chat()`
- `main.py` — adaptado para `OpenRouterAgent`, removendo dependência do context manager
- `.env` — `OPENROUTER_API_KEY`

---

## 5. Funcionalidades Implementadas

- [x] Persona rogeriana via `CustomSystemInstructions`
- [x] Chat em tempo real via WebSocket com streaming de tokens
- [x] Indicador visual de "sintonizando..." (digitando)
- [x] Análise de sentimento local por keywords (5 emoções)
- [x] Transição suave de cores do fundo baseada na emoção
- [x] Fallback regex clássico da ELIZA (português)
- [x] Reconexão automática com backoff exponencial
- [x] Reset de conversa com limpeza do histórico
- [x] Orbe animado de respiração (CSS)
- [x] Interface glassmorphism premium
- [x] Responsivo (mobile-first)

---

## 6. Estrutura de Arquivos

```
ELIZA/
├── .env                  # OPENROUTER_API_KEY
├── .venv/                # Virtualenv (sem pip)
├── agent.py              # OpenRouterAgent + persona rogeriana
├── main.py               # FastAPI + WebSocket + fallback
├── index.html            # Frontend HTML
├── style.css             # Temas emocionais + glassmorphism
├── app.js                # WebSocket client + UI logic
├── requirements.txt      # openai, fastapi, uvicorn, python-dotenv
├── conversations/        # Diretório de sessões (legado)
├── paip-lisp/            # Referência: ELIZA original em Lisp (Norvig)
├── test_conversational.py
└── temp_save_dir/
```

---

## 7. Como Rodar

```bash
# 1. Instalar dependências
pip install -r requirements.txt

# 2. Configurar chave OpenRouter
# Editar .env: OPENROUTER_API_KEY=sk-or-v1-...

# 3. Iniciar
python3 -m uvicorn main:app --host 0.0.0.0 --port 8001

# 4. Acessar
open http://localhost:8001
```

---

## 8. Pendências e Próximos Passos

- [ ] **Persistência de conversas** — O Antigravity salvava em SQLite automaticamente; com OpenRouter é necessário implementar manualmente
- [ ] **Troca dinâmica de modelo** — Permitir selecionar modelo OpenRouter via UI
- [ ] **Histórico por sessão** — Recuperar conversas anteriores ao reconectar
- [ ] **Integração de voz** — Web Speech API (STT/TTS)
- [ ] **Expansão do fallback** — 100+ regras do Lisp original (PAIP)
- [ ] **Áudio ambiente dinâmico** — Sons adaptativos por emoção
- [ ] **Compactação de contexto** — Resumir histórico para evitar estouro de tokens

---

## 9. Notas Técnicas

- O fallback regex garante que o app **nunca fique sem resposta**, mesmo offline ou sem cota
- A análise de sentimento usa dicionário de keywords em português — não entende sarcasmo
- Abas simultâneas compartilham `conversationId` via localStorage — pode causar conflitos
- O modelo padrão `gpt-4o-mini` tem bom custo-benefício; para qualidade superior usar `anthropic/claude-3.5-sonnet` ou `openai/gpt-4o`

---

## 10. Deploy — Hetzner CX22 (22/06/2026)

| Recurso | Detalhe |
|---------|---------|
| Servidor | CX22 — 2 vCPU, 4GB RAM, 80GB SSD |
| IP | **178.104.218.193** |
| URL | **http://178.104.218.193:8001** |
| SO | Ubuntu 24.04 |
| Docker | 29.1.3 + Compose v2 |
| PostgreSQL | 16 Alpine (container `eliza-postgres`) |
| ELIZA API | Python 3.11 Slim (container `eliza-api`) |
| Firewall | ufw: portas 22 e 8001 abertas |
| SSH | Chave ed25519 adicionada |

### Estrutura no servidor

```
/opt/eliza/
├── .env                  # OPENROUTER_API_KEY
├── docker-compose.yml    # postgres + eliza
├── Dockerfile
├── requirements.txt
├── agent.py
├── main.py
├── index.html / app.js / style.css
```

### Comandos úteis

```bash
# SSH
ssh root@178.104.218.193

# Gerenciar containers
cd /opt/eliza
docker compose up -d --build   # rebuild e start
docker compose logs -f          # logs em tempo real
docker compose restart          # restart sem rebuild
docker compose down             # parar tudo

# Backup PostgreSQL
docker exec eliza-postgres pg_dump -U eliza eliza > backup.sql
```