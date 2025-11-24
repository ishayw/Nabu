const API_URL = ""; // Relative path

let startTime = null;
let currentMeetingFilename = null;
let currentTags = [];
let lastNotificationId = null;

// --- Initialization ---
document.addEventListener('DOMContentLoaded', () => {
    fetchDevices();
    fetchHistory();
    updateStatus();
    setInterval(updateStatus, 1000); // Poll status every 1 second
    setInterval(fetchHistory, 3000); // Poll history every 3 seconds
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

function toggleRecording() {
    const btn = document.getElementById('btn-toggle-record');
    const currentState = btn.dataset.state || "idle";

    if (currentState === "idle") {
        control('start');
    } else {
        control('stop');
    }
}

function updateStatus() {
    fetch('/status')
        .then(response => response.json())
        .then(data => {
            const statusBadge = document.getElementById('status-badge');
            const statusText = document.getElementById('status-text');
            const visualizerRing = document.getElementById('visualizer-ring');
            const visualizerPulse = document.getElementById('visualizer-pulse');
            const btnToggle = document.getElementById('btn-toggle-record');
            const btnText = document.getElementById('btn-text');
            const btnIcon = document.getElementById('btn-icon');
            const timer = document.getElementById('timer');

            if (data.is_recording) {
                // Recording State
                statusBadge.innerHTML = '<span class="w-2 h-2 rounded-full bg-red-500 animate-pulse"></span><span>Recording</span>';
                statusText.textContent = "Recording";
                statusText.className = "text-2xl font-bold tracking-wide text-red-500";

                visualizerRing.className = "absolute inset-0 rounded-full border-4 opacity-50 transition-all duration-300 border-red-500";

                // Update Button to Stop (Red)
                btnToggle.classList.remove('from-primary', 'to-blue-600', 'hover:from-cyan-400', 'hover:to-blue-500', 'shadow-neon', 'hover:shadow-[0_0_20px_rgba(6,182,212,0.6)]');
                btnToggle.classList.add('from-red-600', 'to-red-800', 'hover:from-red-500', 'hover:to-red-700', 'shadow-red', 'hover:shadow-[0_0_20px_rgba(239,68,68,0.6)]');
                btnText.textContent = "Stop";
                btnIcon.className = "w-3 h-3 rounded-sm bg-white shadow-[0_0_10px_white]";

                // Store state for toggle function
                btnToggle.dataset.state = "recording";

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

                // Update Button to Record (Original)
                btnToggle.classList.add('from-primary', 'to-blue-600', 'hover:from-cyan-400', 'hover:to-blue-500', 'shadow-neon', 'hover:shadow-[0_0_20px_rgba(6,182,212,0.6)]');
                btnToggle.classList.remove('from-red-600', 'to-red-800', 'hover:from-red-500', 'hover:to-red-700', 'shadow-red', 'hover:shadow-[0_0_20px_rgba(239,68,68,0.6)]');
                btnText.textContent = "Record";
                btnIcon.className = "w-3 h-3 rounded-full bg-white shadow-[0_0_10px_white] animate-pulse";

                // Store state for toggle function
                btnToggle.dataset.state = "idle";

                timer.classList.add('opacity-0');
                timer.textContent = '00:00';
                startTime = null;
                visualizerPulse.style.opacity = 0;
            }

            // Check for notifications
            if (data.notification && data.notification.id !== lastNotificationId) {
                lastNotificationId = data.notification.id;
                showToast(data.notification.message, data.notification.type);

                // UX Enhancement: Also update status text if it's an error/warning
                if (data.notification.type === 'warning' || data.notification.type === 'error') {
                    const statusText = document.getElementById('status-text');
                    // Only update if we are not currently recording (to avoid confusion)
                    if (!data.is_recording) {
                        statusText.textContent = data.notification.message;
                        statusText.className = "text-lg font-bold tracking-wide text-yellow-500";

                        // Revert after 3s
                        setTimeout(() => {
                            // Check again if we are still idle before resetting
                            if (statusText.textContent === data.notification.message) {
                                statusText.textContent = "Ready";
                                statusText.className = "text-2xl font-bold tracking-wide text-white";
                            }
                        }, 3000);
                    }
                }
            }
        })
        .catch(error => console.error('Error:', error));
}

function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    if (!container) {
        const c = document.createElement('div');
        c.id = 'toast-container';
        c.className = 'fixed bottom-5 right-5 z-50 flex flex-col gap-2';
        document.body.appendChild(c);
    }

    const toast = document.createElement('div');
    const bgClass = type === 'warning' ? 'bg-yellow-600' : (type === 'error' ? 'bg-red-600' : 'bg-blue-600');
    toast.className = `${bgClass} text-white px-4 py-2 rounded shadow-lg transition-opacity duration-500 opacity-0 transform translate-y-2`;
    toast.textContent = message;

    document.getElementById('toast-container').appendChild(toast);

    // Animate in
    requestAnimationFrame(() => {
        toast.classList.remove('opacity-0', 'translate-y-2');
    });

    // Remove after 3s
    setTimeout(() => {
        toast.classList.add('opacity-0', 'translate-y-2');
        setTimeout(() => toast.remove(), 500);
    }, 3000);
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
        item.className = "p-3 rounded-lg bg-gray-800 hover:bg-gray-700 cursor-pointer border border-gray-700 transition-colors group mb-2 relative";
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

        const isProcessed = rec.summary_text &&
            rec.summary_text.length > 0 &&
            rec.summary_text !== "Processing..." &&
            !rec.summary_text.startsWith("{");
        let statusHtml = '';

        if (rec.title === "Short Recording" || rec.summary_text === "Recording too short to summarize.") {
            statusHtml = '<span class="text-gray-500 text-xs border border-gray-600 px-1 rounded">Too Short</span>';
        } else if (isProcessed) {
            statusHtml = '<span class="text-green-400 text-xs">Processed</span>';
        } else {
            statusHtml = '<span class="text-yellow-500 text-xs animate-pulse">Processing...</span>';
        }

        item.innerHTML = `
            <div class="flex justify-between items-start mb-1">
                <span class="font-medium text-gray-300 text-sm truncate w-full pr-6" title="${rec.title || rec.filename}">${rec.title || rec.filename}</span>
                <button onclick="deleteMeeting('${rec.filename}', event)" class="text-gray-500 hover:text-red-500 p-1 absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity" title="Delete">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                </button>
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

async function deleteMeeting(filename, event) {
    if (event) event.stopPropagation();
    if (!confirm("Delete this recording?")) return;

    try {
        const response = await fetch(`${API_URL}/history/${filename}`, { method: "DELETE" });
        if (response.ok) {
            fetchHistory();
            // If currently open, close it
            if (currentMeetingFilename === filename) {
                closeMeeting();
            }
        } else {
            alert("Failed to delete");
        }
    } catch (error) {
        console.error("Error deleting:", error);
    }
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
        let summaryText = data.summary_text || "No summary available.";

        // Fallback: If summary text looks like JSON (backend parsing failed), try to parse it here
        if (summaryText.trim().startsWith("{")) {
            try {
                const parsed = JSON.parse(summaryText);
                if (parsed.summary) {
                    summaryText = parsed.summary;
                    // Also update tags if we found them and they weren't set
                    if ((!data.tags || data.tags.length === 0) && parsed.tags) {
                        renderTags(parsed.tags);
                    }
                    if (parsed.title) {
                        document.getElementById("meeting-title").innerText = parsed.title;
                    }
                }
            } catch (e) {
                console.warn("Failed to parse raw JSON summary in frontend:", e);
            }
        }

        document.getElementById("meeting-title").innerText = data.title || "Meeting Summary";
        document.getElementById("meeting-content").innerHTML = marked.parse(summaryText);

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

// --- Settings Management ---
async function openSettings() {
    try {
        // Load current settings
        const response = await fetch(`${API_URL}/settings`);
        const data = await response.json();
        const settings = data.settings;

        // Populate form
        document.getElementById('min_recording_duration').value = settings.min_recording_duration || 3;
        document.getElementById('delete_short_recordings').checked = settings.delete_short_recordings === 'true';
        document.getElementById('compress_recordings').checked = settings.compress_recordings === 'true';
        document.getElementById('auto_detection').checked = settings.auto_detection === 'true';
        document.getElementById('vad_threshold').value = settings.vad_threshold || 0.03;
        document.getElementById('silence_duration').value = settings.silence_duration || 10;

        // Show modal
        document.getElementById('settings-modal').classList.remove('hidden');
    } catch (error) {
        console.error('Error loading settings:', error);
        alert('Failed to load settings');
    }
}

function closeSettings() {
    document.getElementById('settings-modal').classList.add('hidden');
}

async function saveSettings() {
    try {
        const settings = {
            min_recording_duration: document.getElementById('min_recording_duration').value,
            delete_short_recordings: document.getElementById('delete_short_recordings').checked.toString(),
            compress_recordings: document.getElementById('compress_recordings').checked.toString(),
            auto_detection: document.getElementById('auto_detection').checked.toString(),
            vad_threshold: document.getElementById('vad_threshold').value,
            silence_duration: document.getElementById('silence_duration').value,
        };

        const response = await fetch(`${API_URL}/settings`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(settings)
        });

        if (response.ok) {
            closeSettings();
            showToast('Settings saved successfully', 'info');
        } else {
            alert('Failed to save settings');
        }
    } catch (error) {
        console.error('Error saving settings:', error);
        alert('Failed to save settings');
    }
}

// --- Speakers Editing ---
function parseSpeakers(summary) {
    // Extract speakers section from markdown
    const speakersMatch = summary.match(/## Speakers\n([\s\S]*?)(?=\n## |$)/);
    if (!speakersMatch) return [];

    const speakersText = speakersMatch[1];
    const lines = speakersText.split('\n').filter(line => line.trim().startsWith('*'));

    return lines.map(line => {
        // Parse "*   Name: Description"
        const match = line.match(/\*\s+(.+?):\s*(.+)/);
        if (match) {
            return {
                name: match[1].trim(),
                description: match[2].trim()
            };
        }
        return null;
    }).filter(Boolean);
}

async function saveSpeakers(filename, speakers) {
    try {
        const response = await fetch(`${API_URL}/meeting/${filename}/speakers`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ speakers })
        });

        if (response.ok) {
            showToast('Speakers updated', 'info');
            // Reload the meeting to show changes
            loadMeeting(filename);
        } else {
            alert('Failed to update speakers');
        }
    } catch (error) {
        console.error('Error updating speakers:', error);
        alert('Failed to update speakers');
    }
}

 
 / /   - - -   S p e a k e r s   E d i t i n g   - - -  
 f u n c t i o n   p a r s e S p e a k e r s ( s u m m a r y )   {  
         c o n s t   s p e a k e r s M a t c h   =   s u m m a r y . m a t c h ( / # #   S p e a k e r s \ n ( [ \ s \ S ] * ? ) ( ? = \ n # #   | $ ) / ) ;  
         i f   ( ! s p e a k e r s M a t c h )   r e t u r n   [ ] ;  
         c o n s t   s p e a k e r s T e x t   =   s p e a k e r s M a t c h [ 1 ] ;  
         c o n s t   l i n e s   =   s p e a k e r s T e x t . s p l i t ( ' \ n ' ) . f i l t e r ( l i n e   = >   l i n e . t r i m ( ) . s t a r t s W i t h ( ' * ' ) ) ;  
         r e t u r n   l i n e s . m a p ( l i n e   = >   {  
                 c o n s t   m a t c h   =   l i n e . m a t c h ( / \ * \ s + ( . + ? ) : \ s * ( . + ) / ) ;  
                 i f   ( m a t c h )   {  
                         r e t u r n   {   n a m e :   m a t c h [ 1 ] . t r i m ( ) ,   d e s c r i p t i o n :   m a t c h [ 2 ] . t r i m ( )   } ;  
                 }  
                 r e t u r n   n u l l ;  
         } ) . f i l t e r ( B o o l e a n ) ;  
 }  
  
 f u n c t i o n   o p e n S p e a k e r s E d i t o r ( )   {  
         i f   ( ! c u r r e n t M e e t i n g F i l e n a m e )   r e t u r n ;  
         f e t c h ( ` $ { A P I _ U R L } / m e e t i n g / $ { c u r r e n t M e e t i n g F i l e n a m e } ` )  
                 . t h e n ( r e s p o n s e   = >   r e s p o n s e . j s o n ( ) )  
                 . t h e n ( d a t a   = >   {  
                         c o n s t   s p e a k e r s   =   p a r s e S p e a k e r s ( d a t a . s u m m a r y _ t e x t   | |   " " ) ;  
                         c o n s t   s p e a k e r s L i s t   =   d o c u m e n t . g e t E l e m e n t B y I d ( ' s p e a k e r s - l i s t ' ) ;  
                         s p e a k e r s L i s t . i n n e r H T M L   =   ' ' ;  
                         i f   ( s p e a k e r s . l e n g t h   = = =   0 )   {  
                                 a d d S p e a k e r I n p u t ( ) ;  
                         }   e l s e   {  
                                 s p e a k e r s . f o r E a c h ( s p e a k e r   = >   a d d S p e a k e r I n p u t ( s p e a k e r . n a m e ,   s p e a k e r . d e s c r i p t i o n ) ) ;  
                         }  
                         d o c u m e n t . g e t E l e m e n t B y I d ( ' s p e a k e r s - m o d a l ' ) . c l a s s L i s t . r e m o v e ( ' h i d d e n ' ) ;  
                 } )  
                 . c a t c h ( e r r o r   = >   {  
                         c o n s o l e . e r r o r ( ' E r r o r   l o a d i n g   s p e a k e r s : ' ,   e r r o r ) ;  
                         a l e r t ( ' F a i l e d   t o   l o a d   s p e a k e r s ' ) ;  
                 } ) ;  
 }  
  
 f u n c t i o n   c l o s e S p e a k e r s E d i t o r ( )   {  
         d o c u m e n t . g e t E l e m e n t B y I d ( ' s p e a k e r s - m o d a l ' ) . c l a s s L i s t . a d d ( ' h i d d e n ' ) ;  
 }  
  
 f u n c t i o n   a d d S p e a k e r I n p u t ( n a m e   =   ' ' ,   d e s c r i p t i o n   =   ' ' )   {  
         c o n s t   s p e a k e r s L i s t   =   d o c u m e n t . g e t E l e m e n t B y I d ( ' s p e a k e r s - l i s t ' ) ;  
         c o n s t   i n d e x   =   s p e a k e r s L i s t . c h i l d r e n . l e n g t h ;  
         c o n s t   s p e a k e r D i v   =   d o c u m e n t . c r e a t e E l e m e n t ( ' d i v ' ) ;  
         s p e a k e r D i v . c l a s s N a m e   =   ' b g - s u r f a c e / 3 0   b o r d e r   b o r d e r - g r a y - 8 0 0   r o u n d e d - l g   p - 4   s p a c e - y - 3 ' ;  
         s p e a k e r D i v . i n n e r H T M L   =   `  
                 < d i v   c l a s s = " f l e x   j u s t i f y - b e t w e e n   i t e m s - c e n t e r " >  
                         < h 4   c l a s s = " t e x t - s m   f o n t - m e d i u m   t e x t - g r a y - 3 0 0 " > S p e a k e r   $ { i n d e x   +   1 } < / h 4 >  
                         < b u t t o n   o n c l i c k = " t h i s . c l o s e s t ( ' d i v ' ) . p a r e n t E l e m e n t . r e m o v e ( ) "   c l a s s = " t e x t - g r a y - 5 0 0   h o v e r : t e x t - r e d - 4 0 0   t r a n s i t i o n - c o l o r s " >  
                                 < s v g   x m l n s = " h t t p : / / w w w . w 3 . o r g / 2 0 0 0 / s v g "   c l a s s = " h - 5   w - 5 "   f i l l = " n o n e "   v i e w B o x = " 0   0   2 4   2 4 "   s t r o k e = " c u r r e n t C o l o r " >  
                                         < p a t h   s t r o k e - l i n e c a p = " r o u n d "   s t r o k e - l i n e j o i n = " r o u n d "   s t r o k e - w i d t h = " 2 "   d = " M 6   1 8 L 1 8   6 M 6   6 l 1 2   1 2 "   / >  
                                 < / s v g >  
                         < / b u t t o n >  
                 < / d i v >  
                 < i n p u t   t y p e = " t e x t "   p l a c e h o l d e r = " N a m e "   v a l u e = " $ { n a m e } "    
                         c l a s s = " s p e a k e r - n a m e   w - f u l l   b g - d a r k   b o r d e r   b o r d e r - g r a y - 7 0 0   r o u n d e d - l g   p x - 4   p y - 2   t e x t - g r a y - 2 0 0   f o c u s : o u t l i n e - n o n e   f o c u s : b o r d e r - a c c e n t " >  
                 < t e x t a r e a   p l a c e h o l d e r = " D e s c r i p t i o n "   r o w s = " 2 "    
                         c l a s s = " s p e a k e r - d e s c   w - f u l l   b g - d a r k   b o r d e r   b o r d e r - g r a y - 7 0 0   r o u n d e d - l g   p x - 4   p y - 2   t e x t - g r a y - 2 0 0   f o c u s : o u t l i n e - n o n e   f o c u s : b o r d e r - a c c e n t   r e s i z e - n o n e " > $ { d e s c r i p t i o n } < / t e x t a r e a >  
         ` ;  
         s p e a k e r s L i s t . a p p e n d C h i l d ( s p e a k e r D i v ) ;  
 }  
  
 f u n c t i o n   s a v e S p e a k e r s C h a n g e s ( )   {  
         i f   ( ! c u r r e n t M e e t i n g F i l e n a m e )   r e t u r n ;  
         c o n s t   s p e a k e r D i v s   =   d o c u m e n t . q u e r y S e l e c t o r A l l ( ' # s p e a k e r s - l i s t   >   d i v ' ) ;  
         c o n s t   s p e a k e r s   =   [ ] ;  
         s p e a k e r D i v s . f o r E a c h ( d i v   = >   {  
                 c o n s t   n a m e   =   d i v . q u e r y S e l e c t o r ( ' . s p e a k e r - n a m e ' ) . v a l u e . t r i m ( ) ;  
                 c o n s t   d e s c r i p t i o n   =   d i v . q u e r y S e l e c t o r ( ' . s p e a k e r - d e s c ' ) . v a l u e . t r i m ( ) ;  
                 i f   ( n a m e )   {  
                         s p e a k e r s . p u s h ( {   n a m e ,   d e s c r i p t i o n   } ) ;  
                 }  
         } ) ;  
         s a v e S p e a k e r s ( c u r r e n t M e e t i n g F i l e n a m e ,   s p e a k e r s ) ;  
         c l o s e S p e a k e r s E d i t o r ( ) ;  
 }  
  
 a s y n c   f u n c t i o n   s a v e S p e a k e r s ( f i l e n a m e ,   s p e a k e r s )   {  
         t r y   {  
                 c o n s t   r e s p o n s e   =   a w a i t   f e t c h ( ` $ { A P I _ U R L } / m e e t i n g / $ { f i l e n a m e } / s p e a k e r s ` ,   {  
                         m e t h o d :   ' P O S T ' ,  
                         h e a d e r s :   {   ' C o n t e n t - T y p e ' :   ' a p p l i c a t i o n / j s o n '   } ,  
                         b o d y :   J S O N . s t r i n g i f y ( {   s p e a k e r s   } )  
                 } ) ;  
                 i f   ( r e s p o n s e . o k )   {  
                         s h o w T o a s t ( ' S p e a k e r s   u p d a t e d ' ,   ' i n f o ' ) ;  
                         l o a d M e e t i n g ( f i l e n a m e ) ;  
                 }   e l s e   {  
                         a l e r t ( ' F a i l e d   t o   u p d a t e   s p e a k e r s ' ) ;  
                 }  
         }   c a t c h   ( e r r o r )   {  
                 c o n s o l e . e r r o r ( ' E r r o r   u p d a t i n g   s p e a k e r s : ' ,   e r r o r ) ;  
                 a l e r t ( ' F a i l e d   t o   u p d a t e   s p e a k e r s ' ) ;  
         }  
 }  
 