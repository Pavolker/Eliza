# ELIZA — Interface Principal: Chat + Cards Dinâmicos

## Conceito do Produto

**Uma experiência em duas áreas simultâneas**:
- **Esquerda**: Agente ELIZA em conversação empática
- **Direita**: Cards que emergem e se transformam conforme os temas da conversa

---

## Layout da Interface

```
┌─────────────────────────┬──────────────────────────────────────┐
│                         │                                      │
│    🤖 ELIZA             │           📋 SEUS TEMAS              │
│    ─────────────        │           ──────────────             │
│                         │                                      │
│    [bolha de conversa]  │   ┌─────────────────────────────┐   │
│                         │   │  💡 Limites                 │   │
│    "Entendo. Parece     │   │  Você tem reconhecido       │   │
│     que os limites      │   │  que limites são um tema    │   │
│     aparecem muito      │   │  recorrente para você..."   │   │
│     na sua vida..."     │   └─────────────────────────────┘   │
│                         │                                      │
│    [bolha do usuário]   │   ┌─────────────────────────────┐   │
│                         │   │  💭 Reações que se repetem  │   │
│    "Sim, eu sempre      │   │  Padrões de resposta que    │   │
│     acabo aceitando     │   │  aparecem nas conversas...  │   │
│     coisas que não      │   └─────────────────────────────┘   │
│     quero..."           │                                      │
│                         │   ┌─────────────────────────────┐   │
│    [bolha de conversa]  │   │  🔗 Laços que sustentam     │   │
│                         │   │  Quem está ao seu lado?     │   │
│    "E como isso         │   └─────────────────────────────┘   │
│     acontece no seu     │                                      │
│     corpo?"             │           [ver mais cards...]       │
│                         │                                      │
│ ┌─────────────────────┐ │                                      │
│ │ Digite sua mensagem │ │                                      │
│ └─────────────────────┘ │                                      │
│                         │                                      │
└─────────────────────────┴──────────────────────────────────────┘
```

---

## Dinâmica dos Cards

### Como os Cards Aparecem

1. **ELIZA conversa** → detecta tema/objeto relevante
2. **Card emerge** na área da direita (animação suave)
3. **Card evolui** conforme o tema se aprofunda
4. **Outros cards aparecem** por conexão ou contraste
5. **Cards permanecem** acessíveis no histórico

### Estados de um Card

| Estado | Visual | Quando acontece |
|--------|--------|-----------------|
| **Novo** | Borda brilhante | Tema apareceu pela primeira vez |
| **Ativo** | Destacado | Tema sendo discutido agora |
| **Expandido** | Maior, com detalhes | Usuário clicou para aprofundar |
| **Arquivado** | Menor, opaco | Tema já trabalhado, em repouso |
| **Conectado** | Linha para outro card | Relação com outro tema descoberta |

---

## Tipos de Cards

### 1. Cards de Objetos (27 objetos)

Cada um dos 27 objetos de autoconhecimento pode virar um card:

**Foyer Interne (8)**:
| Card | Ícone | Gatilho de aparição |
|------|-------|---------------------|
| Limites que reconhece | 💡 | "não consigo dizer não", "sempre aceito" |
| Reações que se repetem | 🔄 | "de novo", "sempre faço isso" |
| Sensações do corpo | 🫀 | "meu corpo...", "sinto no peito" |
| Ritmos do corpo | ⏰ | "sono", "cansaço", "energia" |
| Como entra em conflito | ⚔️ | "briga", "discussão", "conflito" |
| Dependências que prendem | 🔗 | "não consigo sair", "preciso disso" |
| Práticas que aproximam de si | 🧘 | "medito", "caminho", "escrevo" |
| Capacidade de se observar | 👁️ | "percebi que", "me observei" |

