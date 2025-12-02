/**
 * RKC Photography - Frontend Application
 * 
 * Handles UI interactions and communicates with Python backend via PyWebView's JS-Python bridge.
 * All API calls are made through window.pywebview.api.methodName()
 */

// ==================== State Management ====================
const state = {
    config: {
        input_folder: '',
        output_folder: '',
        border_thickness: 0,
        border_color: '#FFFFFF',
        saturation: 100,  // 100 = original, 0 = grayscale, >100 = more saturated
        watermarks: [],  // Array of {path, position, opacity, scale, margin}
        filename_prefix: '',
        filename_suffix: '',
        overwrite_existing: false
    },
    previewImagePath: '',
    imageCount: 0,
    isProcessing: false,
    nextWatermarkId: 1
};

// ==================== DOM Elements ====================
const elements = {
    // Navigation
    navTabs: document.querySelectorAll('.nav-tab'),
    tabContents: document.querySelectorAll('.tab-content'),
    
    // Settings - Folders
    inputFolder: document.getElementById('input-folder'),
    outputFolder: document.getElementById('output-folder'),
    inputCount: document.getElementById('input-count'),
    btnSelectInput: document.getElementById('btn-select-input'),
    btnSelectOutput: document.getElementById('btn-select-output'),
    overwriteExisting: document.getElementById('overwrite-existing'),
    
    // Settings - Border
    borderThickness: document.getElementById('border-thickness'),
    borderThicknessValue: document.getElementById('border-thickness-value'),
    borderColor: document.getElementById('border-color'),
    borderColorHex: document.getElementById('border-color-hex'),
    colorPresets: document.querySelectorAll('.color-preset'),
    
    // Settings - Saturation
    saturation: document.getElementById('saturation'),
    saturationValue: document.getElementById('saturation-value'),
    saturationPresets: document.querySelectorAll('.saturation-preset'),
    
    // Settings - Watermarks
    watermarkList: document.getElementById('watermark-list'),
    btnAddWatermark: document.getElementById('btn-add-watermark'),
    
    // Settings - Filename
    filenamePrefix: document.getElementById('filename-prefix'),
    filenameSuffix: document.getElementById('filename-suffix'),
    filenameExample: document.getElementById('filename-example'),
    
    // Preview
    btnSelectPreviewImage: document.getElementById('btn-select-preview-image'),
    btnRefreshPreview: document.getElementById('btn-refresh-preview'),
    previewPlaceholder: document.getElementById('preview-placeholder'),
    previewImage: document.getElementById('preview-image'),
    previewLoading: document.getElementById('preview-loading'),
    previewInfo: document.getElementById('preview-info'),
    
    // Process
    summaryInput: document.getElementById('summary-input'),
    summaryOutput: document.getElementById('summary-output'),
    summaryCount: document.getElementById('summary-count'),
    summaryBorder: document.getElementById('summary-border'),
    summarySaturation: document.getElementById('summary-saturation'),
    summaryWatermark: document.getElementById('summary-watermark'),
    validationErrors: document.getElementById('validation-errors'),
    errorList: document.getElementById('error-list'),
    btnStartProcessing: document.getElementById('btn-start-processing'),
    
    // Progress
    progressSection: document.getElementById('progress-section'),
    progressStats: document.getElementById('progress-stats'),
    progressBar: document.getElementById('progress-bar'),
    currentFile: document.getElementById('current-file'),
    progressPercent: document.getElementById('progress-percent'),
    btnCancelProcessing: document.getElementById('btn-cancel-processing'),
    
    // Results
    resultsSection: document.getElementById('results-section'),
    resultsIcon: document.getElementById('results-icon'),
    resultsTitle: document.getElementById('results-title'),
    statSuccess: document.getElementById('stat-success'),
    statErrors: document.getElementById('stat-errors'),
    statSkipped: document.getElementById('stat-skipped'),
    btnOpenOutput: document.getElementById('btn-open-output'),
    btnProcessAgain: document.getElementById('btn-process-again'),
    errorDetails: document.getElementById('error-details'),
    errorLog: document.getElementById('error-log'),
    
    // Toast
    toastContainer: document.getElementById('toast-container')
};

// ==================== API Helper ====================
/**
 * Wait for PyWebView API to be ready
 */
async function waitForApi() {
    return new Promise((resolve) => {
        if (window.pywebview && window.pywebview.api) {
            resolve();
        } else {
            window.addEventListener('pywebviewready', resolve);
        }
    });
}

