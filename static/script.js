const API_URL = ""; // Relative path

let startTime = null;
let currentMeetingFilename = null;
let currentTags = [];

// --- Initialization ---
document.addEventListener('DOMContentLoaded', () => {
    fetchDevices();
    fetchHistory();
    updateStatus();
    setInterval(updateStatus, 1000); // Poll status every second
    setInterval(fetchHistory, 5000); // Poll history every 5 seconds
});

// --- Device Management ---
async function fetchDevices() {
    try {
        const response = await fetch('/devices');
        const data = await response.json();
        const select = document.getElementById('micSelect');

        select.innerHTML = '';
        if (data.devices.length === 0) {
            const option = document.createElement('option');
            option.text = "No devices found";
            select.appendChild(option);
            return;
        }

        data.devices.forEach((device, idx) => {
            const option = document.createElement('option');
            option.value = device.index;
            option.text = device.name;
            if (idx === 0) option.selected = true;
            select.appendChild(option);
        });

        // Set initial device if available
        if (data.devices.length > 0) {
            changeDevice();
        }
    } catch (error) {
        console.error('Error fetching devices:', error);
        document.getElementById('micSelect').innerHTML = '<option>Error loading devices</option>';
    }
}

async function changeDevice() {
    const select = document.getElementById('micSelect');
    if (!select.value) return;

    const deviceIndex = parseInt(select.value);

    try {
        await fetch('/config/device', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ device_index: deviceIndex }),
        });
        console.log(`Device changed to index ${deviceIndex}`);
    } catch (error) {
        console.error('Error changing device:', error);
    }
}

// --- Control & Status ---
function control(action) {
    fetch(`/control/${action}`, { method: 'POST' })
        .then(response => response.json())
        .then(data => {
            console.log(data.status);
            updateStatus();
        })
        .catch(error => console.error('Error:', error));
}

