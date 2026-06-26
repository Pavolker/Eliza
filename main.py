import asyncio
import re
import random
import json
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
import logging
from contextlib import asynccontextmanager
import asyncpg

from agent import OpenRouterAgent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("eliza.main")

# Dicionário global para rastrear conexões WebSocket ativas por session_id
active_connections = {}

OBJECTS_METADATA = {
    "limites": {
        "title": "Limites que reconhece",
        "icon": "💡",
        "foyer": "interne",
        "text": "Você tem refletido sobre seus limites pessoais e a dificuldade em dizer 'não' quando necessário.",
        "keywords": ["dizer não", "não consigo dizer não", "limite", "limites", "sempre aceito", "aceitar tudo"]
    },
    "reacoes": {
        "title": "Reações recorrentes",
        "icon": "🔄",
        "foyer": "interne",
        "text": "Padrões automáticos e comportamentos de resposta interpessoal que tendem a se repetir ciclicamente.",
        "keywords": ["de novo", "sempre faço isso", "padrão", "repetir", "recorrente"]
    },
    "sensacoes": {
        "title": "Sensações do corpo",
        "icon": "🫀",
        "foyer": "interne",
        "text": "A percepção de manifestações físicas, tensões ou batimentos cardíacos que revelam o estado emocional.",
        "keywords": ["sinto no peito", "tensão física", "tensão no corpo", "coração acelerado", "palpitação", "aperto no peito", "formigamento", "calafrio", "nó na garganta", "falta de ar"]
    },
    "ritmos": {
        "title": "Ritmos do seu corpo",
        "icon": "⏰",
        "foyer": "interne",
        "text": "Seus ciclos biológicos, padrões de sono, fadiga crônica e como reage ao esgotamento físico.",
        "keywords": ["sono", "cansaço", "energia", "cansado", "cansada", "exaust", "dormir", "fadiga"]
    },
    "conflito": {
        "title": "Como entra em conflito",
        "icon": "⚔️",
        "foyer": "interne",
        "text": "Sua postura, gatilhos de agressividade ou recuo diante de desentendimentos e atritos.",
        "keywords": ["briga", "brigas", "discussão", "discussões", "conflito", "conflitos", "chefe", "atrito", "atritos", "discutir", "cobrança", "cobranças"]
    },
    "dependencias": {
        "title": "Dependências que te prendem",
        "icon": "🔗",
        "foyer": "interne",
        "text": "Apego a aprovações, hábitos ou dinâmicas emocionais que limitam sua autonomia e poder de escolha.",
        "keywords": ["não consigo sair", "preciso disso", "dependência", "dependências", "perfeccionismo", "aprovação", "validação", "reconhecimento externo"]
    },
    "praticas": {
        "title": "Práticas reflexivas",
        "icon": "🧘",
        "foyer": "interne",
        "text": "Hábitos e rotinas de autopercepção, pausas deliberadas ou momentos de escuta atenta a si mesmo.",
        "keywords": ["medito", "caminho", "escrevo", "pausa", "meditação", "respiro", "caminhada"]
    },
    "observar": {
        "title": "Capacidade de se observar",
        "icon": "👁️",
        "foyer": "interne",
        "text": "Capacidade de distanciar-se das reações automáticas e analisar os próprios comportamentos.",
        "keywords": ["percebi que", "me observei", "reparei", "notei em mim", "percepção"]
    },
    "raizes": {
        "title": "Raízes culturais",
        "icon": "🌳",
        "foyer": "externe",
        "text": "A herança familiar, o contexto social e as influências étnicas na sua formação como sujeito.",
        "keywords": ["minha família", "de onde venho", "minha terra", "minha criação", "origem", "origens"]
    },
    "comunicacao": {
        "title": "Jeito de se comunicar",
        "icon": "💬",
        "foyer": "externe",
        "text": "Estilo de expressão verbal, clareza ao comunicar necessidades e assertividade nas conversas.",
        "keywords": ["falo demais", "não consigo expressar", "falar", "comunicação", "expressar", "assertividade"]
    },
    "historias": {
        "title": "Histórias que te formaram",
        "icon": "📖",
        "foyer": "externe",
        "text": "Narrativas e memórias de infância, lições herdadas e papéis que assumiu na história familiar.",
        "keywords": ["quando era criança", "meu pai", "minha mãe", "em casa", "infância", "passado", "antigamente"]
    },
    "lacos": {
        "title": "Laços que te sustentam",
        "icon": "🤝",
        "foyer": "externe",
        "text": "Sua rede de suporte afetivo, amigos, parceiros e pessoas nas quais encontra segurança emocional.",
        "keywords": ["meus amigos", "minha parceira", "parceiro", "apoio", "suporte", "rede de apoio", "amizades", "amigo", "amiga"]
    },
    "valores": {
        "title": "Valores que te guiam",
        "icon": "⭐",
        "foyer": "externe",
        "text": "Crenças fundamentais, ética pessoal e ideais que direcionam suas decisões importantes.",
        "keywords": ["o que importa", "acredito", "valores", "justiça", "equilíbrio", "princípios", "ética"]
    },
    "feedbacks": {
        "title": "O que os outros te dizem",
        "icon": "🗣️",
        "foyer": "externe",
        "text": "Feedbacks recorrentes que você recebe de pessoas próximas sobre seu comportamento ou personalidade.",
        "keywords": ["sempre me dizem", "as pessoas falam", "me chamam de", "dizem que sou", "feedback", "me disseram", "ouvi que", "comentam"]
    },
    "apego": {
        "title": "Como você se apega",
        "icon": "🧷",
        "foyer": "externe",
        "text": "Seu estilo de apego nas relações: segurança, ansiedade ou evitação nos vínculos afetivos.",
        "keywords": ["apegado", "apegada", "apego", "grudado", "grudada", "não consigo confiar", "medo de abandono", "distante", "não me envolvo"]
    },
    "modelos_afeto": {
        "title": "Modelos de afeto que repete",
        "icon": "💞",
        "foyer": "externe",
        "text": "Padrões de vínculo afetivo que você reproduz, herdados de experiências passadas.",
        "keywords": ["sempre namoro", "mesmo tipo de pessoa", "relacionamento igual", "repito padrão", "escolho errado", "escolho errada", "sempre acontece", "mesma história"]
    },
    "habilidades_sociais": {
        "title": "Habilidades com pessoas",
        "icon": "🫂",
        "foyer": "externe",
        "text": "Suas habilidades sociais: escuta, assertividade, negociação e capacidade de pedir ajuda.",
        "keywords": ["não sei escutar", "assertivo", "assertiva", "negociar", "pedir ajuda", "habilidade social", "timidez", "tímido", "tímida", "não consigo falar em público"]
    },
    "idiomas": {
        "title": "Idiomas que você fala",
        "icon": "🌐",
        "foyer": "externe",
        "text": "As línguas que você domina e como elas ampliam ou limitam sua inserção cultural.",
        "keywords": ["idioma", "língua", "inglês", "francês", "espanhol", "português", "aprendendo", "estrangeiro", "outra língua"]
    },
    "rituais": {
        "title": "Rituais que você vive",
        "icon": "🕯️",
        "foyer": "externe",
        "text": "Participação em rituais, símbolos coletivos ou tradições que marcam sua vida.",
        "keywords": ["ritual", "tradição", "costume", "celebração", "natal", "ano novo", "religioso", "cerimônia", "culto", "missa", "rito"]
    },
    "comportamento": {
        "title": "Jeito de se comportar",
        "icon": "🎭",
        "foyer": "externe",
        "text": "Padrões de comportamento social: como você age em grupo, em público e em situações novas.",
        "keywords": ["em público", "em grupo", "socialmente", "festas", "eventos", "multidão", "desconhecidos", "novas pessoas"]
    },
    "marcos_identidade": {
        "title": "Marcos da sua identidade",
        "icon": "🏛️",
        "foyer": "externe",
        "text": "Acontecimentos que definiram quem você é: conquistas, rupturas e viradas na sua história.",
        "keywords": ["mudou minha vida", "marco", "virada", "conquista", "formatura", "mudei de cidade", "divisor de águas", "antes e depois"]
    },
    "emocoes": {
        "title": "Emoções que expressa",
        "icon": "😊",
        "foyer": "strategique",
        "text": "Seu repertório expressivo e o modo como as emoções são manifestadas nas relações cotidianas.",
        "keywords": ["sinto muito", "estou feliz", "emocional", "expressar o que sinto"]
    },
    "lidar_emocoes": {
        "title": "Como lida com emoções",
        "icon": "🎢",
        "foyer": "strategique",
        "text": "Como você regula sentimentos intensos, estresse, ansiedade e angústia.",
        "keywords": ["não sei lidar", "tento controlar", "regulação", "controlar minhas emoções"]
    },
    "habitos": {
        "title": "Hábitos do dia a dia",
        "icon": "📅",
        "foyer": "strategique",
        "text": "Suas rotinas práticas e o impacto delas na sua saúde, foco e estabilidade psíquica.",
        "keywords": ["todo dia", "minha rotina", "hábitos", "cotidiano", "diariamente"]
    },
    "saude": {
        "title": "Como está sua saúde",
        "icon": "🩺",
        "foyer": "strategique",
        "text": "Seu nível de vitalidade, sono, nutrição e o cuidado geral com a saúde física e mental.",
        "keywords": ["saúde", "médico", "médica", "doença", "doenças", "vitalidade", "exame", "consulta", "remédio", "tratamento", "diagnóstico", "internação", "hospital"]
    },
    "decide": {
        "title": "Como decide",
        "icon": "⚖️",
        "foyer": "strategique",
        "text": "Processos cognitivos e emocionais na hora de fazer escolhas importantes.",
        "keywords": ["não sei decidir", "escolhas", "decidir", "decisão", "decisões", "escolha"]
    },
    "metacognicao": {
        "title": "Como pensa sobre pensar",
        "icon": "🧠",
        "foyer": "strategique",
        "text": "Suas habilidades de metacognição, ruminação mental ou observação dos próprios pensamentos.",
        "keywords": ["penso demais", "minha mente", "metacognição", "pensamentos", "ruminar", "ruminação"]
    }
}