/**
 * Call a Python API method safely
 */
async function api(method, ...args) {
    await waitForApi();
    try {
        return await window.pywebview.api[method](...args);
    } catch (error) {
        console.error(`API error (${method}):`, error);
        showToast(`Error: ${error.message}`, 'error');
        throw error;
    }
}

// ==================== Toast Notifications ====================
function showToast(message, type = 'info', duration = 3000) {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    elements.toastContainer.appendChild(toast);
    
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(100%)';
        setTimeout(() => toast.remove(), 300);
    }, duration);
}

// ==================== Tab Navigation ====================
function switchTab(tabName) {
    elements.navTabs.forEach(tab => {
        tab.classList.toggle('active', tab.dataset.tab === tabName);
    });
    
    elements.tabContents.forEach(content => {
        content.classList.toggle('active', content.id === `${tabName}-tab`);
    });
    
    // Update summary when switching to process tab
    if (tabName === 'process') {
        updateProcessSummary();
    }
}

// ==================== Settings Sync ====================
function syncUIToState() {
    state.config.input_folder = elements.inputFolder.value;
    state.config.output_folder = elements.outputFolder.value;
    state.config.border_thickness = parseInt(elements.borderThicknessValue.value) || 0;
    state.config.border_color = elements.borderColor.value;
    
    // Note: Don't use || 100 because 0 is a valid saturation value (grayscale)
    const satVal = parseInt(elements.saturationValue.value);
    state.config.saturation = isNaN(satVal) ? 100 : satVal;
    
    state.config.filename_prefix = elements.filenamePrefix.value;
    state.config.filename_suffix = elements.filenameSuffix.value;
    state.config.overwrite_existing = elements.overwriteExisting.checked;
    
    // Watermarks are synced in real-time via their event handlers
}

function syncStateToUI() {
    elements.inputFolder.value = state.config.input_folder;
    elements.outputFolder.value = state.config.output_folder;
    elements.borderThickness.value = state.config.border_thickness;
    elements.borderThicknessValue.value = state.config.border_thickness;
    elements.borderColor.value = state.config.border_color;
    elements.borderColorHex.value = state.config.border_color;
    elements.saturation.value = state.config.saturation;
    elements.saturationValue.value = state.config.saturation;
    elements.filenamePrefix.value = state.config.filename_prefix;
    elements.filenameSuffix.value = state.config.filename_suffix;
    elements.overwriteExisting.checked = state.config.overwrite_existing;
    
    // Render watermarks
    renderWatermarkList();
    
    // Update saturation preset highlights
    updateSaturationPresets();
    
    updateFilenameExample();
    updateImageCount();
}

// ==================== Folder & File Selection ====================
async function selectInputFolder() {
    const folder = await api('select_input_folder');
    if (folder) {
        elements.inputFolder.value = folder;
        state.config.input_folder = folder;
        await updateImageCount();
        showToast('Input folder selected', 'success');
    }
}

async function selectOutputFolder() {
    const folder = await api('select_output_folder');
    if (folder) {
        elements.outputFolder.value = folder;
        state.config.output_folder = folder;
        showToast('Output folder selected', 'success');
    }
}

async function selectWatermarkFile() {
    const file = await api('select_watermark_file');
    if (file) {
        elements.watermarkFile.value = file;
        state.config.watermark_path = file;
        showToast('Watermark selected', 'success');
    }
}

function clearWatermark() {
    elements.watermarkFile.value = '';
    state.config.watermark_path = '';
}

async function updateImageCount() {
    if (state.config.input_folder) {
        const result = await api('count_images', state.config.input_folder);
        state.imageCount = result.count;
        elements.inputCount.textContent = result.count > 0 
            ? `${result.count} image${result.count !== 1 ? 's' : ''} found`
            : 'No supported images found';
    } else {
        state.imageCount = 0;
        elements.inputCount.textContent = '';
    }
}

// ==================== Border Settings ====================
function updateBorderThickness() {
    const value = elements.borderThickness.value;
    elements.borderThicknessValue.value = value;
    state.config.border_thickness = parseInt(value);
}

function updateBorderThicknessFromInput() {
    let value = parseInt(elements.borderThicknessValue.value) || 0;
    value = Math.max(0, Math.min(500, value));
    elements.borderThicknessValue.value = value;
    elements.borderThickness.value = Math.min(100, value);
    state.config.border_thickness = value;
}

