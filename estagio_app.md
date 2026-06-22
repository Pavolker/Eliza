# ELIZA 2026 — Registro de Estágio e Arquitetura

**Data:** 22 de Junho de 2026  
**Versão:** 3.0 — Produção (Hetzner + Netlify + HTTPS)  
**Status:** Online

---

## 1. Visão Geral

ELIZA 2026 é um chatbot terapêutico empático inspirado na ELIZA original (1964) de Joseph Weizenbaum, com persona centrada na abordagem rogeriana de Carl Rogers. O app responde com escuta ativa, sem julgamentos, focado em criar um espaço seguro de diálogo.

---

## 2. Arquitetura de Produção

```
┌─────────────────────────────────────────────────────────┐
│                     INTERNET                              │
│                                                           │
│  https://autoconhecer.netlify.app                         │
│  ┌──────────────────────────────────────┐                │
│  │         Netlify (Frontend)            │                │
│  │  index.html / style.css / app.js      │                │
│  │  Deploy automático via GitHub          │                │
│  └──────────────┬───────────────────────┘                │
│                 │ wss://                                  │
│                 ▼                                         │
│  wss://eliza.mdh-hability.com                             │
│  ┌──────────────────────────────────────┐                │
│  │       Caddy (SSL — Let's Encrypt)     │                │
│  │  Porta 443 → localhost:8001          │                │
│  └──────────────┬───────────────────────┘                │
│                 │                                         │
│  ┌──────────────▼───────────────────────┐                │
│  │     Hetzner CX22 (Falkenstein)        │                │
│  │                                       │                │
│  │  ┌─────────────────────────────┐     │                │
│  │  │  eliza-api (Docker)          │     │                │
│  │  │  FastAPI + Uvicorn           │     │                │
│  │  │  OpenRouter (gpt-4o-mini)    │     │                │
│  │  │  Fallback Regex Local        │     │                │
│  │  └─────────────────────────────┘     │                │
│  │                                       │                │
│  │  ┌─────────────────────────────┐     │                │
│  │  │  eliza-postgres (Docker)     │     │                │
│  │  │  PostgreSQL 16 Alpine        │     │                │
│  │  │  Porta 5432 (interno)        │     │                │
│  │  └─────────────────────────────┘     │                │
│  └──────────────────────────────────────┘                │
│                                                           │
│  DNS: Wix (mdh-hability.com)                              │
│  └── eliza.mdh-hability.com → 178.104.218.193            │
└─────────────────────────────────────────────────────────┘
```

---

## 3. Fluxo de uma Requisição

```
1. Usuário acessa https://autoconhecer.netlify.app
2. Frontend carrega HTML/CSS/JS do Netlify
3. app.js abre WebSocket: wss://eliza.mdh-hability.com/ws/new
4. Caddy (Hetzner) termina TLS, repassa para localhost:8001
5. FastAPI recebe mensagem do usuário
6. OpenRouterAgent chama gpt-4o-mini via OpenRouter API
7. Tokens são streamados de volta via WebSocket
8. Análise de sentimento local classifica a emoção
9. Frontend transita cores do fundo conforme emoção detectada
```

---

## 4. Stack Tecnológica

| Camada | Tecnologia | Detalhe |
|--------|------------|---------|
| Linguagem | Python | 3.11 |
| Backend | FastAPI + Uvicorn | WebSocket async |
| LLM | OpenRouter (OpenAI SDK) | Modelo: `openai/gpt-4o-mini` |
| Database | PostgreSQL 16 | Alpine, Docker |
| Proxy SSL | Caddy 2.11 | Let's Encrypt automático |
| Frontend | HTML5 + CSS3 + JS | Vanilla, sem frameworks |
| Fontes | Inter (texto) + Outfit (títulos) | Google Fonts |
| Infra | Docker Compose | 3 containers (caddy + api + postgres) |
| Deploy Frontend | Netlify | Auto-deploy via GitHub |
| Deploy Backend | Hetzner CX22 | Falkenstein, Alemanha |
| DNS | Wix | Domínio `mdh-hability.com` |
| Repositório | GitHub | `Pavolker/Eliza` |

---

## 5. Custos Mensais

| Recurso | Provedor | Custo |
|---------|----------|-------|
| Servidor (CX22) | Hetzner | R\$ 30 |
| Frontend (static) | Netlify | R\$ 0 |
| Domínio | Wix (mdh-hability.com) | Já pago |
| OpenRouter API | OpenRouter | R\$ 0 (~R\$ 10 com uso real) |
| **Total** | | **~R\$ 30-40/mês** |

---

## 6. Estrutura de Arquivos

### Repositório (GitHub)

```
Pavolker/Eliza/
├── .gitignore
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── agent.py                  # OpenRouterAgent + persona rogeriana
├── main.py                   # FastAPI + WebSocket + fallback regex
├── index.html                # Frontend
├── app.js                    # WebSocket client + UI
├── style.css                 # Temas emocionais + glassmorphism
├── estagio_app.md            # Este documento
├── test_conversational.py
└── relatorio_desenvolvimento.md
```

### Servidor Hetzner (`/opt/eliza/`)

