// API Configuration
const API_BASE_URL = 'http://localhost:8000';

// Language configuration (moved from languages.js)
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
        japanese: "Japanese",
        kore: "Korean (Kore)",
        charon: "Charon",
        fenrir: "Fenrir"
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
        japanese: "ஜப்பானியம்",
        kore: "கொரியன் (Kore)",
        charon: "Charon",
        fenrir: "Fenrir"
    }
};

// Language manager (integrated)
class LanguageManager {
    constructor() {
        this.currentLanguage = localStorage.getItem('selectedLanguage') || 'english';
    }

    setLanguage(lang) {
        this.currentLanguage = lang;
        localStorage.setItem('selectedLanguage', lang);
        this.updateUI();
    }

    getCurrentLanguage() {
        return this.currentLanguage;
    }

    getText(key) {
        return languages[this.currentLanguage][key] || key;
    }

    updateUI() {
        // Update all elements with data-lang attribute
        document.querySelectorAll('[data-lang]').forEach(element => {
            const key = element.getAttribute('data-lang');
            const text = this.getText(key);
            
            if (element.tagName === 'INPUT' && element.type !== 'file') {
                element.placeholder = text;
            } else {
                element.textContent = text;
            }
        });

        // Update select options
        document.querySelectorAll('select[data-lang-options]').forEach(select => {
            const optionType = select.getAttribute('data-lang-options');
            this.updateSelectOptions(select, optionType);
        });
    }

