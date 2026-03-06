// ========== DOM References ==========
const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => document.querySelectorAll(sel);

// Sections
const sectionSettings = $('#section-settings');
const sectionAims = $('#section-aims');
const sectionGenerate = $('#section-generate');
const sectionDownload = $('#section-download');

// Settings
const apiKeyInput = $('#api-key');
const modelSelect = $('#model-select');
const mockToggle = $('#mock-toggle');
const mockLabel = $('#mock-label');
const toggleKeyBtn = $('#toggle-key-visibility');
const advancedBtn = $('#toggle-advanced');
const advancedPanel = $('#advanced-settings');
const fontNameSelect = $('#font-name');
const bodySizeInput = $('#body-size');
const headingSizeInput = $('#heading-size');
const codeSizeInput = $('#code-size');
const imageWidthInput = $('#image-width');
const outputFilename = $('#output-filename');

// Aims
const aimsTextarea = $('#aims-textarea');
const fileUpload = $('#file-upload');
const btnLoadSample = $('#btn-load-sample');

// Generate
const experimentsList = $('#experiments-list');
const experimentCount = $('#experiment-count');
const progressContainer = $('#progress-container');
const progressText = $('#progress-text');
const progressPercent = $('#progress-percent');
const progressFill = $('#progress-fill');
const resultsList = $('#results-list');

// Navigation buttons
const btnNextToAims = $('#btn-next-to-aims');
const btnBackToSettings = $('#btn-back-to-settings');
const btnParse = $('#btn-parse');
const btnBackToAims = $('#btn-back-to-aims');
const btnGenerate = $('#btn-generate');
const btnBackToGenerate = $('#btn-back-to-generate');
const btnDownload = $('#btn-download');

// ========== State ==========
let parsedAims = [];
let generatedExperiments = [];
let currentStep = 1;

// ========== Utilities ==========
function showToast(message, type = 'info') {
    const container = $('#toast-container');
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    container.appendChild(toast);
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(40px)';
        toast.style.transition = '0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 3500);
}

function setStep(step) {
    currentStep = step;
    const steps = $$('.step');
    steps.forEach((el, idx) => {
        el.classList.remove('active', 'done');
        if (idx + 1 < step) el.classList.add('done');
        if (idx + 1 === step) el.classList.add('active');
    });
}

function showSection(section) {
    [sectionSettings, sectionAims, sectionGenerate, sectionDownload].forEach(s => {
        s.classList.add('hidden');
    });
    section.classList.remove('hidden');
    section.style.animation = 'none';
    // Trigger reflow for animation restart
    void section.offsetHeight;
    section.style.animation = 'card-in 0.5s ease-out both';
    window.scrollTo({ top: section.offsetTop - 100, behavior: 'smooth' });
}

function getSettings() {
    return {
        fontName: fontNameSelect.value,
        bodySize: bodySizeInput.value,
        headingSize: headingSizeInput.value,
        codeSize: codeSizeInput.value,
        captionSize: '10',
        imageWidth: imageWidthInput.value,
        terminalImgWidth: '600',
        outputFilename: outputFilename.value || 'Generated_Practical_File.docx',
    };
}

function saveToLocalStorage() {
    const data = {
        apiKey: apiKeyInput.value,
        model: modelSelect.value,
        mock: mockToggle.checked,
        fontName: fontNameSelect.value,
        bodySize: bodySizeInput.value,
        headingSize: headingSizeInput.value,
        codeSize: codeSizeInput.value,
        imageWidth: imageWidthInput.value,
        outputFilename: outputFilename.value,
        aims: aimsTextarea.value,
    };
    localStorage.setItem('practigen_settings', JSON.stringify(data));
}

function loadFromLocalStorage() {
    const raw = localStorage.getItem('practigen_settings');
    if (!raw) return;
    try {
        const data = JSON.parse(raw);
        if (data.apiKey) apiKeyInput.value = data.apiKey;
        if (data.model) modelSelect.value = data.model;
        if (data.mock !== undefined) {
            mockToggle.checked = data.mock;
            mockLabel.textContent = data.mock ? 'On' : 'Off';
        }
        if (data.fontName) fontNameSelect.value = data.fontName;
        if (data.bodySize) bodySizeInput.value = data.bodySize;
        if (data.headingSize) headingSizeInput.value = data.headingSize;
        if (data.codeSize) codeSizeInput.value = data.codeSize;
        if (data.imageWidth) imageWidthInput.value = data.imageWidth;
        if (data.outputFilename) outputFilename.value = data.outputFilename;
        if (data.aims) aimsTextarea.value = data.aims;
    } catch (e) { /* ignore */ }
}