```
/opt/eliza/
├── .env                      # OPENROUTER_API_KEY
├── docker-compose.yml        # postgres + eliza-api
├── Dockerfile                # Python 3.11 slim
├── requirements.txt
├── agent.py
├── main.py
├── index.html / app.js / style.css
```

### SSL

```
/etc/caddy/Caddyfile
── eliza.mdh-hability.com → reverse_proxy localhost:8001

Certificados: /var/lib/caddy/.local/share/caddy/
Renovação: automática (Let's Encrypt ACME)
```

---

## 7. Histórico de Migrações

| Data | Versão | Mudança |
|------|--------|---------|
| 20/06 | 1.0 | Protótipo: Google Antigravity + Gemini |
| 21/06 | 2.0 | Migração: Gemini → OpenRouter (gpt-4o-mini) |
| 22/06 | 2.1 | Docker + PostgreSQL + Deploy Hetzner |
| 22/06 | 3.0 | Caddy SSL + Netlify + domínio próprio → Produção |

### O que mudou na migração Gemini → OpenRouter

| Antes | Depois |
|-------|--------|
| `google-antigravity` SDK | `openai` SDK |
| Gemini Flash | `openai/gpt-4o-mini` (qualquer modelo OpenRouter) |
| SQLite (Antigravity) | PostgreSQL 16 (Docker) |
| `GEMINI_API_KEY` | `OPENROUTER_API_KEY` |
| Persistência automática | Em memória (PostgreSQL pendente) |

---

## 8. Funcionalidades

- [x] Persona rogeriana (Carl Rogers) — escuta ativa, sem julgamentos
- [x] WebSocket com streaming de tokens em tempo real
- [x] Indicador visual "sintonizando..."
- [x] Análise de sentimento local (5 emoções: calma, alegria, tristeza, raiva, ansiedade)
- [x] Temas de cor dinâmicos por emoção (CSS transitions)
- [x] Fallback regex clássico da ELIZA (português)
- [x] Reconexão automática com backoff exponencial
- [x] Reset de conversa (limpa histórico e sessão)
- [x] Orbe animado de respiração (CSS)
- [x] Interface glassmorphism
- [x] Responsivo mobile-first
- [x] HTTPS/WSS com Let's Encrypt (Caddy)
- [x] Deploy automatizado (git push → Netlify)

---

## 9. Pendências e Próximos Passos

### Críticas
- [ ] **Persistência de conversas no PostgreSQL** — schema pronto, aguardando implementação
- [ ] **Auth de usuários** — cadastro/login para múltiplos clientes
- [ ] **Histórico por usuário** — recuperar conversas anteriores

### Funcionais
- [ ] **Cards de sugestão de temas** — página com conteúdo curado
- [ ] **Pagamento recorrente** — Stripe para assinaturas mensais
- [ ] **Troca dinâmica de modelo LLM** — selecionar via UI

### Melhorias
- [ ] **Integração de voz** — Web Speech API (STT/TTS)
- [ ] **Expansão do fallback regex** — 100+ regras do Lisp original
- [ ] **Áudio ambiente dinâmico** — sons adaptativos por emoção
- [ ] **Compactação de contexto** — resumir histórico para evitar estouro de tokens
- [ ] **Correção de abas simultâneas** — `conversationId` compartilhado via localStorage

---

## 10. Notas Técnicas

- O fallback regex garante que o app **nunca fique sem resposta**, mesmo offline ou sem cota de API
- A análise de sentimento usa dicionário de keywords em português — não entende sarcasmo ou sinônimos complexos
- O modelo padrão `gpt-4o-mini` tem bom custo-benefício; alternativas: `anthropic/claude-3.5-haiku`, `google/gemini-flash-1.5`, `openai/gpt-4o`
- Caddy renova certificados SSL automaticamente 30 dias antes da expiração
- O PostgreSQL está rodando mas a aplicação ainda não persiste conversas nele — o agente mantém histórico apenas em RAM

---

## 11. Comandos de Operação

### Hetzner (SSH)

```bash
ssh root@178.104.218.193

# Containers
cd /opt/eliza
docker compose up -d --build   # rebuild e start
docker compose logs -f          # logs em tempo real
docker compose restart          # restart sem rebuild
docker compose down             # parar tudo

# Caddy
systemctl status caddy          # status do SSL
systemctl restart caddy         # forçar renovação de certificado
journalctl -u caddy -f          # logs do Caddy

# PostgreSQL
docker exec eliza-postgres psql -U eliza -d eliza   # console SQL
docker exec eliza-postgres pg_dump -U eliza eliza > backup.sql  # backup

# Firewall
ufw status                      # portas abertas
```

### Deploy (local)

```bash
git add -A
git commit -m "descrição"
git push                        # dispara auto-deploy no Netlify
```

---

## 12. URLs e Acessos

| Recurso | URL |
|---------|-----|
| Frontend (produção) | `https://autoconhecer.netlify.app` |
| Backend (produção) | `wss://eliza.mdh-hability.com` |
| Servidor (SSH) | `root@178.104.218.193` |
| Repositório | `https://github.com/Pavolker/Eliza` |