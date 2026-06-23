# Relatório de Desenvolvimento: ELIZA 2026

Este documento registra o histórico das implementações realizadas, a arquitetura do sistema e o estágio atual de desenvolvimento da **ELIZA 2026**, uma versão moderna, empática e responsiva do chatbot de 1964, focada em escuta ativa centrada na pessoa (abordagem rogeriana).

---

## 1. Estágio Atual do Aplicativo

O aplicativo encontra-se no estágio de **Produção Homologada (Online e Funcional)**. 

### URLs de Acesso:
- **Frontend (Produção)**: [https://autoconhecer.netlify.app](https://autoconhecer.netlify.app)
- **Backend (Produção)**: `wss://eliza.mdh-hability.com` (terminação SSL via Caddy reverse proxy)

---

## 2. Histórico de Implementações Realizadas

### A. Camada Cognitiva e Backend
- **Migração de Modelo (Gemini → OpenRouter)**: Transição do SDK Google Antigravity e Gemini Flash para o SDK OpenAI chamando o modelo `gpt-4o-mini` do OpenRouter. Esta mudança otimizou a persistência, flexibilidade e tempo de resposta da inteligência rogeriana.
- **Resiliência e Fallback Local**: Implementação de um interpretador local baseado em expressões regulares clássicas (regras clássicas de Weizenbaum traduzidas para o português). Caso ocorra falha de conexão com a API ou esgotamento de cotas, o sistema entra em fallback automaticamente e responde de forma simulada em tempo de digitação real, garantindo que o usuário nunca seja deixado sem resposta.
- **Persistência de Dados**: Integração de suporte a banco de dados PostgreSQL 16 (dockerizado) para o histórico das sessões (executa em memória caso o banco esteja indisponível).
- **Análise de Emoções**: Detector de humor local baseado em palavras-chave que classifica a mensagem em 5 tonalidades: *calma, alegria, tristeza, raiva e ansiedade* em tempo real.

### B. Interface e Design (Redesenho Split-Screen)
- **Visual Vertical em Duas Faixas (Desktop)**: Reformulação completa do layout. O cabeçalho superior global foi removido, dividindo a tela em dois painéis independentes:
  - **Coluna da Esquerda (Agente + Chat)**: Apresenta o cabeçalho do agente (`agent-profile`) contendo o avatar circular com o orbe de respiração dinâmico, o status da conexão do WebSocket ("Em sintonia com você") e o botão discreto para reinicializar a conversa. O chat e a caixa de entrada ocupam o restante do espaço com rolagem própria.
  - **Coluna da Direita (Painel de Temas)**: Contém o progresso dos três Foyers (*Interne, Externe e Stratégique*) e a listagem de cards de autoconhecimento gerados dinamicamente pelas palavras ditas no diálogo.
- **Tema de Cores Dinâmico**: O fundo do aplicativo e a cor de destaque do orbe do agente transicionam de cor suavemente via CSS baseados na emoção detectada (ex: tons azuis para calma, vermelhos para raiva, amarelos para alegria e verdes para ansiedade).

### C. Sincronização Dinâmica de Cards
- **Suporte a Gênero e Plural**: Correção e ampliação de todas as palavras-chave do dicionário de gatilhos do backend (`main.py`) e do analisador de emoções. Agora o sistema reconhece flexões femininas (como *"cansada"*, *"ansiosa"*, *"preocupada"*, *"sozinha"*) e variações no plural (como *"limites"*, *"conflitos"*, *"brigas"*), assegurando que o diálogo flua naturalmente e os cards correspondentes na direita sejam ativados perfeitamente em tempo de conversa.

---

## 3. Arquitetura do Sistema

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
└─────────────────────────────────────────────────────────┘
```

---

## 4. Pipeline de Publicação (Deploy)

As atualizações da plataforma são propagadas de forma híbrida:
1. **Frontend**: Publicação disparada por commit na branch principal do GitHub (`Pavolker/Eliza`), o que inicia o build e deploy instantâneos nos servidores CDN da Netlify.
2. **Backend**: Sincronização dos arquivos de código Python (`main.py`, `agent.py`, `requirements.txt`) para o diretório `/opt/eliza` no servidor Hetzner através de `rsync`, seguido pela reconstrução do container da API via Docker Compose:
   ```bash
   docker compose up -d --build
   ```

---

## 5. Próximos Passos Propostos

1. **Persistência Avançada de Conversas**: Implementar o schema final no PostgreSQL para restaurar o histórico das conversas mesmo após limpar o `localStorage` do navegador ou trocar de dispositivo.
2. **Autenticação de Usuários**: Adicionar uma tela de login/cadastro simples para que múltiplos usuários possam manter seus temas de autoconhecimento salvos de maneira segura e individualizada.
3. **Expansão do Dicionário de Gatilhos**: Continuar mapeando padrões conversacionais e expandir as conexões e reflexões automáticas geradas pela ELIZA.
