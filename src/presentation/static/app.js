const urlInput = document.getElementById('urlInput');
const downloadBtn = document.getElementById('downloadBtn');
const openFolderBtn = document.getElementById('openFolderBtn');
const queueList = document.getElementById('queueList');
const queueCount = document.getElementById('queueCount');
const emptyState = document.getElementById('emptyState');
const selectionSection = document.getElementById('selectionSection');
const mediaGrid = document.getElementById('mediaGrid');
const selectAllBtn = document.getElementById('selectAllBtn');
const downloadSelectedBtn = document.getElementById('downloadSelectedBtn');
const selectedCount = document.getElementById('selectedCount');
const enhanceSelectedBtn = document.getElementById('enhanceSelectedBtn');
const selectedCountEnhance = document.getElementById('selectedCountEnhance');
const aiModal = document.getElementById('aiModal');
const closeAiModalBtn = document.getElementById('closeAiModalBtn');
const confirmAiBtn = document.getElementById('confirmAiBtn');
const aiPresetSelect = document.getElementById('aiPresetSelect');
const aiColorBoostToggle = document.getElementById('aiColorBoostToggle');

// New Settings Elements
const toggleSettingsBtn = document.getElementById('toggleSettingsBtn');
const settingsPanel = document.getElementById('settingsPanel');
const formatSelect = document.getElementById('formatSelect');
const playlistToggle = document.getElementById('playlistToggle');
const saveCookiesBtn = document.getElementById('saveCookiesBtn');
const cookiesInput = document.getElementById('cookiesInput');

// Advanced Settings Logic
if (toggleSettingsBtn) {
    toggleSettingsBtn.addEventListener('click', () => {
        settingsPanel.classList.toggle('hidden');
    });
}

if (saveCookiesBtn) {
    saveCookiesBtn.addEventListener('click', async () => {
        const content = cookiesInput.value.trim();
        if (!content) return;
        
        saveCookiesBtn.textContent = 'Saving...';
        saveCookiesBtn.disabled = true;
        
        try {
            const res = await fetch('/api/settings/cookies', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ cookie_content: content })
            });
            if (res.ok) {
                saveCookiesBtn.textContent = 'Saved!';
                saveCookiesBtn.classList.replace('text-brand-300', 'text-emerald-400');
                saveCookiesBtn.classList.replace('border-brand-500/30', 'border-emerald-500/30');
                setTimeout(() => {
                    saveCookiesBtn.textContent = 'Save Cookies';
                    saveCookiesBtn.classList.replace('text-emerald-400', 'text-brand-300');
                    saveCookiesBtn.classList.replace('border-emerald-500/30', 'border-brand-500/30');
                }, 2000);
            } else {
                showToast('Failed to save cookies.', 'error');
                saveCookiesBtn.textContent = 'Save Cookies';
            }
        } catch(e) {
            showToast('Error connecting to server.', 'error');
            saveCookiesBtn.textContent = 'Save Cookies';
        }
        saveCookiesBtn.disabled = false;
    });
}

// UI State
let activeDownloads = new Map();
let extractedMediaItems = [];
let selectedUrls = new Set();

// Establish WebSocket connection
const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
const ws = new WebSocket(`${protocol}//${window.location.host}/ws/progress`);

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    updateQueueItem(data);
};

ws.onclose = () => {
    console.warn("WebSocket disconnected. Progress updates will be unavailable.");
};

// Auto-detect clipboard URLs
window.addEventListener('focus', async () => {
    try {
        const text = await navigator.clipboard.readText();
        if (text && /^https?:\/\//i.test(text.trim())) {
            if (!urlInput.value.includes(text.trim())) {
                urlInput.value = urlInput.value ? `${urlInput.value}\n${text.trim()}` : text.trim();
            }
        }
    } catch (err) {
        // Ignore clipboard read errors
    }
});

// Open Folder
openFolderBtn.addEventListener('click', async () => {
    try {
        await fetch('/api/open-folder', { method: 'POST' });
    } catch (e) {
        console.error("Failed to open folder", e);
    }
});

