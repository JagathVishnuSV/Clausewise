// Enhanced JavaScript with better interactivity and language support

// Language configuration
const languages = {
    english: {
        title: "Legal Document Analyzer",
        subtitle: "AI-Powered Document Analysis & Translation",
        uploadTitle: "Upload Document",
        chooseFile: "Choose File",
        translateTo: "Translate To (Optional)",
        noTranslation: "No Translation",
        ttsVoice: "Text-to-Speech Voice",
        enableTTS: "Enable Text-to-Speech",
        analyzeButton: "Analyze Document",
        documentType: "Document Type",
        summary: "Summary",
        keyPoints: "Key Points",
        risks: "Risks",
        actionItems: "Action Items",
        translation: "Translation",
        audioSummary: "Audio Summary",
        analyzing: "Analyzing your document...",
        selectFile: "Please select a file to analyze.",
        errorTitle: "Error",
        spanish: "Spanish",
        french: "French",
        german: "German",
        chinese: "Chinese",
        japanese: "Japanese"
    },
    tamil: {
        title: "சட்ட ஆவண பகுப்பாய்வாளர்",
        subtitle: "செயற்கை நுண்ணறிவு இயக்கப்பட்ட ஆவண பகுப்பாய்வு மற்றும் மொழிபெயர்ப்பு",
        uploadTitle: "ஆவணத்தை பதிவேற்றவும்",
        chooseFile: "கோப்பைத் தேர்ந்தெடுக்கவும்",
        translateTo: "மொழிபெயர்க்க (விருப்பம்)",
        noTranslation: "மொழிபெயர்ப்பு இல்லை",
        ttsVoice: "உரை-பேச்சு குரல்",
        enableTTS: "உரை-பேச்சு இயக்கவும்",
        analyzeButton: "ஆவணத்தை பகுப்பாய்வு செய்யவும்",
        documentType: "ஆவண வகை",
        summary: "சுருக்கம்",
        keyPoints: "முக்கிய அம்சங்கள்",
        risks: "அபாயங்கள்",
        actionItems: "செயல் உருப்படிகள்",
        translation: "மொழிபெயர்ப்பு",
        audioSummary: "ஆடியோ சுருக்கம்",
        analyzing: "உங்கள் ஆவணத்தை பகுப்பாய்வு செய்கிறது...",
        selectFile: "பகுப்பாய்வு செய்ய ஒரு கோப்பைத் தேர்ந்தெடுக்கவும்.",
        errorTitle: "பிழை",
        spanish: "ஸ்பானிஷ்",
        french: "பிரெஞ்சு",
        german: "ஜெர்மன்",
        chinese: "சீனம்",
        japanese: "ஜப்பானியம்"
    }
};

// API Configuration
const API_BASE_URL = 'http://localhost:8000';

// Language Manager
class LanguageManager {
    constructor() {
        this.currentLanguage = localStorage.getItem('selectedLanguage') || 'english';
    }

    setLanguage(lang) {
        this.currentLanguage = lang;
        localStorage.setItem('selectedLanguage', lang);
        this.updateUI();
    }

    getText(key) {
        return languages[this.currentLanguage][key] || key;
    }

    updateUI() {
        document.querySelectorAll('[data-lang]').forEach(element => {
            const key = element.getAttribute('data-lang');
            const text = this.getText(key);
            
            if (element.tagName === 'INPUT' && element.type !== 'file') {
                element.placeholder = text;
            } else {
                element.textContent = text;
            }
        });
    }
}

// Initialize language manager
const langManager = new LanguageManager();

// DOM Elements
const uploadForm = document.getElementById('uploadForm');
const fileInput = document.getElementById('fileInput');
const loadingSection = document.getElementById('loadingSection');
const resultsSection = document.getElementById('resultsSection');
const errorSection = document.getElementById('errorSection');
const languageToggle = document.getElementById('languageToggle');
const languageText = document.getElementById('languageText');
const progressContainer = document.getElementById('progressContainer');
const progressBar = document.getElementById('progressBar');
const progressText = document.getElementById('progressText');
const tamilCheckbox = document.getElementById('tamilCheckbox');

// Initialize UI
document.addEventListener('DOMContentLoaded', () => {
    langManager.updateUI();
    updateLanguageButton();
});