function updateBorderColor(fromPicker = true) {
    if (fromPicker) {
        const color = elements.borderColor.value;
        elements.borderColorHex.value = color.toUpperCase();
        state.config.border_color = color;
    } else {
        let hex = elements.borderColorHex.value.trim();
        if (!hex.startsWith('#')) hex = '#' + hex;
        if (/^#[0-9A-Fa-f]{6}$/.test(hex)) {
            elements.borderColor.value = hex;
            state.config.border_color = hex;
        }
    }
}

function setColorPreset(color) {
    elements.borderColor.value = color;
    elements.borderColorHex.value = color.toUpperCase();
    state.config.border_color = color;
}

// ==================== Saturation Settings ====================
function updateSaturation() {
    const value = elements.saturation.value;
    elements.saturationValue.value = value;
    state.config.saturation = parseInt(value);
    updateSaturationPresets();
}

function updateSaturationFromInput() {
    let value = parseInt(elements.saturationValue.value);
    // Use 100 as default only if input is invalid (NaN), not if it's 0
    if (isNaN(value)) value = 100;
    value = Math.max(0, Math.min(200, value));
    elements.saturationValue.value = value;
    elements.saturation.value = value;
    state.config.saturation = value;
    updateSaturationPresets();
}

function setSaturationPreset(value) {
    elements.saturation.value = value;
    elements.saturationValue.value = value;
    state.config.saturation = parseInt(value);
    updateSaturationPresets();
}

function updateSaturationPresets() {
    const currentValue = state.config.saturation;
    elements.saturationPresets.forEach(preset => {
        const presetValue = parseInt(preset.dataset.value);
        preset.classList.toggle('active', presetValue === currentValue);
    });
}