function renderMediaGrid() {
    mediaGrid.innerHTML = '';
    extractedMediaItems.forEach(item => {
        const isSelected = selectedUrls.has(item.url);
        const div = document.createElement('div');
        div.className = `relative aspect-square rounded-xl overflow-hidden cursor-pointer border-2 transition-all duration-200 ${isSelected ? 'border-brand-500 scale-95 shadow-[0_0_15px_rgba(99,102,241,0.5)]' : 'border-transparent hover:border-white/20'}`;
        
        div.innerHTML = `
            <img src="${item.thumbnail}" class="w-full h-full object-cover" onerror="this.src='data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIxMDAlIiBoZWlnaHQ9IjEwMCUiPjxyZWN0IHdpZHRoPSIxMDAlIiBoZWlnaHQ9IjEwMCUiIGZpbGw9IiMzMzMiLz48dGV4dCB4PSI1MCUiIHk9IjUwJSIgZm9udC1zaXplPSIyMCIgZmlsbD0id2hpdGUiIHRleHQtYW5jaG9yPSJtaWRkbGUiIGRvbWluYW50LWJhc2VsaW5lPSJtaWRkbGUiPk5vIFRodW1iPC90ZXh0Pjwvc3ZnPg=='"/>
            <div class="absolute top-2 right-2 bg-black/60 backdrop-blur-md text-xs font-bold px-2 py-1 rounded-md uppercase border border-white/10">${item.type}</div>
            ${isSelected ? '<div class="absolute top-2 left-2 bg-brand-500 text-white rounded-full p-1"><svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7"></path></svg></div>' : ''}
        `;
        
        div.onclick = () => {
            if (selectedUrls.has(item.url)) {
                selectedUrls.delete(item.url);
            } else {
                selectedUrls.add(item.url);
            }
            selectedCount.textContent = selectedUrls.size;
            if(selectedCountEnhance) selectedCountEnhance.textContent = selectedUrls.size;
            renderMediaGrid();
        };
        
        mediaGrid.appendChild(div);
    });
}

selectAllBtn.onclick = () => {
    if (selectedUrls.size === extractedMediaItems.length) {
        selectedUrls.clear(); // Deselect all if all are selected
    } else {
        extractedMediaItems.forEach(i => selectedUrls.add(i.url));
    }
    selectedCount.textContent = selectedUrls.size;
    if(selectedCountEnhance) selectedCountEnhance.textContent = selectedUrls.size;
    renderMediaGrid();
};

downloadSelectedBtn.onclick = async () => {
    if (selectedUrls.size === 0) return;
    
    const urlsToDownload = Array.from(selectedUrls);
    
    // Create pending queue items
    urlsToDownload.forEach(url => {
        const tempId = String(Math.random());
        updateQueueItem({
            id: tempId,
            url: url,
            status: 'pending',
            progress_percentage: 0,
            tier_used: 1
        });
    });

    try {
        await fetch('/api/download', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                urls: urlsToDownload,
                enhance_images: false,
                color_boost: false,
                format_type: formatSelect ? formatSelect.value : "video",
                is_playlist: playlistToggle ? playlistToggle.checked : false
            })
        });
        
        selectedUrls.clear();
        selectedCount.textContent = '0';
        selectedCountEnhance.textContent = '0';
        renderMediaGrid();
        downloadSelectedBtn.innerHTML = `<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"></path></svg> Download Raw (<span id="selectedCount">0</span>)`;
        enhanceSelectedBtn.innerHTML = `<svg class="w-4 h-4 text-brand-300" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path></svg> ✨ AI Enhance (<span id="selectedCountEnhance">0</span>)`;
        
    } catch (e) {
        console.error("Failed to start download", e);
        showToast("Failed to connect to the server.", 'error');
    }
};

// AI Modal Logic
enhanceSelectedBtn.onclick = () => {
    if (selectedUrls.size === 0) return;
    aiModal.classList.remove('hidden');
    // small delay for transition
    setTimeout(() => {
        aiModal.classList.remove('opacity-0');
        aiModal.classList.add('opacity-100');
    }, 10);
};

closeAiModalBtn.onclick = () => {
    aiModal.classList.remove('opacity-100');
    aiModal.classList.add('opacity-0');
    setTimeout(() => {
        aiModal.classList.add('hidden');
    }, 300);
};

