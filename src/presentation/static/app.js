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
        case 'pending': return 'bg-yellow-500/20 text-yellow-500';
        case 'downloading': return 'bg-brand-500/20 text-brand-400';
        case 'processing': return 'bg-purple-500/20 text-purple-400';
        case 'completed': return 'bg-green-500/20 text-green-400';
        case 'failed': return 'bg-red-500/20 text-red-400';
        default: return 'bg-white/10 text-white';
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
            el.className = `glass-item rounded-xl p-4 border border-white/5 animate-slide-in flex flex-col gap-3 ${data.status === 'pending' ? 'queue-item-pending' : ''}`;
            queueList.insertBefore(el, queueList.firstChild);
        }
    }

    activeDownloads.set(data.id, data);
    updateCount();

    const shortUrl = data.url.length > 50 ? data.url.substring(0, 50) + '...' : data.url;
    const isError = data.status === 'failed';
    const isDone = data.status === 'completed';
    const isWorking = data.status === 'downloading' || data.status === 'processing';

    el.innerHTML = `
        <div class="flex justify-between items-start gap-4">
            <div class="flex-1 min-w-0">
                <p class="text-sm font-medium text-white/90 truncate" title="${data.url}">${shortUrl}</p>
                <div class="flex items-center gap-3 mt-1 text-xs text-white/50">
                    <span class="flex items-center gap-1 ${getStatusColor(data.status)} px-2 py-0.5 rounded-full capitalize">
                        ${isWorking ? '<svg class="animate-spin w-3 h-3" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>' : ''}
                        ${data.status}
                    </span>
                    ${data.speed_mbps ? `<span>${data.speed_mbps.toFixed(2)} MB/s</span>` : ''}
                    ${data.eta_seconds ? `<span>ETA: ${data.eta_seconds}s</span>` : ''}
                    <span title="Extraction Tier">T${data.tier_used || 1}</span>
                </div>
                ${isError && data.error_message ? `<p class="mt-2 text-xs text-red-400 bg-red-400/10 p-2 rounded-md">${data.error_message}</p>` : ''}
                ${isDone && data.file_path ? `<p class="mt-2 text-xs text-green-400 truncate opacity-70">Saved to: ${data.file_path.split('\\\\').pop().split('/').pop()}</p>` : ''}
            </div>
            ${isWorking ? `<div class="font-mono text-sm font-bold text-brand-400">${data.progress_percentage.toFixed(1)}%</div>` : ''}
        </div>
        ${isWorking ? `
        <div class="w-full bg-dark-900 rounded-full h-1.5 overflow-hidden">
            <div class="bg-brand-500 h-1.5 rounded-full transition-all duration-300 ease-out" style="width: ${data.progress_percentage}%"></div>
        </div>` : ''}
    `;
}

function updateCount() {
    const total = activeDownloads.size;
    const active = Array.from(activeDownloads.values()).filter(d => d.status === 'downloading' || d.status === 'processing').length;
    queueCount.textContent = `${active} active / ${total} total`;
}
