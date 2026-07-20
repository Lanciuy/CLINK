const urlInput = document.getElementById('urlInput');
const downloadBtn = document.getElementById('downloadBtn');
const openFolderBtn = document.getElementById('openFolderBtn');
const queueList = document.getElementById('queueList');
const queueCount = document.getElementById('queueCount');
const emptyState = document.getElementById('emptyState');

// UI State
let activeDownloads = new Map();

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

// Start Download
downloadBtn.addEventListener('click', async () => {
    const text = urlInput.value.trim();
    if (!text) return;

    // Extract valid URLs
    const urls = text.split('\n')
        .map(u => u.trim())
        .filter(u => /^https?:\/\//i.test(u));

    if (urls.length === 0) return;

    urlInput.value = '';
    
    urls.forEach(url => {
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
            body: JSON.stringify({ urls })
        });
    } catch (e) {
        console.error("Failed to start download", e);
        alert("Failed to connect to the server.");
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
                ${isError && data.error_message ? `<p class="mt-3 text-sm text-rose-400 bg-rose-500/10 border border-rose-500/20 p-3 rounded-lg">${data.error_message}</p>` : ''}
                ${isDone && data.file_path ? `<p class="mt-3 text-xs text-emerald-400 truncate opacity-80 flex items-center gap-1.5"><svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg> Saved to: ${data.file_path.split('\\\\').pop().split('/').pop()}</p>` : ''}
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

function updateCount() {
    const total = activeDownloads.size;
    const active = Array.from(activeDownloads.values()).filter(d => d.status === 'downloading' || d.status === 'processing').length;
    queueCount.textContent = `${active} active / ${total} total`;
}
