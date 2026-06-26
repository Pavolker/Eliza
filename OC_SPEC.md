# ELIZA OC — Especificação de Objetos de Conhecimento

## Conceito

Cada OC (Objeto de Conhecimento) é um exercício interativo de 3 cenas que revela padrões do usuário através de escolhas binárias. O exercício usa **espelho indireto**: o usuário reage a cenários externos, não responde sobre si mesmo diretamente.

## Estrutura de Dados

```python
OC_CONFIGS = {
    "oc_id": {                                    # Deve bater com key em OBJECTS_METADATA
        "id": "oc_id",
        "title": "Título do exercício",           # Appears no mosaico final
        "force_pair": ["Força A", "Força B"],     # Par de forças opostas
        "scenes": [
            {
                "text": "Cenário narrativo realista",
                "domain": "Domínio",              # ex: Trabalho, Família, Relação
                "domain_color": "#hexcode",       # Cor do domínio (para UI)
                "options": [
                    "Opção A (Força A)",          # choice=0
                    "Opção B (Força B)"           # choice=1
                ]
            },
            # ... 3 cenas no total
        ],
        "mosaic_icons": {
            "left": "🌀",                         # Ícone para Força A (choice=0)
            "right": "⚡"                         # Ícone para Força B (choice=1)
        }
    }
}
```

## Dinâmicas do Template

| Dinâmica | Descrição | Exemplo |
|----------|-----------|---------|
| **Espelho indireto** | Usuário reage a cenas externas, não responde sobre si | "Você está no trabalho..." |
| **Tensão binária** | Cada cena tem 2 forças opostas | Ceder × Impor |
| **Domínios variados** | 3 cenas de contextos diferentes | Trabalho, Família, Relação |
| **Mosaico acumulativo** | Ícones se acumulam conforme escolhas | 🤲🤲✋ |
| **Frase descritiva** | Gera texto baseado no padrão de escolhas | "Este personagem tende a ceder..." |

## Regras de Design

1. **Textos realistas**: Cenas devem ser situações cotidianas believable
2. **Escolhas autênticas**: Ambas opções devem ser razoáveis, sem "resposta certa"
3. **Domínios distintos**: Cada cena deve ser de contexto diferente
4. **Cores por domínio**: Usar paletaharmoniosa para cada domínio
5. **Forças complementares**: O par deve ser genuinamente oposto (não bom × ruim)

## 27 OCs — Repartição por Foyer

### Foyer Interne (8 OCs)
| ID | Título | force_pair | Domínios |
|----|--------|------------|----------|
| limites | Limites que você reconhece | Ceder × Impor | Trabalho, Família, Relação |
| reacoes | Reações recorrentes | Reagir × Refletir | Conflito, Crítica, Surpresa |
| sensacoes | Sensações do corpo | Ignorar × Atentar | Tensão, Desconforto, Intensidade |
| ritmos | Ritmos do seu corpo | Forçar × Respeitar | Rotina, Exaustão, Prazer |
| conflito | Como entra em conflito | Evitar × Enfrentar | Desacordo, Invasão, Competição |
| dependencias | Dependências que te prendem | Anexar × Soltar | Aprovação, Rotina, Substância |
| praticas | Práticas reflexivas | Abandonar × Manter | Meditação, Escrita, Movimento |
| observar | Capacidade de se observar | Envolver × Distanciar | Reação, Padrão, Motivação |