// ========== Event Listeners ==========

// Toggle API key visibility
toggleKeyBtn.addEventListener('click', () => {
    const isPassword = apiKeyInput.type === 'password';
    apiKeyInput.type = isPassword ? 'text' : 'password';
    toggleKeyBtn.textContent = isPassword ? '🙈' : '👁️';
});

// Toggle mock mode label
mockToggle.addEventListener('change', () => {
    mockLabel.textContent = mockToggle.checked ? 'On' : 'Off';
});

// Toggle advanced settings
advancedBtn.addEventListener('click', () => {
    advancedPanel.classList.toggle('open');
    advancedBtn.textContent = advancedPanel.classList.contains('open') ? 'Advanced ▴' : 'Advanced ▾';
});

// File upload
fileUpload.addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (ev) => {
        aimsTextarea.value = ev.target.result;
        showToast(`Loaded "${file.name}"`, 'success');
    };
    reader.readAsText(file);
});

// Load sample aims
btnLoadSample.addEventListener('click', () => {
    aimsTextarea.value = `Install C compiler (GCC/Code::Blocks), set up IDE, compile and run the first "Hello, World!" program.
---
Write a Program to show the use to input (Scanf)/output (Printf) statements and block structure of C-program by highlighting the features of "stdio.h".
---
Write a program to add two numbers and display the sum.
---
Write a program to calculate the area and the circumference of a circle by using radius as the input provided by the user.
---
Write a Program to perform addition, subtraction, division and multiplication of two numbers given as input by the user.`;
    showToast('Sample aims loaded', 'info');
});

// ========== Navigation ==========

btnNextToAims.addEventListener('click', () => {
    saveToLocalStorage();
    setStep(2);
    showSection(sectionAims);
});

btnBackToSettings.addEventListener('click', () => {
    setStep(1);
    showSection(sectionSettings);
});

btnParse.addEventListener('click', async () => {
    const text = aimsTextarea.value.trim();
    if (!text) {
        showToast('Please enter at least one experiment aim', 'error');
        return;
    }

    btnParse.classList.add('loading');
    btnParse.disabled = true;

    try {
        const res = await fetch('/api/parse', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text }),
        });

        if (!res.ok) throw new Error(`Server error: ${res.status}`);
        const data = await res.json();

        if (data.error) throw new Error(data.error);

        parsedAims = data.aims;

        if (parsedAims.length === 0) {
            showToast('No experiments found. Check your separator (---)', 'error');
            return;
        }

        // Render experiment cards
        experimentsList.innerHTML = '';
        parsedAims.forEach((aim, i) => {
            const card = document.createElement('div');
            card.className = 'experiment-card';
            card.style.animationDelay = `${i * 0.06}s`;
            card.innerHTML = `
                <span class="exp-num">${i + 1}</span>
                <span class="exp-text">${escapeHtml(aim.length > 150 ? aim.slice(0, 150) + '...' : aim)}</span>
                <span class="exp-status">⏳</span>
            `;
            experimentsList.appendChild(card);
        });
        experimentCount.textContent = `${parsedAims.length} experiment${parsedAims.length > 1 ? 's' : ''}`;

        saveToLocalStorage();
        setStep(3);
        showSection(sectionGenerate);
        showToast(`Parsed ${parsedAims.length} experiments`, 'success');

    } catch (err) {
        showToast(`Parse failed: ${err.message}`, 'error');
    } finally {
        btnParse.classList.remove('loading');
        btnParse.disabled = false;
    }
});

btnBackToAims.addEventListener('click', () => {
    setStep(2);
    showSection(sectionAims);
});

