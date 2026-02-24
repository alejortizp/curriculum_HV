/**
 * AI Career Suite + PDF download functionality.
 * Reads configuration from the global CV_CONFIG object set by the HTML template.
 */

let currentQuestion = "";

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
    document.getElementById('interviewInputArea').classList.add('hidden');
    document.getElementById('userAnswer').value = "";
    currentQuestion = "";
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
    showResult(await callGemini(CV_CONFIG.prompts.elevatorPitch(getCVText())));
}

async function startMockInterview() {
    currentQuestion = await callGemini(CV_CONFIG.prompts.mockInterview(getCVText()));
    showResult(`### ${CV_CONFIG.i18n.interviewQuestionLabel}:\n\n${currentQuestion}`, true);
}

async function submitAnswer() {
    const ans = document.getElementById('userAnswer').value;
    showResult(await callGemini(CV_CONFIG.prompts.submitAnswer(currentQuestion, ans)));
}

async function generateCoverLetter(comp, role) {
    showResult(await callGemini(CV_CONFIG.prompts.coverLetter(comp, role, getCVText())));
}

async function generateGapAnalysis(role) {
    showResult(await callGemini(CV_CONFIG.prompts.gapAnalysis(role, getCVText())));
}