### Foyer Externe (13 OCs)
| ID | Título | force_pair | Domínios |
|----|--------|------------|----------|
| raizes | Raízes culturais | Manter × Questionar | Tradição, Linguagem, Crença |
| comunicacao | Jeito de se comunicar | Silenciar × Expressar | Conflito, Vulnerabilidade, Grupo |
| historias | Histórias que te formaram | Repetir × Transformar | Família, Escola, Trauma |
| lacos | Laços que te sustentam | Aproximar × Distanciar | Família, Amigos, Parceiro |
| valores | Valores que te guiam | Comprometer × Flexibilizar | Trabalho, Relação, Idealismo |
| feedbacks | O que os outros te dizem | Acolher × Questionar | Crítica, Elogio, Sugestão |
| apego | Como você se apega | Anexar × Libertar | Relação, Separação, Confiança |
| modelos_afeto | Modelos de afeto que repete | Repetir × Diversificar | Proteção, Intimidade, Autonomia |
| habilidades_sociais | Habilidades com pessoas | Recuar × Avançar | Networking, Conflito, Liderança |
| idiomas | Idiomas que você fala | Aprisionar × Expandir | Profissional, Íntimo, Estrangeiro |
| rituais | Rituais que você vive | Abandonar × Criar | Religioso, Familiar, Pessoal |
| comportamento | Jeito de se comportar | Autêntico × Adaptado | Público, Privado, Profissional |
| marcos_identidade | Marcos da sua identidade | Apegar × Soltar | Conquista, Perda, Transformação |

### Foyer Stratégique (6 OCs)
| ID | Título | force_pair | Domínios |
|----|--------|------------|----------|
| emocoes | Emoções que expressa | Contêr × Liberar | Raiva, Alegria, Tristeza, Medo |
| lidar_emocoes | Como lida com emoções | Evitar × Regular | Estresse, Frustração, Ansiedade |
| habitos | Hábitos do dia a dia | Automatizar × Deliberar | Manhã, Trabalho, Noite |
| saude | Como está sua saúde | Cuidar × Negligenciar | Prevenção, Tratamento, Estilo |
| decide | Como decide | Hesitar × Agir | Grande, Médio, Pequeno |
| metacognicao | Como pensa sobre pensar | Ruminar × Soltar | Preocupação, Decisão, Memória |

## Paleta de Cores por Domínio

Sugestão de cores para os 9 domínios principais:

| Domínio | Cor | Hex |
|---------|-----|-----|
| Trabalho | Azul | #4a6fa5 |
| Família | Laranja | #c4956a |
| Relação | Rosa | #b06e8a |
| Conflito | Vermelho | #c75a5a |
| Saúde | Verde | #5a9e7c |
| Criatividade | Roxo | #7a5a9e |
| Finanças | Dourado | #c4a55a |
| Social | Turquesa | #5a9e9e |
| Intimidade | Magenta | #9e5a8a |

## Exemplos de Cenas

### OC: Limites (referência)
```python
{
    "id": "limites",
    "title": "Limites que você reconhece",
    "force_pair": ["Ceder", "Impor"],
    "scenes": [
        {
            "text": "Você está saindo do trabalho às 18h. Seu chefe pede um relatório 'para ontem'.",
            "domain": "Trabalho",
            "domain_color": "#4a6fa5",
            "options": ["Fica e faz o relatório", "Diz que amanhã entrega"]
        },
        {
            "text": "Um parente quer que você organize a festa de fim de ano — de novo, como no ano passado.",
            "domain": "Família",
            "domain_color": "#c4956a",
            "options": ["Aceita, mesmo sabendo que vai se sobrecarregar", "Sugere que outro familiar organize desta vez"]
        },
        {
            "text": "Alguém próximo quer definir todo o seu fim de semana. Você só queria descansar.",
            "domain": "Relação",
            "domain_color": "#b06e8a",
            "options": ["Aceita o programa do outro sem discutir", "Propõe dividir: um período de descanso, um de programa"]
        }
    ],
    "mosaic_icons": {
        "left": "🤲",
        "right": "✋"
    }
}
```

## Checklist de Validação

Antes de implementar um OC, verificar:
- [ ] ID bate com key em OBJECTS_METADATA
- [ ] force_pair tem exatamente 2 forças opostas
- [ ] 3 cenas com domínios distintos
- [ ] Textos realistas e não-julgamentais
- [ ] Ambas opções autênticas (não há "resposta certa")
- [ ] Cores distintas por domínio
- [ ] Ícones significativos para cada força
- [ ] Keywords no OBJECTS_METADATA cobrindo o tema