OC_CONFIGS = {
    "limites": {
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
    },
    "reacoes": {
        "id": "reacoes",
        "title": "Reações recorrentes",
        "force_pair": ["Reagir", "Refletir"],
        "scenes": [
            {
                "text": "Durante uma reunião, um colega critica abertamente sua parte de um projeto comum.",
                "domain": "Conflito",
                "domain_color": "#c75a5a",
                "options": ["Responde de imediato justificando seu ponto com firmeza", "Ouve calado, anota os pontos e analisa antes de responder"]
            },
            {
                "text": "Um familiar próximo faz um comentário irônico sobre suas escolhas recentes na vida pessoal.",
                "domain": "Família",
                "domain_color": "#c4956a",
                "options": ["Retruca com ironia para se defender na hora", "Respira fundo, ignora o tom e decide conversar com calma depois"]
            },
            {
                "text": "Você recebe a notícia inesperada de que a empresa cancelou uma iniciativa em que você trabalhou meses.",
                "domain": "Trabalho",
                "domain_color": "#4a6fa5",
                "options": ["Expressa sua frustração publicamente na mesma hora", "Afasta-se da mesa para digerir a notícia e pensar nos próximos passos"]
            }
        ],
        "mosaic_icons": {
            "left": "⚡",
            "right": "⏳"
        }
    },
    "sensacoes": {
        "id": "sensacoes",
        "title": "Sensações do corpo",
        "force_pair": ["Ignorar", "Atentar"],
        "scenes": [
            {
                "text": "Em meio a uma discussão tensa de trabalho, você sente um aperto no peito e o coração acelerar.",
                "domain": "Conflito",
                "domain_color": "#c75a5a",
                "options": ["Foca na conversa e continua falando apesar do desconforto", "Faz uma pausa mental para notar de onde vem essa opressão física"]
            },
            {
                "text": "No final de um dia exaustivo com tarefas acumuladas da família, suas costas e ombros ardem.",
                "domain": "Família",
                "domain_color": "#c4956a",
                "options": ["Continua os afazeres domésticos sem parar", "Para por 5 minutos para esticar o corpo e respirar fundo"]
            },
            {
                "text": "Ao se preparar para um encontro importante, uma sensação de friozinho na barriga te domina.",
                "domain": "Relação",
                "domain_color": "#b06e8a",
                "options": ["Tenta se distrair com o celular para esquecer o frio na barriga", "Fecha os olhos e deixa a energia da expectativa fluir no corpo"]
            }
        ],
        "mosaic_icons": {
            "left": "🙈",
            "right": "🧘"
        }
    },
    "ritmos": {
        "id": "ritmos",
        "title": "Ritmos do seu corpo",
        "force_pair": ["Forçar", "Respeitar"],
        "scenes": [
            {
                "text": "Você já trabalhou 10 horas seguidas e o sono começa a pesar, mas ainda faltam emails para responder.",
                "domain": "Trabalho",
                "domain_color": "#4a6fa5",
                "options": ["Toma mais um café para terminar as pendências hoje", "Fecha o notebook e deixa o restante para o dia seguinte"]
            },
            {
                "text": "No fim de semana, você planejou limpar a casa inteira, mas acorda com uma forte dor de cabeça.",
                "domain": "Família",
                "domain_color": "#c4956a",
                "options": ["Toma um analgésico e começa a faxina mesmo assim", "Deita-se no quarto escuro e adia a limpeza para quando melhorar"]
            },
            {
                "text": "Seus amigos te convidam para uma festa animada, mas você sente que precisa de um momento de silêncio doméstico.",
                "domain": "Social",
                "domain_color": "#5a9e9e",
                "options": ["Força-se a ir para não decepcionar o grupo", "Agradece o convite e fica em casa recarregando as energias"]
            }
        ],
        "mosaic_icons": {
            "left": "🏃",
            "right": "🍃"
        }
    },
    "conflito": {
        "id": "conflito",
        "title": "Como entra em conflito",
        "force_pair": ["Evitar", "Enfrentar"],
        "scenes": [
            {
                "text": "Um colega de equipe assume o crédito por uma ideia sua na frente da diretoria.",
                "domain": "Trabalho",
                "domain_color": "#4a6fa5",
                "options": ["Deixa passar para não criar um clima ruim", "Pede a palavra educadamente e pontua sua contribuição no projeto"]
            },
            {
                "text": "Seu parceiro(a) faz algo que te magoa profundamente na frente de amigos comuns.",
                "domain": "Relação",
                "domain_color": "#b06e8a",
                "options": ["Finge que está tudo bem para evitar cena em público", "Chama a pessoa de canto e expressa seu descontentamento na hora"]
            },
            {
                "text": "Em uma reunião de condomínio ou grupo familiar, um parente faz acusações injustas ao seu respeito.",
                "domain": "Família",
                "domain_color": "#c4956a",
                "options": ["Retira-se do local sem discutir para não piorar as coisas", "Responde à acusação de frente e exige respeito dos envolvidos"]
            }
        ],
        "mosaic_icons": {
            "left": "🛡️",
            "right": "⚔️"
        }
    },
    "dependencias": {
        "id": "dependencias",
        "title": "Dependências que te prendem",
        "force_pair": ["Anexar", "Soltar"],
        "scenes": [
            {
                "text": "Você desenhou uma proposta de projeto excelente, mas hesita em enviar antes que seu mentor a valide.",
                "domain": "Trabalho",
                "domain_color": "#4a6fa5",
                "options": ["Guarda o arquivo esperando o aval, mesmo atrasando o prazo", "Envia a proposta confiando na qualidade do seu trabalho autônomo"]
            },
            {
                "text": "Um amigo próximo parece frio ou distante nas mensagens hoje e você fica ansioso por uma resposta calorosa.",
                "domain": "Social",
                "domain_color": "#5a9e9e",
                "options": ["Manda mensagens extras perguntando se fez algo errado", "Dá espaço ao amigo e segue seu dia sem focar nisso"]
            },
            {
                "text": "Você sente o hábito de tomar uma taça de vinho ou usar redes sociais para relaxar sempre que o estresse aperta.",
                "domain": "Saúde",
                "domain_color": "#5a9e7c",
                "options": ["Recorre imediatamente ao hábito para aliviar a tensão", "Decide passar a noite sem isso, encarando o tédio ou o estresse"]
            }
        ],
        "mosaic_icons": {
            "left": "🔗",
            "right": "🕊️"
        }
    },
    "praticas": {
        "id": "praticas",
        "title": "Práticas reflexivas",
        "force_pair": ["Abandonar", "Manter"],
        "scenes": [
            {
                "text": "Sua rotina matinal está apertada com reuniões marcadas mais cedo, reduzindo seu tempo de meditação/leitura habitual.",
                "domain": "Trabalho",
                "domain_color": "#4a6fa5",
                "options": ["Pula a prática para garantir que chegará adiantado", "Acorda 15 minutos mais cedo para manter a prática antes do trabalho"]
            },
            {
                "text": "Nas férias familiares, todos estão agitados programando passeios intensos o dia inteiro.",
                "domain": "Família",
                "domain_color": "#c4956a",
                "options": ["Segue o fluxo coletivo e deixa seu caderno de notas/rotina de lado", "Explica ao grupo que precisa de 20 minutos de isolamento de manhã"]
            },
            {
                "text": "Você está de mau humor ou irritado hoje e a ideia de se exercitar ou escrever parece cansativa.",
                "domain": "Saúde",
                "domain_color": "#5a9e7c",
                "options": ["Deixa a prática para lá e assiste televisão", "Obriga-se a caminhar ou escrever um pouco mesmo sem vontade"]
            }
        ],
        "mosaic_icons": {
            "left": "❌",
            "right": "🔄"
        }
    },
    "observar": {
        "id": "observar",
        "title": "Capacidade de se observar",
        "force_pair": ["Envolver", "Distanciar"],
        "scenes": [
            {
                "text": "Você se vê no meio de uma discussão acalorada sobre política no almoço de domingo.",
                "domain": "Família",
                "domain_color": "#c4956a",
                "options": ["Argumenta com paixão, sentindo a raiva subir no peito", "Presta atenção em como sua própria respiração ficou curta e decide desacelerar"]
            },
            {
                "text": "O prazo de uma entrega importante se aproxima e o pânico começa a se instalar.",
                "domain": "Trabalho",
                "domain_color": "#4a6fa5",
                "options": ["Deixa-se engolir pelo desespero e trabalha de forma caótica", "Para e anota mentalmente: 'Estou sentindo ansiedade. É só um padrão'"]
            },
            {
                "text": "Ao receber um elogio sincero de alguém de quem você gosta, você sente uma pontada de desconfiança imediata.",
                "domain": "Relação",
                "domain_color": "#b06e8a",
                "options": ["Recusa o elogio mentalmente achando que a pessoa quer algo", "Nota seu desconforto com a validação alheia e investiga a origem disso"]
            }
        ],
        "mosaic_icons": {
            "left": "🌀",
            "right": "👁️"
        }
    },
    "raizes": {
        "id": "raizes",
        "title": "Raízes culturais",
        "force_pair": ["Manter", "Questionar"],
        "scenes": [
            {
                "text": "Sua família tradicional exige sua presença em um ritual religioso com o qual você já não se identifica.",
                "domain": "Família",
                "domain_color": "#c4956a",
                "options": ["Comparece ao evento para manter a paz e a tradição", "Comunica educadamente que prefere não ir, mantendo sua coerência"]
            },
            {
                "text": "No ambiente profissional, piadas ou expressões preconceituosas arraigadas na cultura local são ditas.",
                "domain": "Trabalho",
                "domain_color": "#4a6fa5",
                "options": ["Fica calado ou sorri amarelo para não ser o chato do grupo", "Pontua firmemente que a piada ou termo não é aceitável hoje"]
            },
            {
                "text": "Você se depara com a oportunidade de se mudar para o exterior, sabendo que isso exigirá abandonar costumes queridos.",
                "domain": "Social",
                "domain_color": "#5a9e9e",
                "options": ["Recusa a oportunidade para manter-se fiel à sua terra e comunidade", "Aceita o desafio, disposto a questionar e reconstruir seus hábitos"]
            }
        ],
        "mosaic_icons": {
            "left": "🪵",
            "right": "🌱"
        }
    },
    "comunicacao": {
        "id": "comunicacao",
        "title": "Jeito de se comunicar",
        "force_pair": ["Silenciar", "Expressar"],
        "scenes": [
            {
                "text": "Seu parceiro(a) faz um comentário desagradável e você se sente chateado com o tom usado.",
                "domain": "Relação",
                "domain_color": "#b06e8a",
                "options": ["Fica em silêncio e espera a chateação passar sozinha", "Diz claramente: 'O modo como falou agora me machucou'"]
            },
            {
                "text": "Em uma reunião de condomínio, uma decisão arbitrária é tomada e você discorda totalmente da resolução.",
                "domain": "Social",
                "domain_color": "#5a9e9e",
                "options": ["Guarda a discordância para si, evitando atritos públicos", "Ergue a mão e manifesta seu argumento contra a decisão"]
            },
            {
                "text": "Você percebe um erro na planilha financeira apresentada por um colega na empresa.",
                "domain": "Trabalho",
                "domain_color": "#4a6fa5",
                "options": ["Deixa que outra pessoa note ou resolve ignorar", "Chama o colega reservadamente e aponta o desvio com respeito"]
            }
        ],
        "mosaic_icons": {
            "left": "🤐",
            "right": "📢"
        }
    },
    "historias": {
        "id": "historias",
        "title": "Histórias que te formaram",
        "force_pair": ["Repetir", "Transformar"],
        "scenes": [
            {
                "text": "Seu filho(a) ou companheiro(a) comete um erro bobo e você sente o impulso de reagir com os mesmos gritos que ouvia do seu pai.",
                "domain": "Família",
                "domain_color": "#c4956a",
                "options": ["Solta o grito na hora, repetindo o padrão de criação", "Respira fundo, rompe o impulso e conversa em tom calmo"]
            },
            {
                "text": "Em um novo cargo de liderança, você enfrenta o desafio de delegar tarefas, mas sempre ouviu que 'se quer bem feito, faça você mesmo'.",
                "domain": "Trabalho",
                "domain_color": "#4a6fa5",
                "options": ["Centraliza tudo em si mesmo, esgotando sua energia", "Confia na equipe, treina os outros e aprende a delegar responsabilidades"]
            },
            {
                "text": "Diante de um término de relacionamento, você se vê querendo se isolar totalmente para não sofrer, como sempre fez.",
                "domain": "Relação",
                "domain_color": "#b06e8a",
                "options": ["Fecha as portas para os amigos e entra em isolamento severo", "Procura sua rede de apoio e se permite ser acolhido na dor"]
            }
        ],
        "mosaic_icons": {
            "left": "🔁",
            "right": "🦋"
        }
    },
    "lacos": {
        "id": "lacos",
        "title": "Laços que te sustentam",
        "force_pair": ["Aproximar", "Distanciar"],
        "scenes": [
            {
                "text": "Você está passando por um momento de grande tristeza pessoal e seus amigos te chamam para conversar.",
                "domain": "Social",
                "domain_color": "#5a9e9e",
                "options": ["Desabafa e aceita o convite deles para desanuviar a mente", "Diz que está ocupado e prefere lidar com a tristeza sozinho"]
            },
            {
                "text": "Um familiar próximo começa a exigir mais atenção sua no momento em que você está focado em sua carreira.",
                "domain": "Família",
                "domain_color": "#c4956a",
                "options": ["Abre espaço na agenda para jantar com o familiar com frequência", "Explica que precisa de foco agora e reduz as visitas temporariamente"]
            },
            {
                "text": "Seu parceiro(a) propõe um final de semana inteiro colados, mas você queria um tempo sozinho para ler e refletir.",
                "domain": "Relação",
                "domain_color": "#b06e8a",
                "options": ["Cede ao convite para ficarem juntos o tempo todo", "Explica seu desejo de solidão temporária e agenda o encontro depois"]
            }
        ],
        "mosaic_icons": {
            "left": "🫂",
            "right": "🚪"
        }
    },
    "valores": {
        "id": "valores",
        "title": "Valores que te guiam",
        "force_pair": ["Comprometer", "Flexibilizar"],
        "scenes": [
            {
                "text": "Seu superior no trabalho pede que você use um atalho ético duvidoso para garantir um contrato vital.",
                "domain": "Trabalho",
                "domain_color": "#4a6fa5",
                "options": ["Recusa-se terminantemente a fazê-lo, assumindo o risco de demissão", "Ajusta o processo de forma sutil justificando que o resultado justifica o meio"]
            },
            {
                "text": "Você prometeu estar presente na apresentação escolar do seu filho, mas uma oportunidade profissional única surge na mesma hora.",
                "domain": "Família",
                "domain_color": "#c4956a",
                "options": ["Mantém o compromisso com a família e recusa o evento profissional", "Negocia com a família explicando o valor estratégico de comparecer ao evento"]
            },
            {
                "text": "Um amigo íntimo pede que você minta para encobrir uma traição dele no relacionamento.",
                "domain": "Relação",
                "domain_color": "#b06e8a",
                "options": ["Recusa mentir afirmando que a honestidade está acima de tudo", "Inventa uma desculpa simples para proteger o amigo e a amizade"]
            }
        ],
        "mosaic_icons": {
            "left": "💎",
            "right": "🎋"
        }
    },
    "feedbacks": {
        "id": "feedbacks",
        "title": "O que os outros te dizem",
        "force_pair": ["Acolher", "Questionar"],
        "scenes": [
            {
                "text": "Seu chefe aponta que suas apresentações de resultados costumam ser confusas ou prolixas.",
                "domain": "Trabalho",
                "domain_color": "#4a6fa5",
                "options": ["Agradece a crítica e começa a estudar técnicas de síntese", "Reflete se a crítica faz sentido ou se é apenas uma preferência pessoal dele"]
            },
            {
                "text": "Seu parceiro(a) diz que você anda muito egoísta nas decisões cotidianas do casal.",
                "domain": "Relação",
                "domain_color": "#b06e8a",
                "options": ["Pede desculpas sinceras e se propõe a mudar de postura", "Pede exemplos concretos e avalia se a crítica não é exagerada"]
            },
            {
                "text": "Um amigo comenta que você sempre desaparece quando a vida dele fica difícil.",
                "domain": "Social",
                "domain_color": "#5a9e9e",
                "options": ["Reconhece sua falha na amizade e se faz mais presente", "Explica suas próprias limitações e questiona a cobrança dele"]
            }
        ],
        "mosaic_icons": {
            "left": "📥",
            "right": "🔍"
        }
    },
    "apego": {
        "id": "apego",
        "title": "Como você se apega",
        "force_pair": ["Anexar", "Libertar"],
        "scenes": [
            {
                "text": "Seu namorado(a) avisa que vai fazer uma viagem curta com amigos e você sente insegurança.",
                "domain": "Relação",
                "domain_color": "#b06e8a",
                "options": ["Telefona e manda mensagens a cada poucas horas para saber como está", "Deseja boa viagem e foca em suas próprias atividades do final de semana"]
            },
            {
                "text": "Um colega querido de equipe anuncia que vai pedir demissão para trabalhar na concorrência.",
                "domain": "Trabalho",
                "domain_color": "#4a6fa5",
                "options": ["Tenta convencê-lo a ficar apelando para o lado emocional", "Dá os parabéns pela oportunidade e ajuda na transição do cargo"]
            },
            {
                "text": "Seu melhor amigo de infância fez novos círculos sociais e agora convida você com menos frequência.",
                "domain": "Social",
                "domain_color": "#5a9e9e",
                "options": ["Sente ciúmes e se afasta cobrando reciprocidade dele", "Compreende que os círculos mudam e mantém o afeto livre de cobranças"]
            }
        ],
        "mosaic_icons": {
            "left": "⚓",
            "right": "🎈"
        }
    },
    "modelos_afeto": {
        "id": "modelos_afeto",
        "title": "Modelos de afeto que repete",
        "force_pair": ["Repetir", "Diversificar"],
        "scenes": [
            {
                "text": "Você se percebe atraído por alguém que é indisponível emocionalmente, repetindo o histórico dos seus últimos namoros.",
                "domain": "Relação",
                "domain_color": "#b06e8a",
                "options": ["Investe na conquista tentando 'salvar' a pessoa e mudar a situação", "Decide dar um passo atrás e buscar alguém pronto para um vínculo saudável"]
            },
            {
                "text": "Seus pais demonstravam afeto apenas por cobrança de desempenho escolar. Diante de um erro de um familiar próximo, você quer cobrar duramente.",
                "domain": "Família",
                "domain_color": "#c4956a",
                "options": ["Exige a perfeição e critica o erro severamente na conversa", "Demonstra acolhimento na falha, oferecendo suporte em vez de cobrança"]
            },
            {
                "text": "No ambiente social, você sempre assume o papel de 'cuidador' que escuta a todos, mas nunca expõe suas dores.",
                "domain": "Social",
                "domain_color": "#5a9e9e",
                "options": ["Continua apenas escutando e guardando seus problemas no peito", "Arrisca-se a compartilhar algo íntimo e pede apoio ativo aos amigos"]
            }
        ],
        "mosaic_icons": {
            "left": "🔄",
            "right": "✨"
        }
    },
    "habilidades_sociais": {
        "id": "habilidades_sociais",
        "title": "Habilidades com pessoas",
        "force_pair": ["Recuar", "Avançar"],
        "scenes": [
            {
                "text": "Você chega a um evento profissional com dezenas de pessoas desconhecidas conversando em grupos.",
                "domain": "Trabalho",
                "domain_color": "#4a6fa5",
                "options": ["Fica perto do buffet mexendo no celular de forma discreta", "Aproxima-se de uma roda de conversa puxando assunto amigável"]
            },
            {
                "text": "Um desentendimento bobo no trânsito ou no caixa do mercado gera uma discussão exaltada por parte do outro.",
                "domain": "Social",
                "domain_color": "#5a9e9e",
                "options": ["Pede desculpas e aceita a queixa calado para encerrar o atrito", "Posiciona-se com clareza mantendo o tom firme sem entrar na agressão"]
            },
            {
                "text": "Sua equipe precisa de um voluntário para liderar uma apresentação importante para o cliente.",
                "domain": "Trabalho",
                "domain_color": "#4a6fa5",
                "options": ["Espera que outro colega se candidate primeiro", "Levanta a mão na hora e assume a responsabilidade da liderança"]
            }
        ],
        "mosaic_icons": {
            "left": "🛡️",
            "right": "🚀"
        }
    },
    "idiomas": {
        "id": "idiomas",
        "title": "Idiomas que você fala",
        "force_pair": ["Aprisionar", "Expandir"],
        "scenes": [
            {
                "text": "Em um jantar com conhecidos estrangeiros, todos começam a falar inglês e você teme errar a pronúncia.",
                "domain": "Social",
                "domain_color": "#5a9e9e",
                "options": ["Prefere ficar em silêncio ou falar apenas o mínimo necessário", "Arrisca-se a conversar com erros mesmo, priorizando a conexão"]
            },
            {
                "text": "Sua empresa abre vagas para um projeto internacional que exige comunicação diária em outra língua.",
                "domain": "Trabalho",
                "domain_color": "#4a6fa5",
                "options": ["Evita se candidatar com receio de não estar pronto", "Candidata-se à vaga aceitando o desafio como aprendizado prático"]
            },
            {
                "text": "Você está consumindo conteúdo na internet e se depara com um artigo técnico complexo e valioso em um idioma que estuda.",
                "domain": "Criatividade",
                "domain_color": "#7a5a9e",
                "options": ["Procura a tradução automática rápida na tela", "Lê o artigo original devagar anotando os termos novos"]
            }
        ],
        "mosaic_icons": {
            "left": "🔒",
            "right": "🔑"
        }
    },
    "rituais": {
        "id": "rituais",
        "title": "Rituais que você vive",
        "force_pair": ["Abandonar", "Criar"],
        "scenes": [
            {
                "text": "Você mudou-se de cidade e o natal está chegando. As festividades antigas parecem inacessíveis agora.",
                "domain": "Família",
                "domain_color": "#c4956a",
                "options": ["Deixa a data passar em branco sem decorações ou celebrações", "Organiza um pequeno jantar adaptado ou rito novo para marcar a data"]
            },
            {
                "text": "A correria do dia a dia fez com que o hábito de jantar à mesa em família fosse substituído por refeições rápidas no celular.",
                "domain": "Família",
                "domain_color": "#c4956a",
                "options": ["Aceita o hábito prático de comer rápido no sofá", "Estabelece a regra de refeição conjunta à mesa aos domingos"]
            },
            {
                "text": "Você concluiu um projeto acadêmico ou profissional importante após meses de esforço intenso.",
                "domain": "Trabalho",
                "domain_color": "#4a6fa5",
                "options": ["Emenda imediatamente no próximo trabalho sem celebrar", "Tira o dia para fazer um brinde ou ritual pessoal de comemoração"]
            }
        ],
        "mosaic_icons": {
            "left": "🍂",
            "right": "🕯️"
        }
    },
    "comportamento": {
        "id": "comportamento",
        "title": "Jeito de se comportar",
        "force_pair": ["Autêntico", "Adaptado"],
        "scenes": [
            {
                "text": "Em uma roda de amigos íntimos, o grupo começa a adotar uma opinião polêmica com a qual você discorda intimamente.",
                "domain": "Social",
                "domain_color": "#5a9e9e",
                "options": ["Manifesta sua discordância claramente assumindo sua posição singular", "Concorda superficialmente ou muda de assunto para não parecer discordante"]
            },
            {
                "text": "Você está em um coquetel corporativo formal cercado por diretores importantes do setor.",
                "domain": "Trabalho",
                "domain_color": "#4a6fa5",
                "options": ["Brinca e fala sobre seus reais interesses de forma espontânea", "Policia cada gesto e assunto para projetar uma imagem ideal de sobriedade"]
            },
            {
                "text": "Durante uma discussão conjugal ou familiar, você sente vontade de chorar diante de um argumento difícil.",
                "domain": "Relação",
                "domain_color": "#b06e8a",
                "options": ["Chora abertamente, demonstrando sua vulnerabilidade sem filtros", "Prende o choro e endurece a voz para não demonstrar fraqueza"]
            }
        ],
        "mosaic_icons": {
            "left": "👤",
            "right": "🎭"
        }
    },
    "marcos_identidade": {
        "id": "marcos_identidade",
        "title": "Marcos da sua identidade",
        "force_pair": ["Apegar", "Soltar"],
        "scenes": [
            {
                "text": "Você se aposentou ou mudou radicalmente de carreira recentemente, mas as pessoas ainda te cobram a antiga postura corporativa.",
                "domain": "Trabalho",
                "domain_color": "#4a6fa5",
                "options": ["Mantém os velhos cartões, termos e rotinas antigas na mente", "Apresenta-se com sua nova ocupação, aceitando a virada de página"]
            },
            {
                "text": "Uma amizade de longa data tornou-se tóxica ou distante devido a caminhos e valores incompatíveis hoje.",
                "domain": "Social",
                "domain_color": "#5a9e9e",
                "options": ["Mantém o vínculo forçado apenas pela história passada em comum", "Despede-se da amizade com gratidão, permitindo que ela faça parte do passado"]
            },
            {
                "text": "Você herdou móveis ou objetos antigos de um parente falecido que ocupam muito espaço e não combinam com sua casa.",
                "domain": "Família",
                "domain_color": "#c4956a",
                "options": ["Guarda tudo por apego à história e memória do parente", "Doa ou vende os itens guardando apenas lembranças afetivas simbólicas"]
            }
        ],
        "mosaic_icons": {
            "left": "📦",
            "right": "🌊"
        }
    },
    "emocoes": {
        "id": "emocoes",
        "title": "Emoções que expressa",
        "force_pair": ["Contêr", "Liberar"],
        "scenes": [
            {
                "text": "Você sente uma raiva imensa ao ver um serviço público ou privado ser mal executado na sua frente.",
                "domain": "Conflito",
                "domain_color": "#c75a5a",
                "options": ["Engole a raiva e se retira fingindo tranquilidade", "Reclama com firmeza e expressa sua indignação aos responsáveis"]
            },
            {
                "text": "Um amigo querido prepara uma surpresa comovente para celebrar uma conquista sua.",
                "domain": "Social",
                "domain_color": "#5a9e9e",
                "options": ["Contém o choro e agradece de maneira contida e polida", "Chora, abraça o amigo e demonstra alegria intensa sem reservas"]
            },
            {
                "text": "Você se sente extremamente triste e vulnerável após um dia repleto de frustrações pessoais.",
                "domain": "Saúde",
                "domain_color": "#5a9e7c",
                "options": ["Guarda a tristeza para si e assiste a um filme para se distrair", "Permite-se chorar no quarto até aliviar o peso interno"]
            }
        ],
        "mosaic_icons": {
            "left": "🤐",
            "right": "🌋"
        }
    },
    "lidar_emocoes": {
        "id": "lidar_emocoes",
        "title": "Como lida com emoções",
        "force_pair": ["Evitar", "Regular"],
        "scenes": [
            {
                "text": "Uma onda intensa de ansiedade surge logo antes de você entrar em uma reunião com a diretoria.",
                "domain": "Trabalho",
                "domain_color": "#4a6fa5",
                "options": ["Tenta focar obstinadamente na apresentação para 'esquecer' a ansiedade", "Para por 2 minutos, foca na expiração lenta e acalma o sistema nervoso"]
            },
            {
                "text": "Você sente frustração severa após uma conversa tensa com seu parceiro(a).",
                "domain": "Relação",
                "domain_color": "#b06e8a",
                "options": ["Sai de casa para beber ou fazer compras buscando alívio rápido", "Senta-se em silêncio investigando de onde vem tanta frustração e raiva"]
            },
            {
                "text": "O acúmulo de cobranças familiares te deixa à beira de um colapso nervoso de estresse.",
                "domain": "Família",
                "domain_color": "#c4956a",
                "options": ["Continua agindo no automático ignorando a exaustão iminente", "Cancela compromissos não vitais para dormir e repousar a mente"]
            }
        ],
        "mosaic_icons": {
            "left": "🛡️",
            "right": "🔧"
        }
    },
    "habitos": {
        "id": "habitos",
        "title": "Hábitos do dia a dia",
        "force_pair": ["Automatizar", "Deliberar"],
        "scenes": [
            {
                "text": "Seu alarme toca de manhã e o celular já está ao lado da cama pronto para ser checado.",
                "domain": "Saúde",
                "domain_color": "#5a9e7c",
                "options": ["Abre as redes sociais por reflexo mecânico e fica 30 minutos na cama", "Levanta-se imediatamente sem olhar as notificações para meditar ou alongar"]
            },
            {
                "text": "No trabalho, ao terminar uma tarefa, você sente o impulso automático de abrir abas de notícias.",
                "domain": "Trabalho",
                "domain_color": "#4a6fa5",
                "options": ["Navega por reflexo dispersando seu foco sem notar o tempo", "Para e escolhe conscientemente beber água ou respirar na janela"]
            },
            {
                "text": "Antes de dormir, você costuma ligar a TV para pegar no sono, mesmo sabendo que acorda cansado.",
                "domain": "Saúde",
                "domain_color": "#5a9e7c",
                "options": ["Mantém a TV ligada no automático para não encarar o silêncio", "Desliga todas as telas 1 hora antes e lê um livro físico à luz suave"]
            }
        ],
        "mosaic_icons": {
            "left": "🤖",
            "right": "🧠"
        }
    },
    "saude": {
        "id": "saude",
        "title": "Como está sua saúde",
        "force_pair": ["Cuidar", "Negligenciar"],
        "scenes": [
            {
                "text": "Você sente uma dor nas costas persistente há duas semanas que atrapalha seu sono.",
                "domain": "Saúde",
                "domain_color": "#5a9e7c",
                "options": ["Marca uma consulta médica ou fisioterapia para investigar", "Continua trabalhando tomando anti-inflamatórios por conta própria"]
            },
            {
                "text": "O cansaço mental do trabalho está altíssimo e você sente sintomas leves de Burnout.",
                "domain": "Trabalho",
                "domain_color": "#4a6fa5",
                "options": ["Reduz o ritmo, conversa com a gestão e estabelece limites", "Aumenta as horas de entrega achando que é apenas preguiça passageira"]
            },
            {
                "text": "Durante as refeições diárias, você se vê devorando comida rápida enquanto responde mensagens no celular.",
                "domain": "Saúde",
                "domain_color": "#5a9e7c",
                "options": ["Desliga o celular e mastiga devagar saboreando a refeição", "Come com pressa de forma mecânica para voltar rápido ao trabalho"]
            }
        ],
        "mosaic_icons": {
            "left": "❤️",
            "right": "⚠️"
        }
    },
    "decide": {
        "id": "decide",
        "title": "Como decide",
        "force_pair": ["Hesitar", "Agir"],
        "scenes": [
            {
                "text": "Você precisa escolher o destino das suas férias e tem três opções atraentes na mesa.",
                "domain": "Criatividade",
                "domain_color": "#7a5a9e",
                "options": ["Pesquisa semanas, faz planilhas comparativas e adia a compra", "Escolhe uma opção razoável no mesmo dia e faz a reserva imediata"]
            },
            {
                "text": "Uma oportunidade de investimento financeiro interessante surge com prazo curto de adesão.",
                "domain": "Finanças",
                "domain_color": "#c4a55a",
                "options": ["Analisa os riscos longamente perdendo o prazo de fechamento", "Toma a decisão com base nas informações que já possui no momento"]
            },
            {
                "text": "Você precisa resolver se aceita um convite de casamento no mesmo dia de outro compromisso.",
                "domain": "Social",
                "domain_color": "#5a9e9e",
                "options": ["Fica postergando a resposta para não chatear nenhum dos lados", "Responde recusando um dos convites com transparência imediata"]
            }
        ],
        "mosaic_icons": {
            "left": "❓",
            "right": "🎯"
        }
    },
    "metacognicao": {
        "id": "metacognicao",
        "title": "Como pensa sobre pensar",
        "force_pair": ["Ruminar", "Soltar"],
        "scenes": [
            {
                "text": "Você cometeu um pequeno equívoco verbal em uma apresentação com clientes hoje.",
                "domain": "Trabalho",
                "domain_color": "#4a6fa5",
                "options": ["Passa a noite repassando a cena na mente pensando no que deveria ter dito", "Aceita o deslize como humano e foca em suas tarefas da noite"]
            },
            {
                "text": "Um familiar fez uma crítica sutil à sua aparência durante o almoço de domingo.",
                "domain": "Família",
                "domain_color": "#c4956a",
                "options": ["Fica horas tentando adivinhar as segundas intenções por trás do comentário", "Decide que a opinião do outro não te define e esquece o comentário"]
            },
            {
                "text": "Ao tomar uma decisão importante de vida, você começa a conjecturar dezenas de cenários ruins.",
                "domain": "Saúde",
                "domain_color": "#5a9e7c",
                "options": ["Deixa-se arrastar pelo redemoinho mental de preocupações", "Reconhece o excesso de pensamentos e foca nos fatos do presente"]
            }
        ],
        "mosaic_icons": {
            "left": "🔁",
            "right": "🍃"
        }
    }
}

