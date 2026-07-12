// Function to handle chat messages
function sendMessage() {
    const inputField = document.getElementById('user-input');
    const chatHistory = document.getElementById('chat-history');
    const userText = inputField.value.trim();

    if (userText === "") return;

    // Add user message to UI
    chatHistory.innerHTML += `<div class="user-msg">You: ${userText}</div>`;
    
    // Clear input
    inputField.value = '';

    // Placeholder: This is where you would call fetch() to send the text to app.py
    setTimeout(() => {
        chatHistory.innerHTML += `<div class="bot-msg">NutriAgent/FacultyBot: I'm processing your query regarding "${userText}"...</div>`;
        chatHistory.scrollTop = chatHistory.scrollHeight; // Auto-scroll to bottom
    }, 500);
}

// Ensure the Enter key triggers the chat
document.addEventListener('keypress', function (e) {
    if (e.key === 'Enter') {
        sendMessage();
    }
});
    

