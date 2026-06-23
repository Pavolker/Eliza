# ELIZA 2026 — Registro de Estágio e Arquitetura

**Data:** 23 de Junho de 2026
**Versão:** 3.2 — PoC OC App (Objeto de Conhecimento) + ELIZA reativa
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
├── Dockerfile                # Python 3.11 slim + libpq-dev
├── requirements.txt          # openai, fastapi, uvicorn, asyncpg
├── agent.py                  # OpenRouterAgent + persona expandida + pool DB
├── main.py                   # FastAPI + cards + foyers + PostgreSQL lifespan
├── index.html                # Split-screen (chat + cards)
├── app.js                    # Cards dinâmicos + foyer progress + filtros
├── style.css                 # Layout split-screen + temas
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
| 23/06 | 3.1 | Split-screen, 27 cards autoconhecimento, PostgreSQL persistência, persona expandida |
| 23/06 | 3.2 | PoC OC App: modal 3 cenas, mosaico, ELIZA reativa, card "Explorado" |

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

- [x] Persona rogeriana expandida (metodologia CNA, Foyers, Attention Active)
- [x] WebSocket com streaming de tokens em tempo real
- [x] Indicador visual "sintonizando..."
- [x] Análise de sentimento local com negação contextual (5 emoções, gênero/plural)
- [x] Temas de cor dinâmicos por emoção (CSS transitions)
- [x] Split-screen: chat (esquerda) + painel de cards (direita)
- [x] 27 cards de autoconhecimento ativados por keywords
- [x] 3 Foyers com barra de progresso (Interne, Externe, Stratégique)
- [x] Conexões entre cards, saltos evolutivos e reflexões
- [x] Filtros de cards por foyer
- [x] Expandir/arquivar cards
- [x] Fallback regex clássico da ELIZA (português)
- [x] Reconexão automática com backoff exponencial
- [x] Reset de conversa (limpa chat + cards)
- [x] Orbe animado de respiração no avatar do agente
- [x] Interface glassmorphism
- [x] Responsivo mobile-first
- [x] HTTPS/WSS com Let's Encrypt (Caddy)
- [x] Deploy automatizado (git push → Netlify)
- [x] Persistência de conversas no PostgreSQL com asyncpg
- [x] Detecção de abas simultâneas (desconecta aba antiga)

---

## 9. Pendências e Próximos Passos

### Críticas
- [ ] **Auth de usuários** — cadastro/login para múltiplos clientes
- [ ] **Pagamento recorrente** — Stripe para assinaturas mensais

### Funcionais
- [ ] **Exportação de cards** — PDF com temas descobertos
- [ ] **Troca dinâmica de modelo LLM** — selecionar via UI

### Melhorias
- [ ] **Integração de voz** — Web Speech API (STT/TTS)
- [ ] **Expansão de conexões e saltos** — mais padrões entre cards
- [ ] **Expansão do fallback regex** — 100+ regras do Lisp original
- [ ] **Áudio ambiente dinâmico** — sons adaptativos por emoção
- [ ] **Compactação de contexto** — resumir histórico para evitar estouro de tokens
- [ ] **27 conteúdos dos OCs** — escrever as cenas e pares de força dos outros 26 OCs
- [ ] **Acumulação entre OCs** — mosaico maior quando múltiplos OCs do mesmo foyer são explorados
- [ ] **Gráfico aranha** — visualização das inclinações por foyer

---

## 10. OC App — Objeto de Conhecimento (Prova de Conceito)

### Arquitetura

```
Chat ELIZA → card aparece na sidebar → usuário clica
    → fetch GET /oc/config/{oc_id}
    → Modal OC abre (3 cenas de escolha binária)
        → Cena 1 (ex: Trabalho) → Cena 2 (ex: Família) → Cena 3 (ex: Relação)
        → Mosaico final (ícones + frase descritiva)
    → "Voltar para conversa" ou "Quero terminar"
    → Card marcado como "Explorado" (borda verde)
    → WebSocket envia __oc_completed__:limites
    → ELIZA recebe contexto e reage naturalmente
```

### Dinâmicas do template (por OC)

| Dinâmica | Descrição |
|---|---|
| **Espelho indireto** | Usuário reage a cenas externas, não responde sobre si |
| **Tensão binária** | Cada cena tem 2 forças opostas (ex: Ceder × Impor) |
| **Personagem** | Constrói perfil de um personagem parecido com ele |
| **Rastro** | Mosaico de ícones se forma sem revelação antecipada |

### Configuração do OC (exemplo: Limites)

```python
OC_CONFIGS = {
    "limites": {
        "force_pair": ["Ceder", "Impor"],
        "scenes": [
            {"domain": "Trabalho", "color": "#4a6fa5", ...},
            {"domain": "Família",  "color": "#c4956a", ...},
            {"domain": "Relação", "color": "#b06e8a", ...},
        ],
        "mosaic_icons": {"left": "🤲", "right": "✋"}
    }
}
```

### Endpoints REST

| Método | Rota | Função |
|---|---|---|
| `GET` | `/oc/config/{oc_id}` | Retorna config do OC (cenas, cores, pares) |
| `GET` | `/oc/state/{conv}/{oc_id}` | Estado atual do OC (cena, escolhas, completado) |
| `POST` | `/oc/save` | Persiste progresso (cenas, escolhas) |
| `DELETE` | `/oc/reset/{conv}` | Zera todos os OCs da conversa |

### Banco de dados — tabela `oc_sessions`

```sql
id, conversation_id, oc_id, scene_index, choices (JSONB), completed, created_at, updated_at
```

### O que foi implementado hoje (23/06)

- [x] OC Limites: 3 cenas (Trabalho, Família, Relação) com eixo Ceder × Impor
- [x] Modal full-screen com cores por domínio
- [x] Mosaico final: ícones 🤲✋ + frase descritiva
- [x] Persistência no PostgreSQL (`oc_sessions`)
- [x] Botão "Reiniciar este exercício" no mosaico
- [x] Card muda para "Explorado" (borda verde) ao completar
- [x] ELIZA reage ao OC completado (recebe resumo, responde naturalmente)
- [x] Contexto do OC persiste no histórico de conversa
- [x] Reset global "Reiniciar" limpa OCs do banco
- [x] Correção: input reabilitado após reconexão
- [x] Correção: double-append no contexto OC
- [x] Correção: cards só do usuário, não da ELIZA
- [x] Correção: keywords desambiguadas para evitar falsos positivos
- [x] 27 objetos completos (8+13+6) + 25 conexões dinâmicas
- [x] Labels em português: Dimensões do Autoconhecimento

### O que falta para amanhã

1. **Conteúdo dos 26 OCs restantes** — cenas, domínios, pares de força (você escreve)
2. **Acumulação visual** — quando múltiplos OCs do mesmo foyer são explorados
3. **Sistema CNA** — diagnóstico antes do chat
4. **Gráfico aranha** — visual das inclinações por foyer

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