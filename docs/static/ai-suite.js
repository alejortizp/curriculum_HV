/**
 * AI Career Suite + PDF download functionality.
 * Reads configuration from the global CV_CONFIG object set by the HTML template.
 * API key resolution: build-time (.env) → localStorage → prompt user.
 */

let currentQuestion = "";

// -- API Key Management --
function getApiKey() {
    return CV_CONFIG.apiKey;
}

function saveApiKey(key) {
    localStorage.setItem("gemini_api_key", key.trim());
    CV_CONFIG.apiKey = key.trim();
}

function clearApiKey() {
    localStorage.removeItem("gemini_api_key");
    CV_CONFIG.apiKey = "";
}

function hasApiKey() {
    return CV_CONFIG.apiKey && CV_CONFIG.apiKey.length > 0;
}

function showApiKeyPrompt(onSuccess) {
    document.getElementById('aiMenu').classList.add('hidden');
    document.getElementById('aiKeySetup').classList.remove('hidden');
    const btn = document.getElementById('saveApiKeyBtn');
    btn.onclick = () => {
        const key = document.getElementById('apiKeyInput').value.trim();
        if (key) {
            saveApiKey(key);
            document.getElementById('aiKeySetup').classList.add('hidden');
            document.getElementById('apiKeyInput').value = "";
            if (onSuccess) onSuccess();
            else resetAI();
        }
    };
}

function requireApiKey(callback) {
    if (hasApiKey()) {
        callback();
    } else {
        showApiKeyPrompt(callback);
    }
}

// -- PDF Download --
function downloadPDF() {
    const element = document.getElementById('cvContent');
    const btn = document.getElementById('btnDownload');
    const originalContent = btn.innerHTML;

    btn.innerHTML = `<i class="fas fa-spinner fa-spin"></i> ${CV_CONFIG.i18n.generating}`;
    btn.disabled = true;

    const opt = {
        margin: 0,
        filename: CV_CONFIG.pdfFilename,
        image: { type: 'jpeg', quality: 0.98 },
        html2canvas: { scale: 2 },
        jsPDF: { unit: 'in', format: 'a4', orientation: 'portrait' }
    };

    html2pdf().set(opt).from(element).save().then(() => {
        btn.innerHTML = originalContent;
        btn.disabled = false;
    }).catch(() => {
        alert(CV_CONFIG.i18n.pdfError);
        btn.innerHTML = originalContent;
        btn.disabled = false;
    });
}

// -- Modal Helpers --
function toggleAIModal() {
    const modal = document.getElementById('aiModal');
    modal.classList.toggle('hidden');
    modal.classList.toggle('flex');
    if (!modal.classList.contains('hidden')) resetAI();
}

function resetAI() {
    document.getElementById('aiMenu').classList.remove('hidden');
    document.getElementById('aiLoading').classList.add('hidden');
    document.getElementById('aiResult').classList.add('hidden');
    document.getElementById('aiInputView').classList.add('hidden');
    document.getElementById('aiKeySetup').classList.add('hidden');
    document.getElementById('interviewInputArea').classList.add('hidden');
    document.getElementById('userAnswer').value = "";
    currentQuestion = "";
    updateKeyStatus();
}

function updateKeyStatus() {
    const statusEl = document.getElementById('apiKeyStatus');
    if (!statusEl) return;
    if (hasApiKey()) {
        const source = CV_CONFIG._buildTimeKey ? CV_CONFIG.i18n.keyFromBuild : CV_CONFIG.i18n.keyFromBrowser;
        statusEl.innerHTML = `<span class="text-green-600"><i class="fas fa-check-circle"></i> ${source}</span>
            <button onclick="clearApiKey(); resetAI();" class="text-xs text-red-500 hover:underline ml-2">${CV_CONFIG.i18n.clearKey}</button>`;
    } else {
        statusEl.innerHTML = `<span class="text-amber-600"><i class="fas fa-exclamation-triangle"></i> ${CV_CONFIG.i18n.noKey}</span>
            <button onclick="showApiKeyPrompt();" class="text-xs text-blue-600 hover:underline ml-2">${CV_CONFIG.i18n.configureKey}</button>`;
    }
}