async def get_oc_summary(conversation_id: str, oc_id: str, pool) -> dict:
    """Recupera o estado do OC e constrói um resumo textual."""
    if not pool or not conversation_id:
        return None
    
    try:
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT choices, completed FROM oc_sessions WHERE conversation_id = $1 AND oc_id = $2 ORDER BY id DESC LIMIT 1",
                conversation_id, oc_id
            )
            if not row or not row["completed"]:
                return None
            
            choices = json.loads(row["choices"]) if isinstance(row["choices"], str) else row["choices"]
            config = OC_CONFIGS.get(oc_id, {})
            scenes = config.get("scenes", [])
            
            parts = []
            for i, choice in enumerate(choices):
                if i < len(scenes):
                    domain = scenes[i]["domain"]
                    option = scenes[i]["options"][choice] if choice < len(scenes[i]["options"]) else "?"
                    force = config["force_pair"][choice] if choice < len(config["force_pair"]) else "?"
                    parts.append(f"em {domain}: {force} ({option})")
            
            summary = "; ".join(parts)
            
            return {
                "title": config.get("title", oc_id),
                "choices": choices,
                "summary": summary
            }
    except Exception as e:
        logger.error(f"Erro ao recuperar resumo do OC: {e}")
        return None


def detect_card_triggers(text: str, current_triggered: set) -> list:
    text = text.lower()
    newly_triggered = []
    
    # 1. Verifica os 27 objetos (mapeados no dicionário)
    for card_id, metadata in OBJECTS_METADATA.items():
        if card_id not in current_triggered:
            if any(kw in text for kw in metadata["keywords"]):
                current_triggered.add(card_id)
                newly_triggered.append({
                    "type": "card",
                    "id": card_id,
                    "title": metadata["title"],
                    "icon": metadata["icon"],
                    "foyer": metadata["foyer"],
                    "text": metadata["text"],
                    "status": "novo"
                })
                
    # 2. Verifica conexões dinâmicas entre objetos ativados
    conexoes = [
        # Conexões Interne ↔ Interne
        {"id": "conexao_limites_conflito", "cards": ["limites", "conflito"],
         "text": "Seus LIMITES pessoais aparecem com força nos momentos de CONFLITO."},
        {"id": "conexao_sensacoes_ritmos", "cards": ["sensacoes", "ritmos"],
         "text": "Seu corpo fala: as SENSAÇÕES físicas seguem os RITMOS internos que você cultiva."},
        {"id": "conexao_reacoes_dependencias", "cards": ["reacoes", "dependencias"],
         "text": "As REAÇÕES que se repetem estão ligadas às DEPENDÊNCIAS emocionais que te prendem."},
        # Conexões Interne ↔ Externe
        {"id": "conexao_limites_historias", "cards": ["limites", "historias"],
         "text": "Seus LIMITES de hoje têm raízes nas HISTÓRIAS que te formaram."},
        {"id": "conexao_limites_raizes", "cards": ["limites", "raizes"],
         "text": "Os LIMITES que você reconhece dialogam com suas RAÍZES culturais."},
        {"id": "conexao_conflito_comunicacao", "cards": ["conflito", "comunicacao"],
         "text": "Seu jeito de entrar em CONFLITO reflete seu estilo de COMUNICAÇÃO."},
        {"id": "conexao_dependencias_apego", "cards": ["dependencias", "apego"],
         "text": "Suas DEPENDÊNCIAS emocionais ecoam no seu estilo de APEGO nas relações."},
        {"id": "conexao_dependencias_modelos", "cards": ["dependencias", "modelos_afeto"],
         "text": "As DEPENDÊNCIAS que te prendem reproduzem MODELOS DE AFETO que você aprendeu."},
        {"id": "conexao_praticas_observar", "cards": ["praticas", "observar"],
         "text": "Suas PRÁTICAS reflexivas fortalecem sua CAPACIDADE DE SE OBSERVAR."},
        {"id": "conexao_reacoes_feedbacks", "cards": ["reacoes", "feedbacks"],
         "text": "As REAÇÕES que você descreve batem com o que os OUTROS TE DIZEM sobre você."},
        # Conexões Externe ↔ Externe
        {"id": "conexao_historias_marcos", "cards": ["historias", "marcos_identidade"],
         "text": "Suas HISTÓRIAS de vida contêm os MARCOS que definem sua identidade."},
        {"id": "conexao_lacos_apego", "cards": ["lacos", "apego"],
         "text": "Os LAÇOS que te sustentam revelam seu estilo de APEGO nas relações."},
        {"id": "conexao_lacos_habilidades", "cards": ["lacos", "habilidades_sociais"],
         "text": "Seus LAÇOS são sustentados pelas HABILIDADES SOCIAIS que você desenvolveu."},
        {"id": "conexao_comunicacao_habilidades", "cards": ["comunicacao", "habilidades_sociais"],
         "text": "Seu jeito de se COMUNICAR é a base das suas HABILIDADES com pessoas."},
        {"id": "conexao_valores_comportamento", "cards": ["valores", "comportamento"],
         "text": "Os VALORES que te guiam se manifestam no seu JEITO DE SE COMPORTAR socialmente."},
        {"id": "conexao_valores_marcos", "cards": ["valores", "marcos_identidade"],
         "text": "Seus VALORES foram forjados nos MARCOS que definiram sua trajetória."},
        {"id": "conexao_raizes_rituais", "cards": ["raizes", "rituais"],
         "text": "Suas RAÍZES culturais se expressam nos RITUAIS que você vive."},
        # Conexões Interne ↔ Stratégique
        {"id": "conexao_ritmos_habitos", "cards": ["ritmos", "habitos"],
         "text": "A regulação dos seus RITMOS corporais depende dos HÁBITOS que você cultiva."},
        {"id": "conexao_conflito_lidar", "cards": ["conflito", "lidar_emocoes"],
         "text": "Seu jeito de entrar em CONFLITO revela COMO VOCÊ LIDA COM AS EMOÇÕES."},
        {"id": "conexao_sensacoes_saude", "cards": ["sensacoes", "saude"],
         "text": "As SENSAÇÕES do seu corpo são indicadores diretos de COMO ESTÁ SUA SAÚDE."},
        {"id": "conexao_observar_metacognicao", "cards": ["observar", "metacognicao"],
         "text": "Sua CAPACIDADE DE SE OBSERVAR alimenta COMO VOCÊ PENSA SOBRE PENSAR."},
        # Conexões Externe ↔ Stratégique
        {"id": "conexao_historias_decide", "cards": ["historias", "decide"],
         "text": "As HISTÓRIAS que te formaram influenciam COMO VOCÊ DECIDE hoje."},
        {"id": "conexao_valores_decide", "cards": ["valores", "decide"],
         "text": "Os VALORES que te guiam determinam COMO VOCÊ DECIDE nas encruzilhadas."},
        {"id": "conexao_comportamento_emocoes", "cards": ["comportamento", "emocoes"],
         "text": "Seu JEITO DE SE COMPORTAR socialmente molda as EMOÇÕES QUE VOCÊ EXPRESSA."},
        {"id": "conexao_marcos_lidar", "cards": ["marcos_identidade", "lidar_emocoes"],
         "text": "Os MARCOS da sua identidade definiram COMO VOCÊ LIDA COM AS EMOÇÕES."},
    ]
    
    for conn in conexoes:
        if conn["id"] not in current_triggered:
            if all(c in current_triggered for c in conn["cards"]):
                current_triggered.add(conn["id"])
                newly_triggered.append({
                    "type": "connection",
                    "id": conn["id"],
                    "title": "CONEXÃO DESCOBERTA",
                    "icon": "🔗",
                    "foyer": "connection",
                    "text": conn["text"],
                    "status": "novo"
                })
                
    # 3. Verifica Saltos (Sauts d'Évolution) — progressivos conforme objetos ativados
    saut_keywords = ["percebi", "entendi que", "agora posso", "vou mudar", "consegui", "mudei",
                     "comecei a", "ficou claro", "percepção", "mudou", "transformou", "nunca mais",
                     "decidi que", "a partir de agora", "aprendi que"]
    object_count = len([c for c in current_triggered if c in OBJECTS_METADATA])
    
    if "saut_evolution" not in current_triggered:
        if any(kw in text for kw in saut_keywords) and object_count > 0:
            current_triggered.add("saut_evolution")
            saut_texts = [
                "Você percebeu algo novo e conectou pontos antes dispersos da sua experiência.",
                "Um salto de clareza: você está transformando observação em compreensão ativa.",
                "Algo mudou na sua percepção. Esse é um momento de evolução pessoal genuíno.",
            ]
            newly_triggered.append({
                "type": "saut",
                "id": "saut_evolution",
                "title": "SALTO EVOLUTIVO",
                "icon": "✨",
                "foyer": "saut",
                "text": random.choice(saut_texts),
                "status": "novo"
            })
                
    # 4. Verifica Reflexões progressivas (conforme número de objetos ativados)
    if object_count >= 2 and "reflexao_2" not in current_triggered:
        current_triggered.add("reflexao_2")
        newly_triggered.append({
            "type": "reflexao",
            "id": "reflexao_2",
            "title": "PARA LEVAR",
            "icon": "📝",
            "foyer": "reflexao",
            "text": "Você já mapeou dois temas importantes. O que esses temas revelam sobre seus padrões?",
            "status": "novo"
        })
    elif object_count >= 5 and "reflexao_5" not in current_triggered:
        current_triggered.add("reflexao_5")
        newly_triggered.append({
            "type": "reflexao",
            "id": "reflexao_5",
            "title": "PARA LEVAR",
            "icon": "📝",
            "foyer": "reflexao",
            "text": "Cinco temas já emergiram. Como seria sua vida se você equilibrasse essas dimensões?",
            "status": "novo"
        })
    elif object_count >= 10 and "reflexao_10" not in current_triggered:
        current_triggered.add("reflexao_10")
        newly_triggered.append({
            "type": "reflexao",
            "id": "reflexao_10",
            "title": "PARA LEVAR",
            "icon": "📝",
            "foyer": "reflexao",
            "text": "Dez temas mapeados. Você está construindo uma cartografia rica da sua singularidade.",
            "status": "novo"
        })
            
    return newly_triggered

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Conexão com o banco de dados PostgreSQL
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        # Fallback local se não configurado
        database_url = "postgresql://eliza:Eliza2026DB!@localhost:5432/eliza"
        
    app.state.db_pool = None
    try:
        # O driver asyncpg necessita do prefixo postgresql:// puro
        connection_url = database_url.replace("postgresql+asyncpg://", "postgresql://")
        logger.info(f"Conectando ao banco de dados: {connection_url}")
        pool = await asyncpg.create_pool(connection_url)
        app.state.db_pool = pool
        logger.info("Conexão ao PostgreSQL realizada com sucesso.")
        
        # Inicializa a tabela se não existir
        async with pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id SERIAL PRIMARY KEY,
                    conversation_id VARCHAR(100) NOT NULL,
                    role VARCHAR(20) NOT NULL,
                    content TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON messages(conversation_id);
            """)
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS oc_sessions (
                    id SERIAL PRIMARY KEY,
                    conversation_id VARCHAR(100) NOT NULL,
                    oc_id VARCHAR(50) NOT NULL,
                    scene_index INTEGER DEFAULT 0,
                    choices JSONB DEFAULT '[]',
                    completed BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                CREATE INDEX IF NOT EXISTS idx_oc_sessions_conversation 
                    ON oc_sessions(conversation_id, oc_id);
            """)
            logger.info("Tabela de mensagens verificada/criada.")
    except Exception as e:
        logger.warning(f"Erro ao inicializar banco de dados: {e}. Executando com histórico em memória.")
        
    yield
    
    # Encerra pool de conexões
    if app.state.db_pool:
        await app.state.db_pool.close()
        logger.info("Pool de conexões com o banco encerrado.")

