const ENABLED_KEY = 'extension_enabled';
const STATS_KEY = 'extension_stats';

document.addEventListener('DOMContentLoaded', () => {
    const toggle = document.getElementById('extensionToggle');
    const statusMessage = document.getElementById('statusMessage');

    chrome.storage.sync.get([ENABLED_KEY, STATS_KEY], (result) => {
        const isEnabled = result[ENABLED_KEY] !== false;
        toggle.checked = isEnabled;
        updateStatus(isEnabled);

        const stats = result[STATS_KEY] || {};
        document.getElementById('emailsProcessed').textContent = stats.emails_processed || 0;
        document.getElementById('spamBlocked').textContent = stats.spam_blocked || 0;
        document.getElementById('responsesGenerated').textContent = stats.responses_generated || 0;
    });

    toggle.addEventListener('change', (e) => {
        const isEnabled = e.target.checked;

        chrome.storage.sync.set({ [ENABLED_KEY]: isEnabled }, () => {
            updateStatus(isEnabled);
        });
    });

    function updateStatus(isEnabled) {
        if (isEnabled) {
            statusMessage.textContent = 'Extension is active';
            statusMessage.className = 'status active';
        } else {
            statusMessage.textContent = 'Extension is paused';
            statusMessage.className = 'status inactive';
        }
    }
});