function showInputView(type) {
    document.getElementById('aiMenu').classList.add('hidden');
    document.getElementById('aiInputView').classList.remove('hidden');
    document.getElementById('aiInputView').classList.add('flex');
    const container = document.getElementById('inputForm');
    container.innerHTML = '';
    const title = document.getElementById('inputTitle');
    const btn = document.getElementById('inputActionBtn');

    if (type === 'coverLetter') {
        const cfg = CV_CONFIG.i18n.coverLetter;
        title.innerText = cfg.title;
        container.innerHTML = `<input type="text" id="inputCompany" placeholder="${cfg.companyPlaceholder}" class="w-full border p-2 rounded"><input type="text" id="inputRole" placeholder="${cfg.rolePlaceholder}" class="w-full border p-2 rounded">`;
        btn.onclick = () => {
            if (document.getElementById('inputCompany').value)
                generateCoverLetter(document.getElementById('inputCompany').value, document.getElementById('inputRole').value);
        };
    } else if (type === 'gapAnalysis') {
        const cfg = CV_CONFIG.i18n.gapAnalysis;
        title.innerText = cfg.title;
        container.innerHTML = `<input type="text" id="inputDreamJob" placeholder="${cfg.placeholder}" class="w-full border p-2 rounded">`;
        btn.onclick = () => {
            if (document.getElementById('inputDreamJob').value)
                generateGapAnalysis(document.getElementById('inputDreamJob').value);
        };
    }
}

function showLoading() {
    document.getElementById('aiMenu').classList.add('hidden');
    document.getElementById('aiInputView').classList.add('hidden');
    document.getElementById('aiLoading').classList.remove('hidden');
    document.getElementById('aiLoading').classList.add('flex');
}

function showResult(text, isInterview = false) {
    document.getElementById('aiLoading').classList.add('hidden');
    document.getElementById('aiLoading').classList.remove('flex');
    document.getElementById('aiResult').classList.remove('hidden');
    document.getElementById('aiResponseText').innerHTML = marked.parse(text);
    if (isInterview) document.getElementById('interviewInputArea').classList.remove('hidden');
}

// -- Gemini API --
async function callGemini(prompt) {
    showLoading();
    try {
        const res = await fetch(
            `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-09-2025:generateContent?key=${CV_CONFIG.apiKey}`,
            {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ contents: [{ parts: [{ text: prompt }] }] })
            }
        );
        const data = await res.json();
        return data.candidates[0].content.parts[0].text;
    } catch (e) {
        return CV_CONFIG.i18n.connectionError;
    }
}

// -- AI Feature Functions --
function getCVText() {
    return document.getElementById('cvContent').innerText.substring(0, 3000);
}

async function generateElevatorPitch() {
    requireApiKey(async () => showResult(await callGemini(CV_CONFIG.prompts.elevatorPitch(getCVText()))));
}

async function startMockInterview() {
    requireApiKey(async () => {
        currentQuestion = await callGemini(CV_CONFIG.prompts.mockInterview(getCVText()));
        showResult(`### ${CV_CONFIG.i18n.interviewQuestionLabel}:\n\n${currentQuestion}`, true);
    });
}

async function submitAnswer() {
    const ans = document.getElementById('userAnswer').value;
    showResult(await callGemini(CV_CONFIG.prompts.submitAnswer(currentQuestion, ans)));
}

async function generateCoverLetter(comp, role) {
    requireApiKey(async () => showResult(await callGemini(CV_CONFIG.prompts.coverLetter(comp, role, getCVText()))));
}

async function generateGapAnalysis(role) {
    requireApiKey(async () => showResult(await callGemini(CV_CONFIG.prompts.gapAnalysis(role, getCVText()))));
}