// ========== Generate ==========
btnGenerate.addEventListener('click', async () => {
    if (parsedAims.length === 0) {
        showToast('No aims to generate', 'error');
        return;
    }

    const apiKey = apiKeyInput.value.trim();
    const mock = mockToggle.checked || !apiKey;

    if (!apiKey && !mockToggle.checked) {
        showToast('No API key provided — using Mock Mode', 'info');
    }

    btnGenerate.disabled = true;
    btnGenerate.classList.add('loading');
    btnBackToAims.disabled = true;

    progressContainer.classList.remove('hidden');
    generatedExperiments = [];

    const cards = experimentsList.querySelectorAll('.experiment-card');

    for (let i = 0; i < parsedAims.length; i++) {
        const aim = parsedAims[i];
        const pct = Math.round(((i) / parsedAims.length) * 100);
        progressFill.style.width = `${pct}%`;
        progressPercent.textContent = `${pct}%`;
        progressText.textContent = `Generating experiment ${i + 1} of ${parsedAims.length}...`;

        // Update card status
        if (cards[i]) {
            cards[i].querySelector('.exp-status').textContent = '🔄';
        }

        try {
            const res = await fetch('/api/generate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    aim,
                    api_key: apiKey,
                    model: modelSelect.value,
                    mock,
                }),
            });

            if (!res.ok) throw new Error(`Server error: ${res.status}`);
            const data = await res.json();
            if (data.error) throw new Error(data.error);

            generatedExperiments.push({ aim, ...data });

            if (cards[i]) {
                cards[i].querySelector('.exp-status').textContent = '✅';
            }
        } catch (err) {
            showToast(`Experiment ${i + 1} failed: ${err.message}`, 'error');
            // Push a fallback
            generatedExperiments.push({
                aim,
                concept: 'Generation failed — see error toast.',
                code: '// Error generating code',
                output: 'Error',
                caption: 'Error',
            });
            if (cards[i]) {
                cards[i].querySelector('.exp-status').textContent = '❌';
            }
        }
    }

    // Done
    progressFill.style.width = '100%';
    progressPercent.textContent = '100%';
    progressText.textContent = 'All experiments generated!';

    // Render results
    renderResults();

    btnGenerate.disabled = false;
    btnGenerate.classList.remove('loading');
    btnBackToAims.disabled = false;

    setStep(4);
    showSection(sectionDownload);
    showToast('Generation complete!', 'success');
});

function renderResults() {
    resultsList.innerHTML = '';
    generatedExperiments.forEach((exp, i) => {
        const card = document.createElement('div');
        card.className = 'result-card';
        card.style.animationDelay = `${i * 0.08}s`;
        card.innerHTML = `
            <div class="result-card-header" data-index="${i}">
                <h3>
                    <span class="exp-num">${i + 1}</span>
                    ${escapeHtml(exp.aim.length > 70 ? exp.aim.slice(0, 70) + '...' : exp.aim)}
                </h3>
                <span class="result-toggle">▾</span>
            </div>
            <div class="result-card-body" id="result-body-${i}">
                <div class="result-section">
                    <h4>Concept</h4>
                    <p>${escapeHtml(exp.concept)}</p>
                </div>
                <div class="result-section">
                    <h4>Code</h4>
                    <pre>${escapeHtml(exp.code)}</pre>
                </div>
                <div class="result-section result-output">
                    <h4>Terminal Output</h4>
                    <pre>${escapeHtml(exp.output)}</pre>
                </div>
                <div class="result-section">
                    <h4>Caption</h4>
                    <p>${escapeHtml(exp.caption)}</p>
                </div>
            </div>
        `;
        resultsList.appendChild(card);
    });

    // Add toggle listeners
    resultsList.querySelectorAll('.result-card-header').forEach(header => {
        header.addEventListener('click', () => {
            const idx = header.dataset.index;
            const body = $(`#result-body-${idx}`);
            const toggle = header.querySelector('.result-toggle');
            body.classList.toggle('open');
            toggle.classList.toggle('open');
        });
    });
}

// ========== Download ==========
btnDownload.addEventListener('click', async () => {
    if (generatedExperiments.length === 0) {
        showToast('No experiments to download', 'error');
        return;
    }

    btnDownload.disabled = true;
    btnDownload.classList.add('loading');

    try {
        const res = await fetch('/api/download', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                experiments: generatedExperiments,
                settings: getSettings(),
            }),
        });

        if (!res.ok) {
            const errData = await res.json().catch(() => ({}));
            throw new Error(errData.error || `Server error: ${res.status}`);
        }

        // Download the blob
        const blob = await res.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = getSettings().outputFilename;
        document.body.appendChild(a);
        a.click();
        a.remove();
        URL.revokeObjectURL(url);

        showToast('Document downloaded successfully!', 'success');
    } catch (err) {
        showToast(`Download failed: ${err.message}`, 'error');
    } finally {
        btnDownload.disabled = false;
        btnDownload.classList.remove('loading');
    }
});

btnBackToGenerate.addEventListener('click', () => {
    setStep(3);
    showSection(sectionGenerate);
});

// ========== Helpers ==========
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ========== Init ==========
loadFromLocalStorage();
