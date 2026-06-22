# Relatório de Desenvolvimento: ELIZA 2026

Este documento registra o estado atual do desenvolvimento, os pontos críticos mapeados, as fragilidades e as direções para aprimoramento da **ELIZA 2026**, uma versão moderna e empática do chatbot clássico de 1964.

---

## 1. Status do Desenvolvimento

O aplicativo encontra-se no estágio de **Protótipo Funcional Resiliente (Pronto para Uso)**. A arquitetura foi desenhada como um sistema híbrido de duas camadas para garantir que a experiência do usuário nunca seja interrompida.

### Componentes Implementados:
*   **Camada Cognitiva (Google Antigravity SDK)**: Wrapper do modelo Gemini 3.5 Flash configurado com uma persona psicoterapêutica da escola de Carl Rogers (Abordagem Centrada na Pessoa). Focado em escuta ativa, sem julgamentos e em tom estritamente humano.
*   **Camada de Fallback Local (Regex Clássico)**: Mecanismo local em Python que intercepta falhas de cota ou conexão e responde instantaneamente com as regras originais de expressões regulares em português (padrões como `mãe`, `triste`, `preciso de`, `talvez`).
*   **Servidor Web (FastAPI + WebSockets)**: Endpoints assíncronos para streaming de texto palavra por palavra (tanto para respostas da IA quanto para as simuladas de fallback) e serving de arquivos estáticos.
*   **Análise de Sentimentos Otimizada**: Classificador local de palavras-chave que detecta a tonalidade emocional do usuário (tristeza, alegria, raiva, ansiedade ou calma) em microssegundos, sem consumir cota da API.
*   **Interface Acolhedora (HTML/CSS/JS)**: UI baseada em Glassmorphism, com orbe animado de respiração e transição de cores ambientais suaves baseadas nas emoções. Inclui sistema de sincronização e reset de sessão no `localStorage`.

---

## 2. Pontos Críticos Mapeados

Durante a implementação e homologação, os seguintes fatores técnicos mostraram-se vitais para o funcionamento do sistema:

### A. Sobrescrita de Diretrizes de Desenvolvimento (Persona Pura)
*   **Desafio**: Inicialmente, ao usar `TemplatedSystemInstructions`, o SDK injetava diretivas padrão destinadas a agentes de desenvolvimento (como a ordem de gerar um resumo de trabalho e relatórios markdown). Isso fazia a ELIZA "vazar" informações técnicas no chat com o usuário.
*   **Solução**: O uso do `CustomSystemInstructions` no arquivo [agent.py](file:///Users/APLICATIVOS GERAIS/ELIZA/agent.py) garantiu o isolamento e controle absoluto sobre a persona conversacional.

### B. Gestão de Estado e Persistência física do SQLite
*   **Desafio**: O SDK do Antigravity armazena as conversas localmente como bancos de dados SQLite com nomes gerados por hashes MD5 (`conversations/<id_conversa>.db`). Tentar retomar uma conversa inexistente informando um ID arbitrário fazia o harness do SDK travar na inicialização.
*   **Solução**: O arquivo [agent.py](file:///Users/APLICATIVOS GERAIS/ELIZA/agent.py#L30-L40) agora inspeciona o disco antes de inicializar a conexão. Se o arquivo `.db` correspondente ao ID enviado pelo navegador não existir (primeiro carregamento ou após reset), o parâmetro é tratado como `None` para induzir o SDK a criar uma nova sessão limpa.

---

## 3. Fragilidades do Sistema

Embora o aplicativo esteja estruturado para nunca travar (devido ao fallback de regex), as seguintes fragilidades devem ser consideradas:

### A. Dependência Estrita de Cota da API (Free Tier)
*   A chave de API Gemini no plano gratuito possui um limite severo de **20 requisições por dia por modelo**. Em testes ativos, esse limite é atingido muito rapidamente. Embora o fallback clássico de regex garanta respostas rogerianas clássicas funcionais, o agente perde a memória contextual rica de longo prazo até que a cota seja reestabelecida.

### B. Simplificação da Análise de Sentimentos Local
*   A mudança do classificador semântico por LLM para um analisador baseado em palavras-chave reduziu o consumo de cota a zero, mas limitou a precisão. O sistema não compreende sarcasmo ou sinônimos complexos fora do dicionário predefinido no arquivo [main.py](file:///Users/APLICATIVOS GERAIS/ELIZA/main.py#L26-L46).

### C. Concorrência e Sincronização de Abas
*   Se o usuário abrir o endereço em duas abas diferentes simultaneamente, ambas compartilharão o mesmo `conversationId` no `localStorage`, o que pode causar inconsistências na entrega de mensagens via WebSockets.

---

## 4. Possibilidades de Aperfeiçoamento

Para levar a ELIZA 2026 a um nível de excelência comercial, propõem-se os seguintes aprimoramentos:

### A. Integração de Voz (Áudio Bidirecional)
*   **Como fazer**: Incorporar APIs Web de síntese e reconhecimento de voz (Speech-to-Text e Text-to-Speech) diretamente no navegador para permitir que o usuário fale e ouça a ELIZA, tornando a sensação de conexão muito mais íntima.

### B. Dicionário de Regex Ampliado (Camada de Fallback)
*   **Como fazer**: Expandir o dicionário `REGRAS_FALLBACK` em [main.py](file:///Users/APLICATIVOS GERAIS/ELIZA/main.py) com a tradução completa das mais de 100 regras clássicas da ELIZA descritas no Lisp original de Peter Norvig (PAIP), cobrindo uma variedade muito maior de construções linguísticas.

### C. Compactação e Resumo de Contexto
*   **Como fazer**: Implementar rotinas do SDK para resumir periodicamente a memória de conversa antiga, impedindo que o histórico SQLite cresça indefinidamente e atinja o limite máximo de tokens do modelo Gemini.

### D. Atmosfera Sonora Dinâmica
*   **Como fazer**: Adicionar áudios ambientais suaves em segundo plano no frontend (como sons de chuva fina, piano de meditação ou ruído rosa) que se adaptam ou mudam de volume de acordo com a emoção detectada pelo analisador de sentimentos.