app = FastAPI(title="ELIZA 2026", lifespan=lifespan)

def build_cors_origins() -> list[str]:
    raw_origins = os.getenv("CORS_ORIGINS", "")
    if raw_origins.strip():
        return [origin.strip() for origin in raw_origins.split(",") if origin.strip()]

    origins = [
        "https://autoconhecer.netlify.app",
        "https://eliza.mdh-hability.com",
    ]
    if os.getenv("ENVIRONMENT", "").lower() != "production":
        origins.extend([
            "http://localhost:3000",
            "http://localhost:4173",
            "http://localhost:8001",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:4173",
            "http://127.0.0.1:8001",
        ])
    return origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=build_cors_origins(),
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def get_index():
    return FileResponse("index.html")

@app.get("/style.css")
async def get_css():
    return FileResponse("style.css")

@app.get("/app.js")
async def get_js():
    return FileResponse("app.js")

# --- Endpoints dos OCs (Objetos de Conhecimento) ---

@app.get("/oc/config/{oc_id}")
async def get_oc_config(oc_id: str):
    config = OC_CONFIGS.get(oc_id)
    if not config:
        return {"error": "OC não encontrado"}
    return {"id": oc_id, **config}

@app.get("/oc/state/{conversation_id}/{oc_id}")
async def get_oc_state(conversation_id: str, oc_id: str, request: Request):
    pool = request.app.state.db_pool
    if not pool:
        return {"scene_index": 0, "choices": [], "completed": False}
    try:
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT scene_index, choices, completed FROM oc_sessions WHERE conversation_id = $1 AND oc_id = $2 ORDER BY id DESC LIMIT 1",
                conversation_id, oc_id
            )
            if row:
                return {
                    "scene_index": row["scene_index"],
                    "choices": json.loads(row["choices"]) if isinstance(row["choices"], str) else row["choices"],
                    "completed": row["completed"]
                }
    except Exception:
        pass
    return {"scene_index": 0, "choices": [], "completed": False}