// Language toggle
languageToggle.addEventListener('click', () => {
    const currentLang = langManager.getCurrentLanguage();
    const newLang = currentLang === 'english' ? 'tamil' : 'english';
    langManager.setLanguage(newLang);
    updateLanguageButton();
});

function updateLanguageButton() {
    const currentLang = langManager.getCurrentLanguage();
    languageText.textContent = currentLang === 'english' ? 'தமிழ்' : 'English';
}

// Form submission with progress tracking
uploadForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const file = fileInput.files[0];
    if (!file) {
        showError(langManager.getText('selectFile'));
        return;
    }

    // Show loading state
    showLoading();
    
    // Prepare form data
    const formData = new FormData();
    formData.append('file', file);
    
    const translateTo = document.getElementById('translateSelect').value;
    if (translateTo) {
        formData.append('translate_to', translateTo);
    }
    
    const enableTTS = document.getElementById('ttsCheckbox').checked;
    if (enableTTS) {
        formData.append('tts', 'true');
        formData.append('tts_voice', document.getElementById('voiceSelect').value);
    }
    
    const language = tamilCheckbox.checked ? 'tamil' : 'english';
    formData.append('language', language);

    try {
        const response = await fetch(`${API_BASE_URL}/analyze`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        displayResults(data);
        
    } catch (error) {
        showError(`${langManager.getText('errorTitle')}: ${error.message}`);
    }
});

// Display functions
function showLoading() {
    loadingSection.classList.remove('hidden');
    resultsSection.classList.add('hidden');
    errorSection.classList.add('hidden');
    progressContainer.classList.remove('hidden');
    
    // Simulate progress
    let progress = 0;
    const interval = setInterval(() => {
        progress += Math.random() * 10;
        if (progress >= 100) {
            progress = 100;
            clearInterval(interval);
            progressContainer.classList.add('hidden');
        }
        progressBar.style.width = progress + '%';
        progressText.textContent = `${Math.round(progress)}% ${langManager.getText('analyzing')}`;
    }, 200);
}

function hideLoading() {
    loadingSection.classList.add('hidden');
    progressContainer.classList.add('hidden');
}

function displayResults(data) {
    hideLoading();
    resultsSection.classList.remove('hidden');
    
    // Document Type
    document.getElementById('docType').textContent = data.document_type;
    
    // Summary
    document.getElementById('summary').textContent = data.summary;
    
    // Key Points
    const keyPointsList = document.getElementById('keyPoints');
    keyPointsList.innerHTML = '';
    data.key_points.forEach(point => {
        const li = document.createElement('li');
        li.innerHTML = `<i class="fas fa-check-circle text-green-400 mr-2"></i>${point}`;
        keyPointsList.appendChild(li);
    });
    
    // Risks
    const risksList = document.getElementById('risks');
    risksList.innerHTML = '';
    data.risks.forEach(risk => {
        const li = document.createElement('li');
        li.innerHTML = `<i class="fas fa-exclamation-triangle text-yellow-400 mr-2"></i>${risk}`;
        risksList.appendChild(li);
    });
    
    // Action Items
    const actionItemsList = document.getElementById('actionItems');
    actionItemsList.innerHTML = '';
    data.action_items.forEach(item => {
        const li = document.createElement('li');
        li.innerHTML = `<i class="fas fa-arrow-right text-blue-400 mr-2"></i>${item}`;
        actionItemsList.appendChild(li);
    });
    
    // Translation
    if (data.translation) {
        document.getElementById('translationSection').classList.remove('hidden');
        document.getElementById('translation').textContent = data.translation;
    }
    
    // Audio
    if (data.tts_path) {
        document.getElementById('audioSection').classList.remove('hidden');
        const audioPlayer = document.getElementById('audioPlayer');
        audioPlayer.src = `${API_BASE_URL}${data.tts_path}`;
    }
    
    // Add animation
    resultsSection.classList.add('fade-in');
}

function showError(message) {
    hideLoading();
    errorSection.classList.remove('hidden');
    document.getElementById('errorMessage').textContent = message;
}

// File input styling
fileInput.addEventListener('change', (e) => {
    const fileName = e.target.files[0]?.name || 'No file selected';
    console.log(`Selected: ${fileName}`);
});