**Foyer Externe (13)**:
| Card | Ícone | Gatilho de aparição |
|------|-------|---------------------|
| Raízes culturais | 🌳 | "minha família", "de onde venho" |
| Jeito de se comunicar | 💬 | "falo demais", "não consigo expressar" |
| Histórias que formaram | 📖 | "quando era criança", "meu pai sempre" |
| Laços que sustentam | 🤝 | "meus amigos", "minha parceira" |
| Feedbacks recorrentes | 📣 | "sempre me dizem", "ouço muito" |
| Como se apega | 💕 | "me apego muito", "tenho medo de perder" |
| Modelos de afeto | ❤️ | "nos meus relacionamentos" |
| Habilidades com pessoas | 👥 | "em grupos", "com as pessoas" |
| Idiomas que fala | 🗣️ | (contextual) |
| Rituais que vive | 🕯️ | "todo ano", "sempre faço" |
| Jeito de se comportar | 🎭 | "como me comporto", "minha postura" |
| Marcos da identidade | 📍 | "mudei muito", "momento importante" |
| Valores que guiam | ⭐ | "o que importa pra mim", "acredito" |

**Foyer Stratégique (6)**:
| Card | Ícone | Gatilho de aparição |
|------|-------|---------------------|
| Emoções que expressa | 😊😢😠 | "sinto muito", "estou feliz" |
| Como lida com emoções | 🎢 | "não sei lidar", "tento controlar" |
| Hábitos do dia a dia | 📅 | "todo dia", "minha rotina" |
| Como está sua saúde | 🩺 | "saúde", "médico", "dor" |
| Como decide | ⚖️ | "não sei decidir", "escolhas" |
| Como pensa sobre pensar | 🧠 | "penso demais", "minha mente" |

### 2. Cards de Conexão

Aparecem quando ELIZA detecta relação entre objetos:

```
┌─────────────────────────────────────┐
│  🔗 CONEXÃO DESCOBERTA              │
│  ───────────────────────            │
│                                     │
│  Seus LIMITES aparecem quando       │
│  fala de seus RELACIONAMENTOS       │
│                                     │
│  "Sempre aceito o que os outros     │
│   querem, mesmo quando não quero"   │
│                                     │
│  [Explorar essa conexão]            │
└─────────────────────────────────────┘
```

### 3. Cards de Sauts (Saltos Evolutivos)

Aparecem quando ELIZA detecta mudança qualitativa:

```
┌─────────────────────────────────────┐
│  ✨ SALTO EVOLUTIVO                 │
│  ───────────────────                │
│                                     │
│  Você percebeu algo novo:           │
│                                     │
│  "Antes eu não via que o problema   │
│   era meu limite. Agora posso       │
│   escolher diferente."              │
│                                     │
│  [Celebrar esse passo]              │
└─────────────────────────────────────┘
```

### 4. Cards de Reflexão

Surgem como convites ao final de um tema:

```
┌─────────────────────────────────────┐
│  📝 PARA REFLETIR                   │
│  ─────────────────                  │
│                                     │
│  "O que aconteceria se você         │
│   experimentasse dizer 'não'        │
│   uma vez essa semana?"             │
│                                     │
│  [Responder depois] [Ignorar]       │
└─────────────────────────────────────┘
```

### 5. Cards de Foyer (visão geral)

Visão panorâmica dos três focos:

```
┌─────────────────────────────────────┐
│  🎯 SEUS FOYERS                     │
│  ───────────────                    │
│                                     │
│  INTERNE    ████░░░░  5.2           │
│  (você)                             │
│                                     │
│  EXTERNE    ███░░░░░  3.8           │
│  (relações)                         │
│                                     │
│  STRATÉGIQUE ████░░░░  4.5          │
│  (escolhas)                         │
│                                     │
│  [Ver detalhes]                     │
└─────────────────────────────────────┘
```

---

## Exemplo de Fluxo Completo

### Cena 1: Chegada

**ELIZA**: "Oi. Como você está chegando hoje?"

**Usuário**: "Cansada. Foi uma semana difícil no trabalho."

**Cards que aparecem**:
```
┌───────────────┐  ┌───────────────┐
│ ⏰ Ritmos     │  │ 💼 Contexto   │
│ "Cansada"     │  │ "Trabalho"    │
│ apareceu      │  │ citado        │
└───────────────┘  └───────────────┘
```

### Cena 2: Aprofundamento

**ELIZA**: "Cansaço... E o que torna a semana difícil no trabalho?"

**Usuário**: "Meu chefe me cobra o tempo todo. E eu fico com medo de falar, de dizer que não dá pra fazer tudo."