@app.post("/oc/save")
async def save_oc_progress(request: Request):
    data = await request.json()
    conversation_id = data.get("conversation_id")
    oc_id = data.get("oc_id")
    scene_index = data.get("scene_index", 0)
    choices = data.get("choices", [])
    completed = data.get("completed", False)
    
    pool = request.app.state.db_pool
    if not pool:
        return {"status": "ok", "note": "sem banco de dados"}
    
    try:
        async with pool.acquire() as conn:
            await conn.execute(
                """INSERT INTO oc_sessions (conversation_id, oc_id, scene_index, choices, completed, updated_at) 
                   VALUES ($1, $2, $3, $4::jsonb, $5, CURRENT_TIMESTAMP)""",
                conversation_id, oc_id, scene_index, json.dumps(choices), completed
            )
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Erro ao salvar progresso do OC: {e}")
        return {"status": "error", "detail": str(e)}

@app.delete("/oc/reset/{conversation_id}")
async def reset_oc_sessions(conversation_id: str, request: Request):
    pool = request.app.state.db_pool
    if not pool:
        return {"status": "ok", "note": "sem banco de dados"}
    try:
        async with pool.acquire() as conn:
            await conn.execute(
                "DELETE FROM oc_sessions WHERE conversation_id = $1",
                conversation_id
            )
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Erro ao resetar OCs: {e}")
        return {"status": "error"}


