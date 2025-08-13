// Language configuration
const languages = {
    english: {
        // Header
        title: "Legal Document Analyzer",
        subtitle: "AI-Powered Document Analysis & Translation",
        
        // Upload Section
        uploadTitle: "Upload Document",
        chooseFile: "Choose File",
        translateTo: "Translate To (Optional)",
        noTranslation: "No Translation",
        ttsVoice: "Text-to-Speech Voice",
        enableTTS: "Enable Text-to-Speech",
        analyzeButton: "Analyze Document",
        
        // Results Section
        documentType: "Document Type",
        summary: "Summary",
        keyPoints: "Key Points",
        risks: "Risks",
        actionItems: "Action Items",
        translation: "Translation",
        audioSummary: "Audio Summary",
        
        // Loading
        analyzing: "Analyzing your document...",
        
        // Errors
        selectFile: "Please select a file to analyze.",
        errorTitle: "Error",
        
        // Languages
        spanish: "Spanish",
        french: "French",
        german: "German",
        chinese: "Chinese",
        japanese: "Japanese",
        
        // Voice options
        kore: "Korean (Kore)",
        charon: "Charon",
        fenrir: "Fenrir"
    },
    tamil: {
        // Header
        title: "சட்ட ஆவண பகுப்பாய்வாளர்",
        subtitle: "செயற்கை நுண்ணறிவு இயக்கப்பட்ட ஆவண பகுப்பாய்வு மற்றும் மொழிபெயர்ப்பு",
        
        // Upload Section
        uploadTitle: "ஆவணத்தை பதிவேற்றவும்",
        chooseFile: "கோப்பைத் தேர்ந்தெடுக்கவும்",
        translateTo: "மொழிபெயர்க்க (விருப்பம்)",
        noTranslation: "மொழிபெயர்ப்பு இல்லை",
        ttsVoice: "உரை-பேச்சு குரல்",
        enableTTS: "உரை-பேச்சு இயக்கவும்",
        analyzeButton: "ஆவணத்தை பகுப்பாய்வு செய்யவும்",
        
        // Results Section
        documentType: "ஆவண வகை",
        summary: "சுருக்கம்",
        keyPoints: "முக்கிய அம்சங்கள்",
        risks: "அபாயங்கள்",
        actionItems: "செயல் உருப்படிகள்",
        translation: "மொழிபெயர்ப்பு",
        audioSummary: "ஆடியோ சுருக்கம்",
        
        // Loading
        analyzing: "உங்கள் ஆவணத்தை பகுப்பாய்வு செய்கிறது...",
        
        // Errors
        selectFile: "பகுப்பாய்வு செய்ய ஒரு கோப்பைத் தேர்ந்தெடுக்கவும்.",
        errorTitle: "பிழை",
        
        // Languages
        spanish: "ஸ்பானிஷ்",
        french: "பிரெஞ்சு",
        german: "ஜெர்மன்",
        chinese: "சீனம்",
        japanese: "ஜப்பானியம்",
        
        // Voice options
        kore: "கொரியன் (Kore)",
        charon: "Charon",
        fenrir: "Fenrir"
    }
};

// Language manager
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
