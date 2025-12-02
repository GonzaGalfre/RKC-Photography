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
        watermark_path: '',
        watermark_position: 'center',
        watermark_opacity: 0.5,
        watermark_scale: 25,
        watermark_margin: 20,
        filename_prefix: '',
        filename_suffix: '',
        overwrite_existing: false
    },
    previewImagePath: '',
    imageCount: 0,
    isProcessing: false
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
    
    // Settings - Watermark
    watermarkFile: document.getElementById('watermark-file'),
    btnSelectWatermark: document.getElementById('btn-select-watermark'),
    btnClearWatermark: document.getElementById('btn-clear-watermark'),
    positionBtns: document.querySelectorAll('.position-btn'),
    watermarkOpacity: document.getElementById('watermark-opacity'),
    watermarkOpacityValue: document.getElementById('watermark-opacity-value'),
    watermarkScale: document.getElementById('watermark-scale'),
    watermarkScaleValue: document.getElementById('watermark-scale-value'),
    
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
    state.config.watermark_path = elements.watermarkFile.value;
    state.config.watermark_opacity = parseInt(elements.watermarkOpacity.value) / 100;
    state.config.watermark_scale = parseInt(elements.watermarkScale.value);
    state.config.filename_prefix = elements.filenamePrefix.value;
    state.config.filename_suffix = elements.filenameSuffix.value;
    state.config.overwrite_existing = elements.overwriteExisting.checked;
    
    // Get active position
    const activePosition = document.querySelector('.position-btn.active');
    if (activePosition) {
        state.config.watermark_position = activePosition.dataset.position;
    }
}

function syncStateToUI() {
    elements.inputFolder.value = state.config.input_folder;
    elements.outputFolder.value = state.config.output_folder;
    elements.borderThickness.value = state.config.border_thickness;
    elements.borderThicknessValue.value = state.config.border_thickness;
    elements.borderColor.value = state.config.border_color;
    elements.borderColorHex.value = state.config.border_color;
    elements.watermarkFile.value = state.config.watermark_path;
    elements.watermarkOpacity.value = Math.round(state.config.watermark_opacity * 100);
    elements.watermarkOpacityValue.textContent = `${Math.round(state.config.watermark_opacity * 100)}%`;
    elements.watermarkScale.value = state.config.watermark_scale;
    elements.watermarkScaleValue.textContent = `${state.config.watermark_scale}%`;
    elements.filenamePrefix.value = state.config.filename_prefix;
    elements.filenameSuffix.value = state.config.filename_suffix;
    elements.overwriteExisting.checked = state.config.overwrite_existing;
    
    // Update position buttons
    elements.positionBtns.forEach(btn => {
        btn.classList.toggle('active', btn.dataset.position === state.config.watermark_position);
    });
    
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

// ==================== Watermark Settings ====================
function setWatermarkPosition(position) {
    elements.positionBtns.forEach(btn => {
        btn.classList.toggle('active', btn.dataset.position === position);
    });
    state.config.watermark_position = position;
}

function updateWatermarkOpacity() {
    const value = elements.watermarkOpacity.value;
    elements.watermarkOpacityValue.textContent = `${value}%`;
    state.config.watermark_opacity = parseInt(value) / 100;
}

function updateWatermarkScale() {
    const value = elements.watermarkScale.value;
    elements.watermarkScaleValue.textContent = `${value}%`;
    state.config.watermark_scale = parseInt(value);
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
    
    // Watermark summary
    if (state.config.watermark_path) {
        const filename = state.config.watermark_path.split(/[\\/]/).pop();
        elements.summaryWatermark.textContent = `${filename} (${state.config.watermark_position})`;
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
    
    // Watermark settings
    elements.btnSelectWatermark.addEventListener('click', selectWatermarkFile);
    elements.watermarkFile.addEventListener('click', selectWatermarkFile);
    elements.btnClearWatermark.addEventListener('click', clearWatermark);
    elements.positionBtns.forEach(btn => {
        btn.addEventListener('click', () => setWatermarkPosition(btn.dataset.position));
    });
    elements.watermarkOpacity.addEventListener('input', updateWatermarkOpacity);
    elements.watermarkScale.addEventListener('input', updateWatermarkScale);
    
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