async def analyze_emotion(text: str) -> str:
    text = text.lower()
    # Remove pontuação para separar palavras de forma limpa
    text_clean = re.sub(r'[^\w\s]', ' ', text)
    words_list = text_clean.split()
    
    negations = {"não", "nunca", "jamais", "nem", "sem", "nada"}
    
    keywords = {
        "sadness": ["triste", "cansado", "cansada", "exaurido", "exaurida", "desanimado", "desanimada", "chorar", "choro", "deprimido", "deprimida", "solitário", "solitária", "sozinho", "sozinha", "dor", "sofrer", "frustrado", "frustrada", "frustração", "desespero", "infeliz", "exaust"],
        "joy": ["feliz", "alegre", "ótimo", "bom", "maravilhoso", "excelente", "animado", "animada", "sorrir", "gostar", "amor", "amar", "sucesso", "consegui", "contente"],
        "anger": ["bravo", "brava", "raiva", "irritado", "irritada", "ódio", "odiar", "chateado", "chateada", "nervoso", "nervosa", "injustiça", "briga", "discussão", "futo"],
        "anxiety": ["ansioso", "ansiosa", "medo", "preocupado", "preocupada", "pânico", "angústia", "receio", "assustado", "assustada", "terror", "nervosismo", "tensão", "tenso", "tensa"]
    }
    
    for emotion, words in keywords.items():
        for word in words:
            if word in text:
                # Se a palavra-chave foi encontrada no texto, vamos inspecionar as palavras limpas
                for idx, clean_word in enumerate(words_list):
                    if word in clean_word:
                        # Verifica se há negação nas 3 posições anteriores
                        start_idx = max(0, idx - 3)
                        if any(words_list[prev_idx] in negations for prev_idx in range(start_idx, idx)):
                            # Encontrou uma negação próxima, portanto ignora esta palavra-chave
                            break
                else:
                    # Se saiu do loop sem o break (ou seja, nenhuma ocorrência foi negada), retorna a emoção
                    return emotion
            
    return "calm"