    updateSelectOptions(select, optionType) {
        const options = {
            translate: [
                { value: '', text: this.getText('noTranslation') },
                { value: 'Spanish', text: this.getText('spanish') },
                { value: 'French', text: this.getText('french') },
                { value: 'German', text: this.getText('german') },
                { value: 'Chinese', text: this.getText('chinese') },
                { value: 'Japanese', text: this.getText('japanese') }
            ],
            voice: [
                { value: 'Kore', text: this.getText('kore') },
                { value: 'Charon', text: this.getText('charon') },
                { value: 'Fenrir', text: this.getText('fenrir') }
            ]
        };

        if (options[optionType]) {
            select.innerHTML = '';
            options[optionType].forEach(option => {
                const opt = document.createElement('option');
                opt.value = option.value;
                opt.textContent = option.text;
                select.appendChild(opt);
            });
        }
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

// Initialize UI text based on saved language
document.addEventListener('DOMContentLoaded', () => {
    langManager.updateUI();
    updateLanguageButton();
});

// Language toggle button
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

// Form Submission
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

// Display Functions
function showLoading() {
    loadingSection.classList.remove('hidden');
    resultsSection.classList.add('hidden');
    errorSection.classList.add('hidden');
}

function hideLoading() {
    loadingSection.classList.add('hidden');
}

function displayResults(data) {
    hideLoading();
    resultsSection.classList.remove('hidden');
    
    // Check for errors
    if (data.error) {
        showError(data.error);
        return;
    }
    
    // Document Type
    document.getElementById('docType').textContent = data.doc_type || 'Unknown';
    document.getElementById('docSubtype').textContent = data.doc_subtype ? `Subtype: ${data.doc_subtype}` : '';
    document.getElementById('confidence').textContent = data.confidence ? `Confidence: ${(data.confidence * 100).toFixed(1)}%` : '';
    
    // Entities
    displayEntities(data.entities);
    
    // Clauses
    displayClauses(data.clauses, data.clause_entities);
    
    // Summary
    if (data.summary) {
        document.getElementById('summary').textContent = data.summary;
    }
    
    // Key Points
    if (data.key_points && data.key_points.length > 0) {
        const keyPointsList = document.getElementById('keyPoints');
        keyPointsList.innerHTML = '';
        data.key_points.forEach(point => {
            const li = document.createElement('li');
            li.innerHTML = `<i class="fas fa-check-circle text-green-400 mr-2"></i>${point}`;
            keyPointsList.appendChild(li);
        });
    }
    
    // Risks
    if (data.risks && data.risks.length > 0) {
        const risksList = document.getElementById('risks');
        risksList.innerHTML = '';
        data.risks.forEach(risk => {
            const li = document.createElement('li');
            li.innerHTML = `<i class="fas fa-exclamation-triangle text-yellow-400 mr-2"></i>${risk}`;
            risksList.appendChild(li);
        });
    }
    
    // Action Items
    if (data.action_items && data.action_items.length > 0) {
        const actionItemsList = document.getElementById('actionItems');
        actionItemsList.innerHTML = '';
        data.action_items.forEach(item => {
            const li = document.createElement('li');
            li.innerHTML = `<i class="fas fa-arrow-right text-blue-400 mr-2"></i>${item}`;
            actionItemsList.appendChild(li);
        });
    }
    
    // Translation
    if (data.translation) {
        document.getElementById('translationSection').classList.remove('hidden');
        document.getElementById('translation').textContent = data.translation;
    }
    
    // Audio
    if (data.tts_paths && Object.keys(data.tts_paths).length > 0) {
        displayAudioPlayers(data.tts_paths);
    }
    
    // Add fade-in animation
    resultsSection.classList.add('fade-in');
}

function displayEntities(entities) {
    const entitiesContainer = document.getElementById('entities');
    entitiesContainer.innerHTML = '';
    
    if (!entities || entities.length === 0) {
        entitiesContainer.innerHTML = '<p class="text-white/70">No entities found</p>';
        return;
    }
    
    // Group entities by type
    const groupedEntities = {};
    entities.forEach(entity => {
        const type = entity.type || 'Other';
        if (!groupedEntities[type]) {
            groupedEntities[type] = [];
        }
        groupedEntities[type].push(entity);
    });
    
    // Display grouped entities
    Object.keys(groupedEntities).forEach(type => {
        const typeDiv = document.createElement('div');
        typeDiv.className = 'mb-4';
        
        const typeHeader = document.createElement('h4');
        typeHeader.className = 'text-lg font-semibold text-white mb-2';
        typeHeader.textContent = `${type} (${groupedEntities[type].length})`;
        typeDiv.appendChild(typeHeader);
        
        const entitiesList = document.createElement('div');
        entitiesList.className = 'flex flex-wrap gap-2';
        
        groupedEntities[type].forEach(entity => {
            const entitySpan = document.createElement('span');
            entitySpan.className = 'bg-white/20 px-2 py-1 rounded text-sm text-white';
            entitySpan.textContent = entity.value;
            entitiesList.appendChild(entitySpan);
        });
        
        typeDiv.appendChild(entitiesList);
        entitiesContainer.appendChild(typeDiv);
    });
}

function displayClauses(clauses, clauseEntities) {
    const clausesContainer = document.getElementById('clauses');
    clausesContainer.innerHTML = '';
    
    if (!clauses || clauses.length === 0) {
        clausesContainer.innerHTML = '<p class="text-white/70">No clauses found</p>';
        return;
    }
    
    clauses.forEach(clause => {
        const clauseDiv = document.createElement('div');
        clauseDiv.className = 'border border-white/20 rounded-lg p-4 mb-4';
        
        const clauseHeader = document.createElement('h4');
        clauseHeader.className = 'text-lg font-semibold text-white mb-2';
        clauseHeader.textContent = `Clause ${clause.clause_number}`;
        clauseDiv.appendChild(clauseHeader);
        
        // Simplified text only (hide original as requested)
        const simplifiedDiv = document.createElement('div');
        simplifiedDiv.className = 'mb-1';
        simplifiedDiv.innerHTML = `
            <p class="text-white/90 text-sm">${clause.simplified_text || '(not available)'}</p>
        `;
        clauseDiv.appendChild(simplifiedDiv);
        
        // Entities for this clause
        if (clauseEntities && clauseEntities[clause.clause_number]) {
            const entities = clauseEntities[clause.clause_number];
            if (entities.length > 0) {
                const entitiesDiv = document.createElement('div');
                entitiesDiv.className = 'mt-2';
                entitiesDiv.innerHTML = `
                    <h6 class="text-xs font-semibold text-white/70 mb-1">Entities:</h6>
                    <div class="flex flex-wrap gap-1">
                        ${entities.map(entity => 
                            `<span class="bg-blue-500/30 px-1 py-0.5 rounded text-xs text-white">${entity.value}</span>`
                        ).join('')}
                    </div>
                `;
                clauseDiv.appendChild(entitiesDiv);
            }
        }
        
        clausesContainer.appendChild(clauseDiv);
    });
}

function displayAudioPlayers(ttsPaths) {
    const audioSection = document.getElementById('audioSection');
    const audioPlayersContainer = document.getElementById('audioPlayers');
    
    audioSection.classList.remove('hidden');
    audioPlayersContainer.innerHTML = '';
    
    Object.keys(ttsPaths).forEach(key => {
        const audioDiv = document.createElement('div');
        audioDiv.className = 'mb-4';
        
        const audioLabel = document.createElement('label');
        audioLabel.className = 'block text-white/80 mb-2 text-sm font-semibold';
        audioLabel.textContent = key === 'summary' ? 'Document Summary' : `Clause ${key}`;
        audioDiv.appendChild(audioLabel);
        
        const audio = document.createElement('audio');
        audio.controls = true;
        audio.className = 'w-full';
        audio.src = `${API_BASE_URL}${ttsPaths[key]}`;
        audioDiv.appendChild(audio);
        
        audioPlayersContainer.appendChild(audioDiv);
    });
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
