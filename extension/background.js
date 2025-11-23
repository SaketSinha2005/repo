chrome.runtime.onInstalled.addListener(() => {
    console.log('Gmail Customer Service Assistant installed');

    chrome.storage.sync.set({ extension_enabled: true });

    chrome.storage.sync.set({
        extension_stats: {
            emails_processed: 0,
            spam_blocked: 0,
            responses_generated: 0
        }
    });
});

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === 'updateStats') {
        chrome.storage.sync.get(['extension_stats'], (result) => {
            const stats = result.extension_stats || {};

            if (request.type === 'email_processed') {
                stats.emails_processed = (stats.emails_processed || 0) + 1;
            } else if (request.type === 'spam_blocked') {
                stats.spam_blocked = (stats.spam_blocked || 0) + 1;
            } else if (request.type === 'response_generated') {
                stats.responses_generated = (stats.responses_generated || 0) + 1;
            }

            chrome.storage.sync.set({ extension_stats: stats });
            sendResponse({ success: true });
        });

        return true; 
    }
});