function updateStatus() {
    fetch('/status')
        .then(response => response.json())
        .then(data => {
            const statusBadge = document.getElementById('status-badge');
            const statusText = document.getElementById('status-text');
            const visualizerRing = document.getElementById('visualizer-ring');
            const visualizerPulse = document.getElementById('visualizer-pulse');
            const btnStart = document.getElementById('btn-start');
            const btnStop = document.getElementById('btn-stop');
            const timer = document.getElementById('timer');

            if (data.is_recording) {
                // Recording State
                statusBadge.innerHTML = '<span class="w-2 h-2 rounded-full bg-red-500 animate-pulse"></span><span>Recording</span>';
                statusText.textContent = "Recording";
                statusText.className = "text-2xl font-bold tracking-wide text-red-500";

                visualizerRing.className = "absolute inset-0 rounded-full border-4 opacity-50 transition-all duration-300 border-red-500";

                btnStart.disabled = true;
                btnStart.classList.add('opacity-50', 'cursor-not-allowed');
                btnStop.disabled = false;
                btnStop.classList.remove('opacity-50', 'cursor-not-allowed');

                timer.classList.remove('opacity-0');

                // Update timer
                if (!startTime) startTime = Date.now();
                const elapsed = Math.floor((Date.now() - startTime) / 1000);
                const minutes = Math.floor(elapsed / 60);
                const seconds = elapsed % 60;
                timer.textContent = `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;

                // Visualizer Animation
                const scale = 1 + Math.min(data.rms * 5, 1.5);
                visualizerPulse.style.transform = `scale(${scale})`;
                visualizerPulse.style.opacity = Math.min(data.rms * 2, 0.8);

            } else {
                // Idle State
                statusBadge.innerHTML = '<span class="w-2 h-2 rounded-full bg-gray-400"></span><span>Idle</span>';
                statusText.textContent = "Ready";
                statusText.className = "text-2xl font-bold tracking-wide text-white";

                visualizerRing.className = "absolute inset-0 rounded-full border-4 opacity-50 transition-all duration-300 border-gray-700";

                btnStart.disabled = false;
                btnStart.classList.remove('opacity-50', 'cursor-not-allowed');
                btnStop.disabled = true;
                btnStop.classList.add('opacity-50', 'cursor-not-allowed');

                timer.classList.add('opacity-0');
                timer.textContent = '00:00';
                startTime = null;
                visualizerPulse.style.transform = 'scale(1)';
                visualizerPulse.style.opacity = 0;
            }
        })
        .catch(error => console.error('Error:', error));
}

// --- History & Search ---
async function fetchHistory() {
    // Only fetch if not searching (simple check: search input empty)
    const searchInput = document.getElementById('search-input');
    if (searchInput && searchInput.value.trim() !== "") return;

    try {
        const response = await fetch(`${API_URL}/history`);
        const data = await response.json();
        renderHistory(data.recordings);
    } catch (error) {
        console.error("Error fetching history:", error);
    }
}

let searchTimeout;
async function searchHistory(query) {
    clearTimeout(searchTimeout);

    if (!query) {
        fetchHistory();
        return;
    }

    searchTimeout = setTimeout(async () => {
        try {
            const response = await fetch(`${API_URL}/search?q=${encodeURIComponent(query)}`);
            const data = await response.json();
            renderHistory(data.results);
        } catch (error) {
            console.error("Search error:", error);
        }
    }, 300); // Debounce
}

function renderHistory(recordings) {
    const list = document.getElementById("history-list");
    list.innerHTML = "";

    if (!recordings || recordings.length === 0) {
        list.innerHTML = '<div class="text-center text-gray-500 mt-10 text-sm">No recordings found</div>';
        return;
    }

    recordings.forEach(rec => {
        const item = document.createElement("div");
        item.className = "p-3 rounded-lg bg-gray-800 hover:bg-gray-700 cursor-pointer border border-gray-700 transition-colors group mb-2";
        item.onclick = () => loadMeeting(rec.filename);

        // Format date
        let dateStr = rec.created_at;
        try {
            if (dateStr && (dateStr.includes("T") || dateStr.includes(" "))) {
                // Simple parse attempt
                dateStr = dateStr.split('.')[0]; // Remove microseconds if present
            }
        } catch (e) { }

        // Tags HTML
        let tagsHtml = "";
        if (rec.tags && rec.tags.length > 0) {
            tagsHtml = `<div class="flex flex-wrap gap-1 mt-2">
                ${rec.tags.map(t => `<span class="px-1.5 py-0.5 rounded text-[10px] bg-gray-600 text-gray-300 border border-gray-500">${t}</span>`).join('')}
            </div>`;
        }

        const isProcessed = rec.summary_text && rec.summary_text.length > 0;
        const statusHtml = isProcessed
            ? '<span class="text-green-400 text-xs">Processed</span>'
            : '<span class="text-yellow-500 text-xs animate-pulse">Processing...</span>';

        item.innerHTML = `
            <div class="flex justify-between items-start mb-1">
                <span class="font-medium text-gray-300 text-sm truncate w-full" title="${rec.title || rec.filename}">${rec.title || rec.filename}</span>
            </div>
            <div class="flex justify-between items-center text-xs text-gray-500">
                <span>${dateStr}</span>
                ${statusHtml}
            </div>
            ${tagsHtml}
        `;
        list.appendChild(item);
    });
}

async function clearHistory() {
    if (!confirm("Are you sure you want to delete all recordings?")) return;

    try {
        await fetch(`${API_URL}/history`, { method: "DELETE" });
        fetchHistory();
        closeMeeting();
    } catch (error) {
        console.error("Error clearing history:", error);
    }
}

// --- Upload ---
async function uploadFile(input) {
    const file = input.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append("file", file);

    // Show uploading state
    const historyList = document.getElementById("history-list");
    const tempId = "uploading-" + Date.now();
    const tempItem = document.createElement("div");
    tempItem.id = tempId;
    tempItem.className = "p-3 rounded-lg bg-gray-800 border border-gray-700 animate-pulse mb-2";
    tempItem.innerHTML = `
        <div class="flex justify-between items-start mb-1">
            <span class="font-medium text-gray-300 text-sm truncate">${file.name}</span>
            <span class="text-xs text-primary">Uploading...</span>
        </div>
    `;
    historyList.prepend(tempItem);

    try {
        const response = await fetch(`${API_URL}/upload`, {
            method: "POST",
            body: formData
        });

        if (response.ok) {
            // Give it a moment to register in DB then fetch
            setTimeout(fetchHistory, 1000);
        } else {
            alert("Upload failed");
            tempItem.remove();
        }
    } catch (error) {
        console.error("Error uploading:", error);
        alert("Upload error");
        tempItem.remove();
    }

    // Reset input
    input.value = "";
}

// --- Meeting View ---
async function loadMeeting(filename) {
    try {
        // Show loading state
        document.getElementById("meeting-view").classList.remove("hidden");
        document.getElementById("empty-state").classList.add("hidden");
        document.getElementById("meeting-content").innerHTML = '<p class="text-gray-500 animate-pulse">Loading...</p>';

        const response = await fetch(`${API_URL}/meeting/${filename}`);
        if (!response.ok) throw new Error("Failed to load meeting");

        const data = await response.json();

        document.getElementById("meeting-title").innerText = data.title || "Meeting Summary";
        document.getElementById("meeting-content").innerHTML = marked.parse(data.summary_text || "No summary available.");

        // Setup audio
        const audio = document.getElementById("audio-player");
        audio.src = `${API_URL}/audio/${filename}`;

        // Setup tags
        currentMeetingFilename = filename;
        renderTags(data.tags || []);

    } catch (error) {
        console.error("Error loading meeting:", error);
        document.getElementById("meeting-content").innerHTML = '<p class="text-red-500">Error loading meeting details.</p>';
    }
}

function closeMeeting() {
    document.getElementById("meeting-view").classList.add("hidden");
    document.getElementById("empty-state").classList.remove("hidden");
    // Stop audio
    const audio = document.getElementById("audio-player");
    audio.pause();
    audio.currentTime = 0;
}

// --- Tagging ---
function renderTags(tags) {
    const tagsDisplay = document.getElementById('tags-display');
    tagsDisplay.innerHTML = '';
    currentTags = tags;

    currentTags.forEach(tag => {
        const tagEl = document.createElement('span');
        tagEl.className = 'px-3 py-1 bg-primary/20 text-primary rounded-full text-sm flex items-center space-x-2 border border-primary/30';
        tagEl.innerHTML = `
            <span>${tag}</span>
            <button onclick="removeTag('${tag}')" class="hover:text-red-400 transition-colors ml-1 font-bold">×</button>
        `;
        tagsDisplay.appendChild(tagEl);
    });
}

async function addTag() {
    const input = document.getElementById('tag-input');
    const tag = input.value.trim();

    if (!tag || !currentMeetingFilename) return;

    // Optimistic update
    if (!currentTags.includes(tag)) {
        currentTags.push(tag);
        renderTags(currentTags);

        try {
            const response = await fetch(`${API_URL}/tags/${currentMeetingFilename}`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ tag: tag })
            });

            if (!response.ok) {
                // Revert if failed
                currentTags = currentTags.filter(t => t !== tag);
                renderTags(currentTags);
                alert("Failed to add tag");
            } else {
                input.value = "";
                // Refresh history to show new tag in sidebar
                fetchHistory();
            }
        } catch (error) {
            console.error("Error adding tag:", error);
            currentTags = currentTags.filter(t => t !== tag);
            renderTags(currentTags);
        }
    } else {
        input.value = "";
    }
}

async function removeTag(tag) {
    // Note: We don't have a remove tag endpoint yet in the backend!
    // For now, we can't really remove tags easily without updating the whole list or adding a DELETE endpoint.
    // The user asked to "add tags", not explicitly remove, but the UI implies it.
    // Let's just alert for now or implement it if we have time.
    alert("Tag removal not yet supported by backend.");
}

// --- Copy Summary to Clipboard ---
async function copySummaryToClipboard() {
    const meetingContent = document.getElementById('meeting-content');
    const copyBtn = document.getElementById('copy-btn-text');
    const originalText = copyBtn.textContent;

    if (!meetingContent) {
        alert('No summary to copy.');
        return;
    }

    // Get the text content from the rendered markdown
    const textContent = meetingContent.innerText;

    try {
        await navigator.clipboard.writeText(textContent);

        // Visual feedback
        copyBtn.textContent = 'Copied!';
        copyBtn.parentElement.classList.add('bg-green-600', 'border-green-500');
        copyBtn.parentElement.classList.remove('bg-gray-800', 'border-gray-600');

        // Reset after 2 seconds
        setTimeout(() => {
            copyBtn.textContent = originalText;
            copyBtn.parentElement.classList.remove('bg-green-600', 'border-green-500');
            copyBtn.parentElement.classList.add('bg-gray-800', 'border-gray-600');
        }, 2000);
    } catch (error) {
        console.error('Failed to copy:', error);
        alert('Failed to copy to clipboard. Please try again.');
    }
}