confirmAiBtn.onclick = async () => {
    if (selectedUrls.size === 0) return;
    
    closeAiModalBtn.onclick(); // close modal
    
    const urlsToDownload = Array.from(selectedUrls);
    
    // Create pending queue items
    urlsToDownload.forEach(url => {
        const tempId = String(Math.random());
        updateQueueItem({
            id: tempId,
            url: url,
            status: 'pending',
            progress_percentage: 0,
            tier_used: 1
        });
    });

    try {
        await fetch('/api/download', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                urls: urlsToDownload,
                enhance_images: true, // TRIGGER AI
                color_boost: aiColorBoostToggle ? aiColorBoostToggle.checked : false,
                format_type: formatSelect ? formatSelect.value : "video",
                is_playlist: playlistToggle ? playlistToggle.checked : false
            })
        });
        
        selectedUrls.clear();
        selectedCount.textContent = '0';
        selectedCountEnhance.textContent = '0';
        renderMediaGrid();
        downloadSelectedBtn.innerHTML = `<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"></path></svg> Download Raw (<span id="selectedCount">0</span>)`;
        enhanceSelectedBtn.innerHTML = `<svg class="w-4 h-4 text-brand-300" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path></svg> ✨ AI Enhance (<span id="selectedCountEnhance">0</span>)`;
        
    } catch (e) {
        console.error("Failed to start AI download", e);
        showToast("Failed to connect to the server.", 'error');
    }
};

// Analyze Media (changed from Start Download)
downloadBtn.addEventListener('click', async () => {
    const text = urlInput.value.trim();
    if (!text) return;

    const urls = text.split('\n')
        .map(u => u.trim())
        .filter(u => /^https?:\/\//i.test(u));

    if (urls.length === 0) return;

    urlInput.value = '';
    downloadBtn.innerHTML = '<svg class="animate-spin w-5 h-5" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg> Analyzing...';
    downloadBtn.disabled = true;

    try {
        const res = await fetch('/api/analyze', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                urls,
                format_type: formatSelect ? formatSelect.value : "video",
                is_playlist: playlistToggle ? playlistToggle.checked : false
            }) // Sending the list of urls (backend currently only processes the first)
        });
        
        const data = await res.json();
        
        if (data.items && data.items.length > 0) {
            extractedMediaItems = data.items;
            selectedUrls.clear();
            extractedMediaItems.forEach(i => selectedUrls.add(i.url)); // Select all by default
            selectedCount.textContent = selectedUrls.size;
            selectedCountEnhance.textContent = selectedUrls.size;
            
            renderMediaGrid();
            selectionSection.classList.remove('hidden');
        } else {
            showToast(data.error || "No media found at this URL.", 'error');
        }
    } catch (e) {
        console.error("Failed to analyze URL", e);
        showToast("Failed to analyze the URL. Please check the server.", 'error');
    } finally {
        downloadBtn.disabled = false;
        downloadBtn.innerHTML = '<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"></path></svg> Fetch Media';
    }
});

function getStatusColor(status) {
    switch(status) {
        case 'pending': return 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20';
        case 'downloading': return 'bg-brand-500/10 text-brand-400 border-brand-500/20 pulse-ring';
        case 'processing': return 'bg-purple-500/10 text-purple-400 border-purple-500/20';
        case 'completed': return 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20';
        case 'failed': return 'bg-rose-500/10 text-rose-400 border-rose-500/20';
        default: return 'bg-white/5 text-white/50 border-white/10';
    }
}