**Cards que aparecem/evoluem**:
```
┌───────────────────┐  ┌───────────────────┐  ┌───────────────────┐
│ 💡 Limites        │  │ 😰 Medo          │  │ 💬 Comunicação    │
│ "Dizer não"       │  │ "Medo de falar"  │  │ "Não expressa"    │
│ ★ ATIVO           │  │ ★ NOVO           │  │ ★ NOVO            │
└───────────────────┘  └───────────────────┘  └───────────────────┘
```

### Cena 3: Conexão

**ELIZA**: "Parece que há algo entre seus limites e esse medo de falar. Você consegue ver isso?"

**Usuário**: "Sim... Na verdade, eu nunca aprendi a falar o que preciso. Em casa também era assim."

**Card de conexão aparece**:
```
┌─────────────────────────────────────┐
│ 🔗 CONEXÃO                          │
│ ──────────                          │
│ Limites ↔ Histórias que formaram    │
│                                     │
│ "Em casa também era assim"          │
│                                     │
│ [Aprofundar essa conexão]           │
└─────────────────────────────────────┘
```

### Cena 4: Fechamento

**ELIZA**: "Hoje percebemos algumas coisas importantes. Seus limites aparecem no trabalho, e isso parece ter raízes antigas. Que tal continuarmos essa conversa outro dia?"

**Card de reflexão aparece**:
```
┌─────────────────────────────────────┐
│ 📝 PARA LEVAR                       │
│ ───────────                         │
│                                     │
│ "Onde mais na sua vida você        │
│  sente que não consegue dizer      │
│  'não'?"                            │
│                                     │
│ [Refletir até a próxima]            │
└─────────────────────────────────────┘
```

---

## Interações com Cards

### Clique em Card

- **Expande** para mostrar mais detalhes
- **Mostra histórico** de quando esse tema apareceu
- **Oferece ação**: "Aprofundar agora", "Voltar à conversa"

### Hover em Card

- **Preview** do conteúdo
- **Conexões** com outros cards

### Arrastar Card

- **Reorganizar** posição
- **Agrupar** cards relacionados

### Arquivar Card

- **Esconder** tema trabalhado
- **Manter acessível** no histórico

---

## Área de Cards: Visualizações

### Modo Padrão (Cards)

Cards organizados em grade, priorizando os mais ativos.

### Modo Timeline (Cronologia)

Cards organizados por quando apareceram:
```
Hoje
  ├─ 💡 Limites (ativo)
  └─ ⏰ Ritmos

Ontem
  └─ 💕 Relacionamentos

Última semana
  └─ ⭐ Valores
```

### Modo Foyer (Três Focos)

Cards agrupados por Foyer:
```
┌─────────────────────────────────────────┐
│  INTERNE          │  EXTERNE           │
│  ────────         │  ───────           │
│  💡 Limites       │  🤝 Laços          │
│  🔄 Reações       │  💬 Comunicação    │
│  🫀 Sensações     │                    │
│                   ├────────────────────┤
│                   │  STRATÉGIQUE       │
│                   │  ───────────       │
│                   │  🎢 Emoções        │
│                   │  ⚖️ Decisões       │
└─────────────────────────────────────────┘
```

### Modo Conexões (Grafo)

Cards como nós conectados:
```
    💡 Limites ──────┬────── 🏠 Histórias
         │           │
         └─────── 💕 Relacionamentos
                        │
                   💬 Comunicação
```

---

## Diferenciais da Interface

1. **Conversa + Visualização**: Não é só chat, é chat com representação visual dos temas
2. **Cards vivos**: Aparecem, evoluem, se conectam — refletem o processo em tempo real
3. **Metodologia invisível**: Usuário vê "seus temas", não "objetos de autoconhecimento"
4. **Histórico acessível**: Pode voltar a qualquer tema trabalhado
5. **Conexões reveladas**: ELIZA mostra relações que o usuário não via

---

## Próximos Passos

1. **Wireframe da interface** (Figma/protótipo)
2. **Teste de usabilidade** com usuários reais
3. **Definir animações** de cards (aparecimento, expansão, conexão)
4. **Mapear todas as frases-gatilho** para cada objeto
5. **Prototipar versão mobile** (adaptação da interface)

---

## Referência

- Skill: `eliza-autoconhecimento`
- MVP: `~/APLICATIVO-MINI/ELIZA/MVP_APP_CONVERSACIONAL.md`
- Objetos: 27 objetos distribuídos nos 3 Foyers