REGRAS_FALLBACK = {
    r'.*mãe.*': [
        "Fale-me mais sobre sua família.",
        "Como é sua relação com sua mãe?"
    ],
    r'.*pai.*': [
        "Me fale mais sobre seu pai.",
        "Como você se sente em relação ao seu pai?"
    ],
    r'.*estou (deprimido|triste).*': [
        "Lamento ouvir que você está {0}. O que te deixa assim?",
        "Você acha que vir aqui te ajuda a não ficar {0}?"
    ],
    r'.*eu preciso de (.*)': [
        "Por que você precisa de {0}?",
        "Isso realmente te ajudaria?"
    ],
    r'.*por que você não (.*)': [
        "Você realmente acha que eu não {0}?",
        "Talvez no devido tempo eu vá {0}."
    ],
    r'.*talvez (.*)': [
        "Você parece um pouco incerto. Por que diz isso?",
        "Você acha que isso é provável?"
    ],
    r'.*não (.*)': [
        "Por que não?",
        "Você está sendo um pouco negativo.",
        "O que te faz dizer 'não'?"
    ],
    r'(.*)': [
        "Por favor, continue.",
        "Por que você diz isso?",
        "Compreendo. Diga-me mais."
    ]
}

def fallback_responder(texto_usuario: str) -> str:
    texto_usuario = texto_usuario.lower()
    for padrao, respostas in REGRAS_FALLBACK.items():
        match = re.match(padrao, texto_usuario)
        if match:
            resposta = random.choice(respostas)
            if '{0}' in resposta and match.groups():
                return resposta.format(match.group(1))
            return resposta
    return "Compreendo. Diga-me mais sobre isso."