function updateQueueItem(data) {
    if (emptyState && emptyState.style.display !== 'none') {
        emptyState.style.display = 'none';
    }

    let el = document.getElementById(`item-${data.id}`);
    
    if (!el) {
        const pendingItems = Array.from(document.querySelectorAll('.queue-item-pending'));
        const match = pendingItems.find(i => i.dataset.url === data.url);
        
        if (match && data.id !== match.dataset.id) {
            match.id = `item-${data.id}`;
            match.dataset.id = data.id;
            match.classList.remove('queue-item-pending');
            el = match;
        } else {
            el = document.createElement('div');
            el.id = `item-${data.id}`;
            el.dataset.id = data.id;
            el.dataset.url = data.url;
            el.className = `glass-item rounded-2xl p-5 animate-slide-in flex flex-col gap-4 relative overflow-hidden group ${data.status === 'pending' ? 'queue-item-pending' : ''}`;
            queueList.insertBefore(el, queueList.firstChild);
        }
    }

    activeDownloads.set(data.id, data);
    updateCount();

    const shortUrl = data.url.length > 60 ? data.url.substring(0, 60) + '...' : data.url;
    const isError = data.status === 'failed';
    const isDone = data.status === 'completed';
    const isWorking = data.status === 'downloading' || data.status === 'processing';

    el.innerHTML = `
        <div class="absolute inset-0 bg-gradient-to-r from-transparent via-white/[0.02] to-transparent -translate-x-full group-hover:translate-x-full transition-transform duration-1000"></div>
        <div class="flex justify-between items-start gap-5 relative z-10">
            <div class="flex-1 min-w-0">
                <p class="text-base font-semibold text-white/95 truncate" title="${data.url}">${shortUrl}</p>
                <div class="flex flex-wrap items-center gap-3 mt-2 text-xs font-medium text-white/50">
                    <span class="flex items-center gap-1.5 ${getStatusColor(data.status)} px-2.5 py-1 rounded-md border capitalize transition-colors">
                        ${isWorking ? '<svg class="animate-spin w-3.5 h-3.5" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>' : ''}
                        ${data.status}
                    </span>
                    ${data.speed_mbps ? `<span class="bg-white/5 px-2 py-1 rounded-md flex items-center gap-1"><svg class="w-3 h-3 text-white/40" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 14l-7 7m0 0l-7-7m7 7V3"></path></svg>${data.speed_mbps.toFixed(2)} MB/s</span>` : ''}
                    ${data.eta_seconds ? `<span class="bg-white/5 px-2 py-1 rounded-md flex items-center gap-1"><svg class="w-3 h-3 text-white/40" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>${data.eta_seconds}s left</span>` : ''}
                    <span class="bg-white/5 px-2 py-1 rounded-md text-brand-400" title="Extraction Tier">T${data.tier_used || 1} Engine</span>
                </div>
                ${isError && data.error_message ? `
                <div class="mt-3 bg-rose-500/10 border border-rose-500/20 p-3 rounded-lg flex justify-between items-center gap-4">
                    <p class="text-sm text-rose-400 break-words flex-1">${data.error_message}</p>
                    <button onclick="retryDownload('${data.url}')" class="shrink-0 px-3 py-1.5 bg-rose-500/20 hover:bg-rose-500/40 text-rose-300 text-xs font-bold rounded-md transition-colors border border-rose-500/30 flex items-center gap-1.5">
                        <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path></svg>
                        Retry
                    </button>
                </div>
                ` : ''}
                ${isDone && data.file_path ? `<p class="mt-3 text-xs text-emerald-400 truncate opacity-80 flex items-center gap-1.5"><svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg> Saved to: ${data.file_path.split('\\\\').pop().split('/').pop()}</p>` : ''}
                ${isDone && data.enhanced_file_path ? `
                <div class="mt-3">
                    <button onclick="openComparison('${data.file_path.replace(/\\/g, '\\\\')}', '${data.enhanced_file_path.replace(/\\/g, '\\\\')}')" class="px-4 py-1.5 text-xs font-bold rounded-lg bg-gradient-to-r from-brand-500 to-purple-500 text-white shadow-lg hover:scale-105 transition-transform flex items-center gap-2 w-max">
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"></path></svg>
                        View AI Enhancement
                    </button>
                </div>
                ` : ''}
            </div>
            ${isWorking ? `<div class="font-mono text-xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-brand-400 to-purple-400 drop-shadow-[0_0_10px_rgba(99,102,241,0.5)]">${data.progress_percentage.toFixed(1)}%</div>` : ''}
        </div>
        ${isWorking ? `
        <div class="w-full bg-dark-900/50 rounded-full h-2 mt-2 overflow-hidden border border-white/5">
            <div class="bg-gradient-to-r from-brand-500 to-purple-500 h-2 rounded-full transition-all duration-300 ease-out relative" style="width: ${data.progress_percentage}%">
                <div class="absolute inset-0 bg-white/20 w-full animate-[slideRight_1s_linear_infinite]" style="transform: skewX(-20deg);"></div>
            </div>
        </div>` : ''}
    `;
}

// Toast Notification System
const toastContainer = document.getElementById('toastContainer');

function showToast(message, type = 'info') {
    if (!toastContainer) return;
    
    const toast = document.createElement('div');
    
    let colorClass = 'bg-white/10 text-white border-white/20';
    let icon = '<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>';
    
    if (type === 'error') {
        colorClass = 'bg-rose-500/10 text-rose-400 border-rose-500/30 shadow-[0_0_15px_rgba(244,63,94,0.2)]';
        icon = '<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>';
    } else if (type === 'success') {
        colorClass = 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30 shadow-[0_0_15px_rgba(16,185,129,0.2)]';
        icon = '<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>';
    }
    
    toast.className = `flex items-center gap-3 px-4 py-3 rounded-xl border backdrop-blur-xl animate-slide-in pointer-events-auto transition-all duration-300 ${colorClass}`;
    toast.innerHTML = `${icon} <span class="font-medium text-sm">${message}</span>`;
    
    toastContainer.appendChild(toast);
    
    setTimeout(() => {
        toast.classList.replace('animate-slide-in', 'opacity-0');
        toast.style.transform = 'translateY(100%)';
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

function updateCount() {
    const total = activeDownloads.size;
    const active = Array.from(activeDownloads.values()).filter(d => d.status === 'downloading' || d.status === 'processing').length;
    queueCount.textContent = `${active} active / ${total} total`;
}

// Before/After Slider Logic
const comparisonModal = document.getElementById('comparisonModal');
const closeComparisonBtn = document.getElementById('closeComparisonBtn');
const sliderContainer = document.getElementById('sliderContainer');
const sliderClipper = document.getElementById('sliderClipper');
const sliderHandle = document.getElementById('sliderHandle');
const imgOriginal = document.getElementById('imgOriginal');
const imgEnhanced = document.getElementById('imgEnhanced');

let isDragging = false;

function openComparison(originalPath, enhancedPath) {
    if (!comparisonModal) return;
    
    // Use the API endpoint to serve files natively
    imgOriginal.src = `/api/serve-file?file_path=${encodeURIComponent(originalPath)}`;
    imgEnhanced.src = `/api/serve-file?file_path=${encodeURIComponent(enhancedPath)}`;
    
    // Reset slider to 50%
    sliderClipper.style.width = '50%';
    sliderHandle.style.left = '50%';
    
    // Calculate 200% width for the enhanced image to prevent stretching
    imgEnhanced.style.width = '200%';
    
    comparisonModal.classList.remove('hidden');
    // small delay for transition
    setTimeout(() => {
        comparisonModal.classList.remove('opacity-0');
    }, 10);
}

if (closeComparisonBtn) {
    closeComparisonBtn.addEventListener('click', () => {
        comparisonModal.classList.add('opacity-0');
        setTimeout(() => {
            comparisonModal.classList.add('hidden');
            imgOriginal.src = '';
            imgEnhanced.src = '';
        }, 300);
    });
}

function updateSlider(e) {
    if (!isDragging || !sliderContainer) return;
    
    const rect = sliderContainer.getBoundingClientRect();
    let x = e.clientX || (e.touches && e.touches[0].clientX);
    x = x - rect.left;
    
    // Clamp between 0 and width
    x = Math.max(0, Math.min(x, rect.width));
    
    const percentage = (x / rect.width) * 100;
    
    sliderClipper.style.width = `${percentage}%`;
    sliderHandle.style.left = `${percentage}%`;
    
    // Update the inner image width dynamically to remain aligned
    imgEnhanced.style.width = `${(100 / percentage) * 100}%`;
}

if (sliderContainer) {
    sliderContainer.addEventListener('mousedown', (e) => {
        isDragging = true;
        updateSlider(e);
    });
    
    sliderContainer.addEventListener('touchstart', (e) => {
        isDragging = true;
        updateSlider(e);
    });
    
    window.addEventListener('mouseup', () => { isDragging = false; });
    window.addEventListener('touchend', () => { isDragging = false; });
    
    window.addEventListener('mousemove', updateSlider);
    window.addEventListener('touchmove', updateSlider);
}

// Queue Management
const clearQueueBtn = document.getElementById('clearQueueBtn');

if (clearQueueBtn) {
    clearQueueBtn.addEventListener('click', () => {
        let cleared = 0;
        for (const [id, data] of activeDownloads.entries()) {
            if (data.status === 'completed' || data.status === 'failed') {
                const el = document.getElementById(`item-${id}`);
                if (el) el.remove();
                activeDownloads.delete(id);
                cleared++;
            }
        }
        
        updateCount();
        
        if (cleared > 0) {
            showToast(`Cleared ${cleared} finished items.`, 'success');
        }
        
        if (activeDownloads.size === 0 && emptyState) {
            emptyState.style.display = 'flex';
        }
    });
}

window.retryDownload = async function(url) {
    if (!url) return;
    
    showToast(`Retrying ${url.substring(0, 30)}...`, 'info');
    
    // Create new pending item
    const tempId = String(Math.random());
    updateQueueItem({
        id: tempId,
        url: url,
        status: 'pending',
        progress_percentage: 0,
        tier_used: 1
    });

    try {
        await fetch('/api/download', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                urls: [url],
                enhance_images: enhanceToggle ? enhanceToggle.checked : false,
                color_boost: colorBoostToggle ? colorBoostToggle.checked : false,
                format_type: formatSelect ? formatSelect.value : "video",
                is_playlist: playlistToggle ? playlistToggle.checked : false
            })
        });
    } catch (e) {
        showToast("Failed to retry download.", 'error');
    }
};
