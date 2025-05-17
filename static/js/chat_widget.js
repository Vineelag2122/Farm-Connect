class ChatWidget {
    constructor() {
        this.createChatIcon();
        this.createChatDialog();
        this.messages = [];
    }

    createChatIcon() {
        const chatIcon = document.createElement('div');
        chatIcon.innerHTML = `
            <div id="chat-icon" style="
                position: fixed;
                bottom: 20px;
                right: 20px;
                width: 60px;
                height: 60px;
                background-color: #1976d2;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                cursor: pointer;
                box-shadow: 0 2px 5px rgba(0,0,0,0.2);
                z-index: 9999;
            ">
                <svg style="width: 24px; height: 24px; fill: white;" viewBox="0 0 24 24">
                    <path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2z"/>
                </svg>
            </div>
        `;
        document.body.appendChild(chatIcon);
        
        chatIcon.querySelector('#chat-icon').addEventListener('click', () => {
            this.toggleDialog();
        });
    }

    createChatDialog() {
        const dialog = document.createElement('div');
        dialog.innerHTML = `
            <div id="chat-dialog" style="
                position: fixed;
                bottom: 90px;
                right: 20px;
                width: 300px;
                height: 400px;
                background: white;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                z-index: 9999;
                display: none;
                flex-direction: column;
                overflow: hidden;
            ">
                <div style="padding: 15px; background: #1976d2; color: white; font-weight: bold;">
                    AI Assistant (Telugu)
                    <span id="chat-close" style="float: right; cursor: pointer;">×</span>
                </div>
                <div id="chat-messages" style="flex-grow: 1; overflow-y: auto; padding: 15px;"></div>
                <div style="padding: 15px; border-top: 1px solid #eee;">
                    <form id="chat-form" style="display: flex; gap: 10px;">
                        <input type="text" id="chat-input" placeholder="Type your message..." 
                            style="flex-grow: 1; padding: 8px; border: 1px solid #ddd; border-radius: 4px;">
                        <button type="submit" style="background: #1976d2; color: white; border: none; 
                            padding: 8px 15px; border-radius: 4px; cursor: pointer;">Send</button>
                    </form>
                </div>
            </div>
        `;
        document.body.appendChild(dialog);
        
        const closeBtn = dialog.querySelector('#chat-close');
        closeBtn.addEventListener('click', () => {
            this.toggleDialog();
        });

        const form = dialog.querySelector('#chat-form');
        form.addEventListener('submit', (e) => {
            e.preventDefault();
            const input = dialog.querySelector('#chat-input');
            const message = input.value.trim();
            if (message) {
                this.sendMessage(message);
                input.value = '';
            }
        });
    }

    toggleDialog() {
        const dialog = document.querySelector('#chat-dialog');
        if (dialog) {
            dialog.style.display = dialog.style.display === 'none' ? 'flex' : 'none';
        }
    }

    async sendMessage(message) {
        const messagesDiv = document.querySelector('#chat-messages');
        
        // Add user message
        this.addMessage(message, 'user');

        try {
            const response = await fetch('/api/ai/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message })
            });

            const data = await response.json();
            if (data.response) {
                this.addMessage(data.response, 'ai');
            }
        } catch (error) {
            console.error('Error:', error);
            this.addMessage('Sorry, something went wrong.', 'error');
        }
    }

    addMessage(text, sender) {
        const messagesDiv = document.querySelector('#chat-messages');
        const messageDiv = document.createElement('div');
        messageDiv.style.marginBottom = '10px';
        messageDiv.style.display = 'flex';
        messageDiv.style.justifyContent = sender === 'user' ? 'flex-end' : 'flex-start';
        
        const bubble = document.createElement('div');
        bubble.style.maxWidth = '80%';
        bubble.style.padding = '8px 12px';
        bubble.style.borderRadius = '15px';
        bubble.style.backgroundColor = sender === 'user' ? '#1976d2' : '#f0f0f0';
        bubble.style.color = sender === 'user' ? 'white' : 'black';
        bubble.textContent = text;
        
        messageDiv.appendChild(bubble);
        messagesDiv.appendChild(messageDiv);
        messagesDiv.scrollTop = messagesDiv.scrollHeight;
    }
}

// Initialize the chat widget when the page loads
window.addEventListener('load', () => {
    new ChatWidget();
});
