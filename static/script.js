/**
 * Common JavaScript functionality for the AI Challenge Game
 */

// Show a toast notification
function showNotification(message, type = 'info') {
    const toast = document.getElementById('notification-toast');
    const messageEl = document.getElementById('notification-message');
    
    if (!toast || !messageEl) return;
    
    // Set message
    messageEl.textContent = message;
    
    // Set color based on type
    if (type === 'success') {
        toast.classList.add('bg-green-700');
        toast.classList.remove('bg-gray-800', 'bg-red-700');
    } else if (type === 'error') {
        toast.classList.add('bg-red-700');
        toast.classList.remove('bg-gray-800', 'bg-green-700');
    } else {
        toast.classList.add('bg-gray-800');
        toast.classList.remove('bg-green-700', 'bg-red-700');
    }
    
    // Show toast
    toast.classList.remove('translate-y-20', 'opacity-0');
    toast.classList.add('translate-y-0', 'opacity-100');
    
    // Hide after 3 seconds
    setTimeout(() => {
        toast.classList.add('translate-y-20', 'opacity-0');
        toast.classList.remove('translate-y-0', 'opacity-100');
    }, 3000);
}

// Show/hide loading overlay
function toggleLoading(show, message = 'Loading...') {
    const overlay = document.getElementById('loading-overlay');
    const loadingMessage = document.getElementById('loading-message');
    
    if (!overlay) return;
    
    if (show) {
        if (loadingMessage) loadingMessage.textContent = message;
        overlay.classList.remove('hidden');
        overlay.classList.add('flex');
    } else {
        overlay.classList.add('hidden');
        overlay.classList.remove('flex');
    }
}

// Format time in MM:SS
function formatTime(seconds) {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
}

// Get URL parameters
function getUrlParams() {
    const params = {};
    const queryString = window.location.search;
    const urlParams = new URLSearchParams(queryString);
    
    for (const [key, value] of urlParams.entries()) {
        params[key] = value;
    }
    
    return params;
}

// Connect to Socket.IO and return the socket
function connectSocket() {
    return io();
}
