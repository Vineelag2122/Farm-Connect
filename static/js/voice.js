const synth = window.speechSynthesis;

// Assistant state
let isAssistantActive = false;
let currentPage = window.location.pathname;
let selectedLanguage = 'en-IN'; // Default language: English (India)
let voices = [];

// Instructions for each page in English, Telugu, and Hindi
const instructions = {
    '/farmerdash': {
        'en-IN': [
            'Welcome to the Farmer Dashboard. Here you can access all farming related information.',
            'Check weather updates, soil analysis, market prices, and get assistance from our chatbot.',
            'Click on News to see the latest agricultural news and updates.'
        ],
        'te-IN': [
            'రైతు డాష్‌బోర్డ్‌కు స్వాగతం. ఇక్కడ మీరు వ్యవసాయానికి సంబంధించిన అన్ని సమాచారాన్ని యాక్సెస్ చేయవచ్చు.',
            'వాతావరణ నవీకరణలు, నేల విశ్లేషణ, మార్కెట్ ధరలను తనిఖీ చేయండి మరియు మా చాట్‌బాట్ నుండి సహాయం పొందండి.',
            'తాజా వ్యవసాయ వార్తలు మరియు నవీకరణలను చూడటానికి వార్తలపై క్లిక్ చేయండి.'
        ],
        'hi-IN': [
            'किसान डैशबोर्ड में आपका स्वागत है। यहां आप खेती से संबंधित सभी जानकारी एक्सेस कर सकते हैं।',
            'मौसम अपडेट, मिट्टी विश्लेषण, बाजार मूल्य जांचें और हमारे चैटबॉट से सहायता प्राप्त करें।',
            'नवीनतम कृषि समाचार और अपडेट देखने के लिए न्यूज पर क्लिक करें।'
        ]
    }
};

// Load voices with retries
async function loadVoices(maxRetries = 5, delayMs = 1000) {
    let attempt = 0;
    while (attempt < maxRetries) {
        voices = synth.getVoices();
        if (voices.length > 0) {
            console.log('Voices loaded successfully');
            return;
        }
        console.log(`Attempt ${attempt + 1}: Waiting for voices to load...`);
        await new Promise(resolve => setTimeout(resolve, delayMs));
        attempt++;
    }
    console.error('Failed to load voices after maximum retries');
}

// Get available voices for supported languages
function getAvailableVoices() {
    const supportedLanguages = ['en-IN', 'te-IN', 'hi-IN'];
    return voices.filter(voice => 
        supportedLanguages.some(lang => voice.lang.startsWith(lang))
    );
}

// Speak a message
function speak(text) {
    if (!isAssistantActive) return;

    // Cancel any ongoing speech
    synth.cancel();

    const utterance = new SpeechSynthesisUtterance(text);
    
    // Find a voice for the selected language
    const availableVoices = getAvailableVoices();
    const voice = availableVoices.find(v => v.lang.startsWith(selectedLanguage)) || 
                 voices.find(v => v.lang.startsWith('en')) || 
                 voices[0];
    
    utterance.voice = voice;
    utterance.lang = selectedLanguage;
    utterance.rate = 1;
    utterance.pitch = 1;

    synth.speak(utterance);
}

// Start the assistant
function startAssistant() {
    isAssistantActive = true;
    document.getElementById('assistant-toggle').classList.add('active');
    
    // Get instructions for current page
    const pageInstructions = instructions[currentPage] || instructions['/'];
    if (pageInstructions) {
        const langInstructions = pageInstructions[selectedLanguage] || pageInstructions['en-IN'];
        if (langInstructions) {
            // Speak each instruction with a delay
            langInstructions.forEach((instruction, index) => {
                setTimeout(() => speak(instruction), index * 5000);
            });
        }
    }
}

// Stop the assistant
function stopAssistant() {
    isAssistantActive = false;
    synth.cancel();
    document.getElementById('assistant-toggle').classList.remove('active');
}

// Initialize voices when available
speechSynthesis.onvoiceschanged = () => {
    loadVoices();
};

// Add voice assistant button when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    const assistantButton = document.createElement('button');
    assistantButton.id = 'assistant-toggle';
    assistantButton.className = 'voice-assistant-btn';
    assistantButton.innerHTML = `
        <i class="fas fa-microphone"></i>
        <span class="tooltip">Voice Assistant</span>
    `;
    document.body.appendChild(assistantButton);

    // Add styles
    const style = document.createElement('style');
    style.textContent = `
        .voice-assistant-btn {
            position: fixed;
            bottom: 100px;
            right: 20px;
            width: 50px;
            height: 50px;
            border-radius: 50%;
            background-color: #4CAF50;
            border: none;
            color: white;
            cursor: pointer;
            box-shadow: 0 2px 5px rgba(0,0,0,0.2);
            z-index: 9998;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.3s ease;
        }
        .voice-assistant-btn:hover {
            transform: scale(1.1);
        }
        .voice-assistant-btn.active {
            background-color: #f44336;
        }
        .voice-assistant-btn .tooltip {
            position: absolute;
            right: 60px;
            background-color: #333;
            color: white;
            padding: 5px 10px;
            border-radius: 5px;
            font-size: 12px;
            opacity: 0;
            transition: opacity 0.3s;
            white-space: nowrap;
        }
        .voice-assistant-btn:hover .tooltip {
            opacity: 1;
        }
    `;
    document.head.appendChild(style);

    // Toggle assistant on button click
    assistantButton.addEventListener('click', () => {
        if (isAssistantActive) {
            stopAssistant();
        } else {
            startAssistant();
        }
    });
});
