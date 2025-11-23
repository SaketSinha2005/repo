const CONFIG = {
    API_URL: 'http://localhost:5000',
    ENABLED_KEY: 'extension_enabled'
};

let isEnabled = true;

chrome.storage.sync.get([CONFIG.ENABLED_KEY], (result) => {
    isEnabled = result[CONFIG.ENABLED_KEY] !== false;
    if (isEnabled) {
        console.log('Gmail Customer Service Assistant: Active');
        initializeExtension();
    }
});

function initializeExtension() {
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', observeGmail);
    } else {
        observeGmail();
    }
}

function observeGmail() {
    const observer = new MutationObserver((mutations) => {
        const emailContainer = document.querySelector('[role="main"]');
        if (emailContainer && !emailContainer.dataset.assistantInjected) {
            detectNewEmail(emailContainer);
        }
    });

    observer.observe(document.body, {
        childList: true,
        subtree: true
    });
}

async function detectNewEmail(container) {
    container.dataset.assistantInjected = 'true';

    const emailContent = extractEmailContent();

    if (!emailContent) {
        return;
    }

    console.log('Processing email...', emailContent.substring(0, 100));

    showProcessingIndicator();

    try {
        const response = await fetch(`${CONFIG.API_URL}/generate-response`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ email: emailContent })
        });

        const data = await response.json();

        removeProcessingIndicator();

        if (data.is_spam) {
            showSpamNotification(data.spam_confidence);
        } else if (!data.success) {
            console.error('Response generation failed:', data.error);
            showErrorNotification(`Error: ${data.error || 'Failed to generate response'}`);
        } else if (data.response) {
            showResponseSuggestion(data.response, data.classification);
        } else {
            console.error('No response generated:', data);
            showErrorNotification('No response was generated. Please check the server logs.');
        }
    } catch (error) {
        console.error('Error calling API:', error);
        removeProcessingIndicator();
        showErrorNotification();
    }
}

function extractEmailContent() {
    const selectors = [
        '.a3s.aiL',  
        '[data-message-id] .a3s',
        '.ii.gt' 
    ];

    for (const selector of selectors) {
        const element = document.querySelector(selector);
        if (element) {
            return element.innerText || element.textContent;
        }
    }

    return null;
}

function showProcessingIndicator() {
    const indicator = document.createElement('div');
    indicator.id = 'cs-assistant-processing';
    indicator.innerHTML = `
        <div style="background: #4285f4; color: white; padding: 12px; border-radius: 8px; 
                    position: fixed; top: 20px; right: 20px; z-index: 10000; box-shadow: 0 2px 10px rgba(0,0,0,0.2);">
            <div style="display: flex; align-items: center; gap: 10px;">
                <div class="spinner"></div>
                <span>Processing email...</span>
            </div>
        </div>
    `;
    document.body.appendChild(indicator);
}

function removeProcessingIndicator() {
    const indicator = document.getElementById('cs-assistant-processing');
    if (indicator) {
        indicator.remove();
    }
}

function showSpamNotification(confidence) {
    const notification = createNotification(
        'Spam Detected',
        `This email was classified as spam (${(confidence * 100).toFixed(0)}% confidence). No response generated.`,
        '#ea4335'
    );
    document.body.appendChild(notification);

    setTimeout(() => notification.remove(), 5000);
}

function showResponseSuggestion(response, classification) {
    // Find reply box area
    const replyArea = document.querySelector('[role="main"]');

    if (!replyArea) {
        console.error('Could not find reply area');
        return;
    }

    // Create suggestion box
    const suggestionBox = document.createElement('div');
    suggestionBox.id = 'cs-assistant-suggestion';
    suggestionBox.innerHTML = `
        <div class="cs-suggestion-container">
            <div class="cs-suggestion-header">
                <h3>AI-Generated Response Suggestion</h3>
                <span class="cs-badge">${classification?.query_type || 'customer_query'}</span>
            </div>
            <div class="cs-suggestion-body">
                <pre>${response}</pre>
            </div>
            <div class="cs-suggestion-actions">
                <button id="cs-use-response" class="cs-btn cs-btn-primary">Use This Response</button>
                <button id="cs-edit-response" class="cs-btn cs-btn-secondary">Edit</button>
                <button id="cs-dismiss" class="cs-btn cs-btn-text">Dismiss</button>
            </div>
        </div>
    `;

    replyArea.insertBefore(suggestionBox, replyArea.firstChild);

    // Add event listeners
    document.getElementById('cs-use-response')?.addEventListener('click', () => {
        copyToReply(response);
        suggestionBox.remove();
    });

    document.getElementById('cs-edit-response')?.addEventListener('click', () => {
        copyToReply(response);
        suggestionBox.remove();
    });

    document.getElementById('cs-dismiss')?.addEventListener('click', () => {
        suggestionBox.remove();
    });
}

function copyToReply(text) {
    const replyBox = document.querySelector('[role="textbox"][aria-label*="reply" i]') ||
        document.querySelector('[role="textbox"]');

    if (replyBox) {
        replyBox.focus();
        replyBox.innerText = text;

        const event = new Event('input', { bubbles: true });
        replyBox.dispatchEvent(event);

        showSuccessNotification('Response copied to reply box!');
    } else {
        // Fallback: copy to clipboard
        navigator.clipboard.writeText(text);
        showSuccessNotification('Response copied to clipboard!');
    }
}

function showSuccessNotification(message) {
    const notification = createNotification('Success', message, '#34a853');
    document.body.appendChild(notification);
    setTimeout(() => notification.remove(), 3000);
}

function showErrorNotification(message) {
    const defaultMessage = 'Could not connect to backend server. Please ensure it is running.';
    const notification = createNotification(
        'Error',
        message || defaultMessage,
        '#ea4335'
    );
    document.body.appendChild(notification);
    setTimeout(() => notification.remove(), 5000);
}

function createNotification(title, message, color) {
    const div = document.createElement('div');
    div.className = 'cs-notification';
    div.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: white;
        border-left: 4px solid ${color};
        padding: 16px;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        z-index: 10000;
        max-width: 400px;
        animation: slideIn 0.3s ease-out;
    `;

    div.innerHTML = `
        <div style="font-weight: 600; margin-bottom: 4px;">${title}</div>
        <div style="color: #5f6368; font-size: 14px;">${message}</div>
    `;

    return div;
}

// Listen for extension enable/disable
chrome.storage.onChanged.addListener((changes, namespace) => {
    if (changes[CONFIG.ENABLED_KEY]) {
        isEnabled = changes[CONFIG.ENABLED_KEY].newValue !== false;
        console.log('Extension', isEnabled ? 'enabled' : 'disabled');

        if (isEnabled) {
            initializeExtension();
        }
    }
});
