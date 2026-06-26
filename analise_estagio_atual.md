# Análise do Estágio de Desenvolvimento — ELIZA 2026 (26 de Junho de 2026)

Este documento registra a análise detalhada do estágio atual de desenvolvimento do aplicativo **ELIZA 2026**, mapeando os componentes implementados, o funcionamento da arquitetura e as pendências para evolução do projeto.

---

## 1. Visão Geral e Arquitetura

O aplicativo **ELIZA 2026** é um chatbot terapêutico reativo baseado na abordagem rogeriana (psicoterapia centrada na pessoa) e na metodologia do Autoconhecimento Ativo. A arquitetura divide-se em:

- **Frontend (Vanilla)**: Desenvolvido em HTML5, CSS3 e JavaScript puro (Vanilla JS), com design responsivo, estilo glassmorphism e iluminação dinâmica baseada no humor detectado.
- **Backend (FastAPI)**: Servidor assíncrono em Python utilizando FastAPI e WebSockets para streaming de tokens em tempo real.
- **Camada Cognitiva (LLM + Fallback)**:
  - **Principal**: Integração com a API do OpenRouter (usando SDK da OpenAI) chamando o modelo `gpt-4o-mini` com comportamento e diretrizes da persona rogeriana.
  - **Secundária (Fallback)**: Interpretador regex clássico local (estilo Weizenbaum traduzido para o português) ativado automaticamente se a conexão com a API falhar.
- **Banco de Dados**: PostgreSQL 16 (dockerizado) persistindo o histórico das conversas (`messages`) e o progresso dos exercícios interativos (`oc_sessions`). Caso o banco esteja indisponível, o sistema opera de forma resiliente mantendo os estados em memória RAM.

---

## 2. Status dos Componentes e Código Fonte

A análise do código-fonte local (`main.py`, `agent.py`, `app.js`, `index.html` e `style.css`) revela o seguinte panorama de implementação:

### A. Camada de Chat e Comunicação
- **WebSocket funcional**: Comunicação assíncrona bidirecional em tempo real funcionando com streaming de caracteres.
- **Gerenciamento de abas simultâneas**: Implementado no backend. Se uma nova aba abre a mesma sessão (`conversation_id`), a conexão anterior é notificada e desconectada para evitar corrupção de histórico.
- **Indicador de digitação**: UI exibe "sintonizando..." de forma reativa durante a geração de resposta pelo agente.
- **Fallback resiliente**: Testado e integrado. O dicionário de regex locais e o script `test_conversational.py` mostram que, caso a API do OpenRouter falhe, a resposta do backend chaveia imediatamente para o motor local.

### B. Mapeamento de Temas (Cards Dinâmicos)
- **Filtros e Visualização**: A área da direita (sidebar) exibe os temas desbloqueados e permite filtrar por foyers (*Interno, Externo, Estratégico*).
- **Gatilhos de ativação**: `main.py` contém um motor de busca por palavras-chave que ativa 27 temas possíveis baseados nas mensagens do usuário.
- **Conexões dinâmicas**: Sistema consegue cruzar a ativação simultânea de temas específicos (ex: `limites` + `conflito`) e gerar um card de conexão descobrindo o padrão.
- **Milestones conversacionais**: Mapeamento de "Saltos Evolutivos" baseados em frases de transição do usuário e cards de reflexão progressivos ("PARA LEVAR") ativados ao atingir 2, 5 e 10 temas mapeados.

### C. Módulo de OC (Objetos de Conhecimento)
- **Modal interativo**: Ao clicar em um card ativo, o sistema renderiza uma tela overlay de 3 cenas narrativas com escolhas binárias (tensão de forças).
- **Feedback para o Agente**: Quando o exercício do OC é completado, o frontend envia uma notificação WebSocket formatada em JSON (`oc_completed`) contendo o resumo das escolhas. O backend recebe essa estrutura, injeta no contexto da conversa (`oc_context`) e faz a ELIZA reagir de forma sutil e natural ao progresso.
- **Status "Explorado"**: O card concluído ganha borda verde e a tag "Explorado".

---

## 3. Checklist de Implementação (Status Real)

Comparando a especificação e os arquivos do repositório, identificamos o status exato das funcionalidades planejadas:

### 🟢 Concluído e Operacional
- [x] Persona rogeriana integrada via prompt de sistema no OpenRouter (`gpt-4o-mini`).
- [x] Detecção local de sentimentos (5 estados) com suavização de negação contextual no backend.
- [x] Mudança cromática e iluminação ambiental dinâmica na interface (calma, alegria, tristeza, raiva, ansiedade).
- [x] Layout split-screen responsivo para desktop e mobile.
- [x] Detecção e criação automática de cards de conexão, saltos evolutivos e reflexões.
- [x] Mecanismo de persistência das conversas e progresso de OCs no PostgreSQL (com lifespan assíncrono).
- [x] Prova de conceito (PoC) do **OC Limites** funcional (3 cenas: Trabalho, Família, Relação; mosaico final com ícones 🤲 e ✋; botão para reiniciar o exercício).
- [x] Resiliência local: fallback regex e execução em memória se o banco falhar.

### 🟡 Parcialmente Implementado / Pendente
- [ ] **Conteúdo dos 26 OCs restantes**: Apenas o OC `"limites"` está configurado no dicionário `OC_CONFIGS` em `main.py`. Os outros 26 temas mapeados em `OBJECTS_METADATA` ainda necessitam que suas respectivas cenas, domínios, pares de forças e mosaicos de ícones sejam escritos e incluídos nas configurações do backend.
- [ ] **Persistência avançada no cliente**: A sincronização automática do `conversation_id` via `localStorage` e carregamento do histórico existe, mas o app carece de um fluxo formal de login para que usuários compartilhem sessões de forma segura entre dispositivos.

### 🔴 Planejado / Não Iniciado
- [ ] **Acumulação visual**: Exibir um mosaico expandido ou dashboard gráfico quando múltiplos OCs de um mesmo foyer forem concluídos.
- [ ] **Gráfico aranha (Spider Chart)**: Gráfico visual indicando a inclinação do usuário em relação a cada um dos Foyers.
- [ ] **Diagnóstico CNA Inicial**: Sistema de onboarding ou triagem para identificar o tipo de crise (*Interna, Relacional, Contextual*) antes de iniciar o diálogo aberto.
- [ ] **Exportação em PDF**: Gerar relatório final compilando todos os cards e reflexões descobertos pelo usuário.
- [ ] **Customização do Modelo**: Seletor visual na interface para o usuário alternar o modelo de LLM em uso.
- [ ] **Integração de Voz**: Recursos de voz baseados na Web Speech API (transcrição e síntese).
- [ ] **Sons ambientais**: Trilha sonora dinâmica e relaxante que se adapta às emoções e humor detectados na conversa.

---

## 4. Diagnóstico Técnico de Infraestrutura

Executando diagnósticos locais no repositório:
1. **Ambiente de Testes**: O script `test_conversational.py` foi executado com sucesso e confirmou o funcionamento do fluxo de streaming com o OpenRouterAgent, além do chaveamento resiliente (o banco de dados local não estava com o usuário configurado, e o sistema iniciou em memória RAM sem quebrar).
2. **CORS e Deploy**: A configuração de CORS no `main.py` foi aprimorada recentemente para carregar dinamicamente as origens a partir da variável `CORS_ORIGINS`, permitindo um deploy seguro tanto no Netlify quanto no Caddy local.
3. **Docker**: O repositório está pronto com configurações de compose, contudo o Docker local do usuário estava inativo durante a verificação (o backend se adapta e roda com SQLite/RAM se necessário).

---

## 5. Próximos Passos Sugeridos

Para levar o aplicativo do estágio de homologação atual para um produto completo e maduro, recomenda-se:

1. **Definição e inserção dos 26 OCs**: Desenvolver a narrativa das 3 cenas e escolhas para os 26 temas restantes no backend (ex: `reacoes`, `sensacoes`, `ritmos`, `conflito`, etc.).
2. **Implementação da Tela de Diagnóstico CNA**: Criar o modal/fluxo inicial para mapear o perfil da crise de chegada do usuário.
3. **Gráfico de Foyers**: Inserir uma visualização gráfica (como Chart.js ou SVG interativo) para ilustrar o avanço e equilíbrio entre as 3 Dimensões de Autoconhecimento na sidebar.
4. **Resumo Automático de Contexto**: Adicionar compressão/resumo de histórico no backend para otimizar o consumo de tokens em conversas longas e evitar estouro de limite da API.