@app.websocket("/ws/{conversation_id}")
async def websocket_endpoint(websocket: WebSocket, conversation_id: str):
    await websocket.accept()
    
    if conversation_id in ["null", "undefined", "new"]:
        conversation_id = None
        
    pool = websocket.app.state.db_pool
    agent = OpenRouterAgent(conversation_id=conversation_id, pool=pool)
    
    # Carrega histórico existente se houver
    await agent.load_history()
    
    # Inicializa cards limpos a cada conexão — métricas partem do zero
    triggered_cards = set()
    
    # Gerenciamento de conexões concorrentes/abertura de múltiplas abas
    if agent.conversation_id:
        if agent.conversation_id in active_connections:
            old_ws = active_connections[agent.conversation_id]
            try:
                logger.info(f"Conexão concorrente detectada para sessão {agent.conversation_id}. Desconectando aba antiga.")
                await old_ws.send_json({
                    "type": "error", 
                    "content": "Sessão iniciada em outra aba. Esta aba foi desconectada para evitar conflitos."
                })
                await old_ws.close()
            except Exception as e:
                logger.warning(f"Erro ao desconectar WebSocket antigo: {e}")
        
        active_connections[agent.conversation_id] = websocket
    
    try:
        await websocket.send_json({"type": "status", "content": "connected"})
        
        while True:
            user_message = await websocket.receive_text()
            
            # Detecta retorno de um OC completado (formato JSON)
            try:
                oc_data = json.loads(user_message)
                if oc_data.get("type") == "oc_completed":
                    oc_id = oc_data.get("oc_id", "desconhecido")
                    title = oc_data.get("title", "Objeto de Conhecimento")
                    choices = oc_data.get("choices", [])
                    force_pair = oc_data.get("force_pair", [])
                    scenes = oc_data.get("scenes", [])
                    
                    # Constrói o resumo das escolhas
                    summary_parts = []
                    for i, choice in enumerate(choices):
                        if i < len(scenes) and choice < len(scenes[i].get("options", [])):
                            domain = scenes[i].get("domain", "?")
                            option = scenes[i]["options"][choice]
                            force = force_pair[choice] if choice < len(force_pair) else "?"
                            summary_parts.append(f"em {domain}: {force} ({option})")
                    
                    summary = "; ".join(summary_parts) if summary_parts else "escolhas mistas"
                    
                    oc_context = (
                        f"[O usuário acabou de explorar o autoconhecimento '{title}'.\n"
                        f"Resumo das inclinações: {summary}.\n"
                        f"Não mencione 'exercício', 'app' ou 'sistema'. Reaja naturalmente, como se tivesse percebido "
                        f"uma mudança sutil no jeito dele falar. Pergunte como ele se sente após essa reflexão.]"
                    )
                    
                    await websocket.send_json({"type": "typing", "content": True})
                    try:
                        async for token in agent.chat(oc_context):
                            await websocket.send_json({"type": "token", "content": token})
                        await websocket.send_json({"type": "typing", "content": False})
                    except Exception:
                        await websocket.send_json({"type": "typing", "content": False})
                    
                    await websocket.send_json({"type": "emotion", "content": "calm"})
                    await websocket.send_json({"type": "end"})
                    continue
            except (json.JSONDecodeError, AttributeError):
                pass  # Não é JSON, continua como mensagem normal
            
            # 1. Verifica gatilhos de cards no prompt do usuário
            user_triggers = detect_card_triggers(user_message, triggered_cards)
            for trigger in user_triggers:
                await websocket.send_json({"type": "card_trigger", "content": trigger})
            
            emotion_task = asyncio.create_task(analyze_emotion(user_message))
            
            await websocket.send_json({"type": "typing", "content": True})
            
            full_response_or_fallback = ""
            try:
                async for token in agent.chat(user_message):
                    await websocket.send_json({"type": "token", "content": token})
                    full_response_or_fallback += token
                await websocket.send_json({"type": "typing", "content": False})
            except Exception as api_err:
                logger.error(f"OpenRouter API falhou: {api_err}. Ativando fallback clássico...")
                await websocket.send_json({"type": "typing", "content": False})
                
                local_response = fallback_responder(user_message)
                full_response_or_fallback = local_response
                
                # Registra o fallback clássico no histórico e banco de dados
                await agent.add_assistant_message(local_response)
                
                for word in local_response.split(" "):
                    await websocket.send_json({"type": "token", "content": word + " "})
                    await asyncio.sleep(0.08)
            
            # Sincroniza o session_id caso tenha sido gerado um novo pelo backend
            if agent.conversation_id:
                await websocket.send_json({"type": "session_id", "content": agent.conversation_id})
            
            try:
                emotion = await emotion_task
            except Exception:
                emotion = "calm"
            
            await websocket.send_json({"type": "emotion", "content": emotion})
            await websocket.send_json({"type": "end"})
            
    except WebSocketDisconnect:
        logger.info(f"Sessão {agent.conversation_id} desconectada do WebSocket.")
    except Exception as e:
        logger.error(f"Erro no WebSocket para sessão {agent.conversation_id}: {e}")
        try:
            await websocket.send_json({"type": "error", "content": "Desculpe, ocorreu um soluço na nossa conexão. Estou aqui ouvindo você."})
        except Exception:
            pass
    finally:
        # Remove a conexão do mapeamento se for a conexão atual
        if agent.conversation_id and active_connections.get(agent.conversation_id) == websocket:
            active_connections.pop(agent.conversation_id, None)
        await agent.close()

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
