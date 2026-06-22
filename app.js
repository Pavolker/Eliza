// ==========================================================================
// APP.JS — LÓGICA DE INTERACTION ELIZA 2026
// Conexão via WebSocket, Gerenciamento de Sessão e Efeitos Atmosféricos
// ==========================================================================

document.addEventListener('DOMContentLoaded', () => {
    const chatHistory = document.getElementById('chat-history');
    const chatForm = document.getElementById('chat-form');
    const userInput = document.getElementById('user-input');
    const typingIndicator = document.getElementById('typing-indicator');
    const connectionDot = document.getElementById('connection-dot');
    const connectionText = document.getElementById('connection-text');
    
    let socket = null;
    let currentResponseElement = null;
    let reconnectTimeout = null;
    let reconnectDelay = 1000; // Começa com 1s

    // Recupera ou cria um ID de conversa persistente para o usuário
    let conversationId = localStorage.getItem('eliza_session_id') || 'new';

    // Inicializa o tema padrão como Calm
    document.body.className = 'theme-calm';

    // Backend WebSocket — servidor Hetzner via Caddy + SSL
    const ELIZA_BACKEND = 'eliza.mdh-hability.com';

    // Função de Conexão WebSocket com Reconexão Automática
    function connectWebSocket() {
        const wsUrl = `wss://${ELIZA_BACKEND}/ws/${conversationId}`;
        
        socket = new WebSocket(wsUrl);

        socket.onopen = () => {
            console.log('Conectado ao consultório da ELIZA.');
            connectionDot.className = 'connection-dot connected';
            connectionText.textContent = 'Em sintonia com você';
            reconnectDelay = 1000; // Reseta o delay
            if (reconnectTimeout) clearTimeout(reconnectTimeout);
        };

        socket.onmessage = (event) => {
            const data = JSON.parse(event.data);
            
            switch (data.type) {
                case 'status':
                    console.log('Status do servidor:', data.content);
                    break;
                    
                case 'typing':
                    if (data.content) {
                        showTypingIndicator();
                    } else {
                        hideTypingIndicator();
                    }
                    break;
                    
                case 'token':
                    // Oculta indicador de digitação no primeiro token
                    hideTypingIndicator();
                    appendToken(data.content);
                    break;
                    
                case 'emotion':
                    // Transita o fundo do aplicativo suavemente de acordo com a emoção
                    changeAtmosphere(data.content);
                    break;
                    
                case 'session_id':
                    // Sincroniza o ID persistente da conversa no cliente
                    if (conversationId !== data.content) {
                        conversationId = data.content;
                        localStorage.setItem('eliza_session_id', conversationId);
                        console.log('ID de conversa atualizado e persistido:', conversationId);
                    }
                    break;
                    
                case 'end':
                    // Finaliza a resposta atual
                    currentResponseElement = null;
                    enableInput();
                    break;
                    
                case 'error':
                    hideTypingIndicator();
                    appendErrorMessage(data.content);
                    enableInput();
                    break;
            }
        };

        socket.onclose = () => {
            console.log('Conexão fechada. Tentando reconectar...');
            connectionDot.className = 'connection-dot disconnected';
            connectionText.textContent = 'Conexão instável, restabelecendo...';
            disableInput();
            
            // Backoff exponencial para reconexão
            reconnectTimeout = setTimeout(() => {
                reconnectDelay = Math.min(reconnectDelay * 2, 30000); // Máximo 30s
                connectWebSocket();
            }, reconnectDelay);
        };

        socket.onerror = (error) => {
            console.error('Erro no WebSocket:', error);
            socket.close();
        };
    }

    // Gerenciamento do Histórico de Mensagens
    function showTypingIndicator() {
        typingIndicator.classList.remove('hidden');
        scrollToBottom();
    }

    function hideTypingIndicator() {
        typingIndicator.classList.add('hidden');
    }

    function appendToken(token) {
        if (!currentResponseElement) {
            // Cria um novo contêiner de mensagem para a resposta da ELIZA
            const messageDiv = document.createElement('div');
            messageDiv.className = 'message eliza-message';
            
            const contentDiv = document.createElement('div');
            contentDiv.className = 'message-content';
            messageDiv.appendChild(contentDiv);
            
            chatHistory.appendChild(messageDiv);
            currentResponseElement = contentDiv;
        }
        
        // Adiciona o token ao conteúdo da mensagem
        currentResponseElement.innerHTML += token;
        scrollToBottom();
    }

    function appendUserMessage(text) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message user-message';
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        contentDiv.textContent = text;
        
        messageDiv.appendChild(contentDiv);
        chatHistory.appendChild(messageDiv);
        scrollToBottom();
    }

    function appendErrorMessage(text) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message eliza-message system-error';
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        contentDiv.style.color = '#ff8787';
        contentDiv.textContent = text;
        
        messageDiv.appendChild(contentDiv);
        chatHistory.appendChild(messageDiv);
        scrollToBottom();
    }

    function scrollToBottom() {
        chatHistory.scrollTop = chatHistory.scrollHeight;
    }

    function disableInput() {
        userInput.disabled = true;
        userInput.placeholder = "Aguardando sintonia...";
    }

    function enableInput() {
        userInput.disabled = false;
        userInput.placeholder = "Fale comigo, estou ouvindo...";
        userInput.focus();
    }

    // Mudança suave na iluminação ambiental baseada na emoção
    function changeAtmosphere(emotion) {
        const validEmotions = ['calm', 'joy', 'sadness', 'anger', 'anxiety'];
        if (validEmotions.includes(emotion)) {
            // Remove temas anteriores e adiciona o novo
            validEmotions.forEach(e => document.body.classList.remove(`theme-${e}`));
            document.body.classList.add(`theme-${emotion}`);
            console.log(`Atmosfera alterada para: ${emotion}`);
        }
    }

    // Submissão do Formulário de Envio
    chatForm.addEventListener('submit', (event) => {
        event.preventDefault();
        
        const text = userInput.value.trim();
        if (!text || socket.readyState !== WebSocket.OPEN) return;

        // Adiciona a mensagem do usuário na tela
        appendUserMessage(text);
        
        // Envia para o backend via WebSocket
        socket.send(text);
        
        // Limpa o campo e desativa input temporariamente até a ELIZA responder
        userInput.value = '';
        disableInput();
        showTypingIndicator();
    });

    // Reinicia a conversa de forma limpa ao clicar no botão de reset
    const resetButton = document.getElementById('reset-button');
    if (resetButton) {
        resetButton.addEventListener('click', () => {
            if (confirm('Deseja reiniciar a conversa e limpar o histórico?')) {
                localStorage.removeItem('eliza_session_id');
                conversationId = 'new';
                
                // Limpa o feed visual de mensagens
                chatHistory.innerHTML = `
                    <div class="message eliza-message initial-message">
                        <div class="message-content">
                            Olá. Estou aqui e pronta para ouvir você. Como você está se sentindo hoje?
                        </div>
                    </div>
                `;
                
                // Força reconexão WebSocket enviando 'new' para o servidor
                if (socket) {
                    socket.close();
                }
            }
        });
    }

    // Inicia conexão
    connectWebSocket();
});