// ==================== Watermark Management ====================
function createWatermarkItem(watermark, index) {
    const filename = watermark.path ? watermark.path.split(/[\\/]/).pop() : 'No file selected';
    
    return `
        <div class="watermark-item" data-watermark-id="${watermark.id}">
            <div class="watermark-item-header">
                <div class="watermark-item-title">
                    <span class="watermark-item-number">${index + 1}</span>
                    <span class="watermark-item-filename">${filename}</span>
                </div>
                <button class="btn-remove-watermark" data-id="${watermark.id}" title="Remove watermark">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <line x1="18" y1="6" x2="6" y2="18"/>
                        <line x1="6" y1="6" x2="18" y2="18"/>
                    </svg>
                </button>
            </div>
            <div class="watermark-item-content">
                <div class="watermark-item-left">
                    <div class="watermark-file-input">
                        <input type="text" value="${watermark.path}" placeholder="Select watermark image..." readonly data-id="${watermark.id}" class="watermark-path-input">
                        <button class="btn-icon btn-select-wm-file" data-id="${watermark.id}" title="Browse">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4M7 10l5 5 5-5M12 15V3"/>
                            </svg>
                        </button>
                    </div>
                    <div class="position-grid" data-id="${watermark.id}">
                        ${['top-left', 'top', 'top-right', 'left', 'center', 'right', 'bottom-left', 'bottom', 'bottom-right'].map(pos => `
                            <button class="position-btn ${watermark.position === pos ? 'active' : ''}" data-position="${pos}" data-id="${watermark.id}" title="${pos}">
                                <span class="position-preview"><span class="dot ${pos}"></span></span>
                            </button>
                        `).join('')}
                    </div>
                </div>
                <div class="watermark-item-right">
                    <div class="watermark-slider-group">
                        <label>Opacity</label>
                        <div class="range-input">
                            <input type="range" min="0" max="100" value="${Math.round(watermark.opacity * 100)}" data-id="${watermark.id}" class="wm-opacity-slider">
                            <span class="range-value wm-opacity-value" data-id="${watermark.id}">${Math.round(watermark.opacity * 100)}%</span>
                        </div>
                    </div>
                    <div class="watermark-slider-group">
                        <label>Size (% of image)</label>
                        <div class="range-input">
                            <input type="range" min="5" max="80" value="${watermark.scale}" data-id="${watermark.id}" class="wm-scale-slider">
                            <span class="range-value wm-scale-value" data-id="${watermark.id}">${watermark.scale}%</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
}

function renderWatermarkList() {
    if (state.config.watermarks.length === 0) {
        elements.watermarkList.innerHTML = `
            <div class="watermark-empty">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                    <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
                </svg>
                <p>No watermarks added yet</p>
            </div>
        `;
    } else {
        elements.watermarkList.innerHTML = state.config.watermarks
            .map((wm, i) => createWatermarkItem(wm, i))
            .join('');
    }
    
    // Attach event listeners to new elements
    attachWatermarkListeners();
}

function attachWatermarkListeners() {
    // Remove buttons
    document.querySelectorAll('.btn-remove-watermark').forEach(btn => {
        btn.addEventListener('click', () => removeWatermark(parseInt(btn.dataset.id)));
    });
    
    // File selection buttons
    document.querySelectorAll('.btn-select-wm-file').forEach(btn => {
        btn.addEventListener('click', () => selectWatermarkFile(parseInt(btn.dataset.id)));
    });
    
    // File input click
    document.querySelectorAll('.watermark-path-input').forEach(input => {
        input.addEventListener('click', () => selectWatermarkFile(parseInt(input.dataset.id)));
    });
    
    // Position buttons
    document.querySelectorAll('.watermark-item .position-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const id = parseInt(btn.dataset.id);
            const position = btn.dataset.position;
            setWatermarkPosition(id, position);
        });
    });
    
    // Opacity sliders
    document.querySelectorAll('.wm-opacity-slider').forEach(slider => {
        slider.addEventListener('input', () => {
            const id = parseInt(slider.dataset.id);
            updateWatermarkOpacity(id, parseInt(slider.value));
        });
    });
    
    // Scale sliders
    document.querySelectorAll('.wm-scale-slider').forEach(slider => {
        slider.addEventListener('input', () => {
            const id = parseInt(slider.dataset.id);
            updateWatermarkScale(id, parseInt(slider.value));
        });
    });
}

function addWatermark() {
    const newWatermark = {
        id: state.nextWatermarkId++,
        path: '',
        position: 'center',
        opacity: 0.5,
        scale: 25,
        margin: 20
    };
    state.config.watermarks.push(newWatermark);
    renderWatermarkList();
}

function removeWatermark(id) {
    state.config.watermarks = state.config.watermarks.filter(wm => wm.id !== id);
    renderWatermarkList();
}

async function selectWatermarkFile(id) {
    const file = await api('select_watermark_file');
    if (file) {
        const wm = state.config.watermarks.find(w => w.id === id);
        if (wm) {
            wm.path = file;
            renderWatermarkList();
            showToast('Watermark selected', 'success');
        }
    }
}

function setWatermarkPosition(id, position) {
    const wm = state.config.watermarks.find(w => w.id === id);
    if (wm) {
        wm.position = position;
        // Update UI
        const grid = document.querySelector(`.position-grid[data-id="${id}"]`);
        if (grid) {
            grid.querySelectorAll('.position-btn').forEach(btn => {
                btn.classList.toggle('active', btn.dataset.position === position);
            });
        }
    }
}

function updateWatermarkOpacity(id, value) {
    const wm = state.config.watermarks.find(w => w.id === id);
    if (wm) {
        wm.opacity = value / 100;
        const valueEl = document.querySelector(`.wm-opacity-value[data-id="${id}"]`);
        if (valueEl) valueEl.textContent = `${value}%`;
    }
}

function updateWatermarkScale(id, value) {
    const wm = state.config.watermarks.find(w => w.id === id);
    if (wm) {
        wm.scale = value;
        const valueEl = document.querySelector(`.wm-scale-value[data-id="${id}"]`);
        if (valueEl) valueEl.textContent = `${value}%`;
    }
}

// ==================== Filename Preview ====================
function updateFilenameExample() {
    const prefix = elements.filenamePrefix.value;
    const suffix = elements.filenameSuffix.value;
    elements.filenameExample.textContent = `${prefix}photo${suffix}.jpg`;
}

// ==================== Preview ====================
async function selectPreviewImage() {
    const file = await api('select_preview_image');
    if (file) {
        state.previewImagePath = file;
        elements.btnRefreshPreview.disabled = false;
        await generatePreview();
    }
}

async function generatePreview() {
    if (!state.previewImagePath) {
        showToast('Select an image first', 'warning');
        return;
    }
    
    syncUIToState();
    
    // Show loading
    elements.previewPlaceholder.classList.add('hidden');
    elements.previewImage.classList.add('hidden');
    elements.previewLoading.classList.remove('hidden');
    
    try {
        const result = await api('generate_preview', state.config, state.previewImagePath);
        
        if (result.success) {
            elements.previewImage.src = result.image_data;
            elements.previewImage.classList.remove('hidden');
            elements.previewInfo.textContent = state.previewImagePath.split(/[\\/]/).pop();
        } else {
            elements.previewPlaceholder.classList.remove('hidden');
            showToast(`Preview error: ${result.error}`, 'error');
        }
    } catch (error) {
        elements.previewPlaceholder.classList.remove('hidden');
    } finally {
        elements.previewLoading.classList.add('hidden');
    }
}

// ==================== Process Tab ====================
function updateProcessSummary() {
    syncUIToState();
    
    // Update summary values
    elements.summaryInput.textContent = state.config.input_folder || 'Not selected';
    elements.summaryOutput.textContent = state.config.output_folder || 'Not selected';
    elements.summaryCount.textContent = state.imageCount;
    
    // Border summary
    if (state.config.border_thickness > 0) {
        elements.summaryBorder.innerHTML = `
            <span style="display:inline-block;width:12px;height:12px;background:${state.config.border_color};border:1px solid #333;border-radius:2px;vertical-align:middle;margin-right:4px;"></span>
            ${state.config.border_thickness}px
        `;
    } else {
        elements.summaryBorder.textContent = 'None';
    }
    
    // Saturation summary
    if (state.config.saturation !== 100) {
        let satLabel = '';
        if (state.config.saturation === 0) {
            satLabel = 'Grayscale (0)';
        } else if (state.config.saturation < 100) {
            satLabel = `Reduced (${state.config.saturation})`;
        } else {
            satLabel = `Enhanced (${state.config.saturation})`;
        }
        elements.summarySaturation.textContent = satLabel;
    } else {
        elements.summarySaturation.textContent = 'Original (100)';
    }
    
    // Watermark summary
    const activeWatermarks = state.config.watermarks.filter(wm => wm.path);
    if (activeWatermarks.length > 0) {
        elements.summaryWatermark.textContent = `${activeWatermarks.length} watermark${activeWatermarks.length > 1 ? 's' : ''}`;
    } else {
        elements.summaryWatermark.textContent = 'None';
    }
}

async function validateAndProcess() {
    syncUIToState();
    
    // Validate configuration
    const validation = await api('validate_config', state.config);
    
    if (!validation.valid) {
        // Show errors
        elements.validationErrors.classList.remove('hidden');
        elements.errorList.innerHTML = validation.errors
            .map(err => `<li>${err}</li>`)
            .join('');
        return;
    }
    
    // Hide validation errors
    elements.validationErrors.classList.add('hidden');
    
    // Check if there are images to process
    if (state.imageCount === 0) {
        showToast('No images to process', 'warning');
        return;
    }
    
    // Start processing
    startProcessing();
}

async function startProcessing() {
    state.isProcessing = true;
    
    // Show progress section, hide others
    elements.progressSection.classList.remove('hidden');
    elements.resultsSection.classList.add('hidden');
    elements.btnStartProcessing.disabled = true;
    
    // Reset progress display
    elements.progressBar.style.width = '0%';
    elements.progressStats.textContent = '0 / 0';
    elements.progressPercent.textContent = '0%';
    elements.currentFile.textContent = 'Starting...';
    
    // Start processing
    const result = await api('start_processing', state.config);
    
    if (!result.success) {
        showToast(`Error: ${result.error}`, 'error');
        resetProcessingUI();
    }
}

async function cancelProcessing() {
    await api('cancel_processing');
    showToast('Processing cancelled', 'warning');
}

function resetProcessingUI() {
    state.isProcessing = false;
    elements.progressSection.classList.add('hidden');
    elements.btnStartProcessing.disabled = false;
}

// ==================== Progress Callbacks ====================
window.onProcessingProgress = function(progress) {
    elements.progressBar.style.width = `${progress.progress_percent}%`;
    elements.progressStats.textContent = `${progress.processed_count} / ${progress.total_files}`;
    elements.progressPercent.textContent = `${Math.round(progress.progress_percent)}%`;
    elements.currentFile.textContent = progress.current_file || '';
};

window.onProcessingComplete = function(progress) {
    state.isProcessing = false;
    
    // Hide progress, show results
    elements.progressSection.classList.add('hidden');
    elements.resultsSection.classList.remove('hidden');
    elements.btnStartProcessing.disabled = false;
    
    // Update results
    const hasErrors = progress.error_count > 0 || progress.state === 'cancelled' || progress.state === 'error';
    
    elements.resultsIcon.className = `results-icon ${hasErrors ? 'error' : 'success'}`;
    elements.resultsIcon.innerHTML = hasErrors
        ? '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>'
        : '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 11-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>';
    
    if (progress.state === 'cancelled') {
        elements.resultsTitle.textContent = 'Processing Cancelled';
    } else if (progress.state === 'error') {
        elements.resultsTitle.textContent = 'Processing Failed';
    } else {
        elements.resultsTitle.textContent = progress.error_count > 0 
            ? 'Completed with Errors' 
            : 'Processing Complete';
    }
    
    elements.statSuccess.textContent = progress.success_count;
    elements.statErrors.textContent = progress.error_count;
    elements.statSkipped.textContent = progress.skipped_count;
    
    // Show error details if any
    if (progress.errors && progress.errors.length > 0) {
        elements.errorDetails.classList.remove('hidden');
        elements.errorLog.innerHTML = progress.errors
            .map(err => `<div class="error-log-entry"><span class="error-log-file">${err.file}:</span><span class="error-log-message">${err.error}</span></div>`)
            .join('');
    } else {
        elements.errorDetails.classList.add('hidden');
    }
    
    // Show success toast
    if (progress.success_count > 0 && progress.state === 'completed') {
        showToast(`Successfully processed ${progress.success_count} image${progress.success_count !== 1 ? 's' : ''}`, 'success');
    }
};

async function openOutputFolder() {
    if (state.config.output_folder) {
        await api('open_folder', state.config.output_folder);
    }
}

function processAgain() {
    elements.resultsSection.classList.add('hidden');
    switchTab('settings');
}

// ==================== Initialization ====================
async function init() {
    console.log('Initializing RKC Photography...');
    
    // Wait for PyWebView API
    await waitForApi();
    console.log('PyWebView API ready');
    
    // Load saved configuration
    try {
        const savedConfig = await api('load_config');
        Object.assign(state.config, savedConfig);
        syncStateToUI();
    } catch (error) {
        console.log('No saved config found, using defaults');
    }
    
    // Set up event listeners
    setupEventListeners();
    
    console.log('Initialization complete');
}

function setupEventListeners() {
    // Navigation
    elements.navTabs.forEach(tab => {
        tab.addEventListener('click', () => switchTab(tab.dataset.tab));
    });
    
    // Folder selection
    elements.btnSelectInput.addEventListener('click', selectInputFolder);
    elements.btnSelectOutput.addEventListener('click', selectOutputFolder);
    elements.inputFolder.addEventListener('click', selectInputFolder);
    elements.outputFolder.addEventListener('click', selectOutputFolder);
    elements.overwriteExisting.addEventListener('change', () => {
        state.config.overwrite_existing = elements.overwriteExisting.checked;
    });
    
    // Border settings
    elements.borderThickness.addEventListener('input', updateBorderThickness);
    elements.borderThicknessValue.addEventListener('change', updateBorderThicknessFromInput);
    elements.borderColor.addEventListener('input', () => updateBorderColor(true));
    elements.borderColorHex.addEventListener('change', () => updateBorderColor(false));
    elements.colorPresets.forEach(preset => {
        preset.addEventListener('click', () => setColorPreset(preset.dataset.color));
    });
    
    // Saturation settings
    elements.saturation.addEventListener('input', updateSaturation);
    elements.saturationValue.addEventListener('change', updateSaturationFromInput);
    elements.saturationPresets.forEach(preset => {
        preset.addEventListener('click', () => setSaturationPreset(preset.dataset.value));
    });
    
    // Watermark settings
    elements.btnAddWatermark.addEventListener('click', addWatermark);
    
    // Initial render of watermark list
    renderWatermarkList();
    
    // Filename settings
    elements.filenamePrefix.addEventListener('input', updateFilenameExample);
    elements.filenameSuffix.addEventListener('input', updateFilenameExample);
    
    // Preview
    elements.btnSelectPreviewImage.addEventListener('click', selectPreviewImage);
    elements.btnRefreshPreview.addEventListener('click', generatePreview);
    
    // Process
    elements.btnStartProcessing.addEventListener('click', validateAndProcess);
    elements.btnCancelProcessing.addEventListener('click', cancelProcessing);
    elements.btnOpenOutput.addEventListener('click', openOutputFolder);
    elements.btnProcessAgain.addEventListener('click', processAgain);
}

// Start the application
init();

