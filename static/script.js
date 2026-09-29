// ═══════════════════════════════════════════════════
//              PARTICLES BACKGROUND
// ═══════════════════════════════════════════════════

function createParticles() {
    const container = document.getElementById('particles');
    const count = 60;

    for (let i = 0; i < count; i++) {
        const p = document.createElement('div');
        p.className = 'particle';
        p.style.left = Math.random() * 100 + '%';
        p.style.width = p.style.height = (Math.random() * 3 + 2) + 'px';
        p.style.animationDuration = (Math.random() * 12 + 8) + 's';
        p.style.animationDelay = Math.random() * 8 + 's';
        p.style.opacity = Math.random() * 0.6 + 0.3;
        container.appendChild(p);
    }
}

// ═══════════════════════════════════════════════════
//                    UTILITIES
// ═══════════════════════════════════════════════════

const sentimentEmojis = {
    'Very Positive': '😄',
    'Positive': '🙂',
    'Neutral': '😐',
    'Negative': '🙁',
    'Very Negative': '😡'
};

const sentimentColors = {
    'Very Positive': '#43e97b',
    'Positive': '#38f9d7',
    'Neutral': '#fee140',
    'Negative': '#fa709a',
    'Very Negative': '#f5576c'
};

function showToast(message, isError = false) {
    const existing = document.querySelector('.toast');
    if (existing) existing.remove();

    const toast = document.createElement('div');
    toast.className = 'toast' + (isError ? ' error' : '');
    toast.innerHTML = `<i class="fas ${isError ? 'fa-exclamation-circle' : 'fa-check-circle'}"></i> ${message}`;
    document.body.appendChild(toast);

    setTimeout(() => toast.classList.add('show'), 50);
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 400);
    }, 3000);
}

function formatDate(dateStr) {
    const d = new Date(dateStr);
    const now = new Date();
    const diff = Math.floor((now - d) / 1000);

    if (diff < 60) return 'just now';
    if (diff < 3600) return Math.floor(diff / 60) + 'm ago';
    if (diff < 86400) return Math.floor(diff / 3600) + 'h ago';
    if (diff < 604800) return Math.floor(diff / 86400) + 'd ago';

    return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}

// ═══════════════════════════════════════════════════
//                ANALYZE TEXT
// ═══════════════════════════════════════════════════

async function analyzeText() {
    const text = document.getElementById('textInput').value.trim();

    if (!text) {
        showToast('Please enter some text first', true);
        return;
    }

    const btn = document.getElementById('analyzeBtn');
    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Analyzing...';

    try {
        const res = await fetch('/api/analyze', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text })
        });

        const data = await res.json();

        if (!res.ok) {
            showToast(data.error || 'Analysis failed', true);
            return;
        }

        displayResult(data);
        loadHistory();
        loadStats();
        showToast('Analysis complete!');
    } catch (err) {
        console.error(err);
        showToast('Network error', true);
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<i class="fas fa-magic"></i> Analyze Sentiment';
    }
}

function displayResult(data) {
    document.getElementById('emptyResult').style.display = 'none';
    document.getElementById('resultContent').style.display = 'block';

    const color = data.color;

    document.getElementById('emojiBig').textContent = data.emoji;
    document.getElementById('sentimentLabel').textContent = data.sentiment;
    document.getElementById('sentimentLabel').style.color = color;
    document.getElementById('confidenceLabel').textContent =
        `Confidence: ${data.confidence}%`;

    document.getElementById('polarityVal').textContent = data.polarity.toFixed(2);
    document.getElementById('subjectivityVal').textContent = data.subjectivity.toFixed(2);
    document.getElementById('wordsVal').textContent = data.word_count;
    document.getElementById('sentencesVal').textContent = data.sentence_count;

    // Polarity indicator position: map [-1, 1] → [0%, 100%]
    const pct = ((data.polarity + 1) / 2) * 100;
    const indicator = document.getElementById('polarityIndicator');
    indicator.style.left = pct + '%';
    indicator.style.color = color;

    // Keywords
    const kw = document.getElementById('keywordsList');
    if (data.keywords && data.keywords.length > 0) {
        kw.innerHTML = data.keywords
            .map(k => `<span class="keyword">${k.word} ×${k.count}</span>`)
            .join('');
    } else {
        kw.innerHTML = '<span style="color:rgba(255,255,255,0.4);font-size:0.85rem;">No keywords extracted</span>';
    }
}

// ═══════════════════════════════════════════════════
//                   LOAD HISTORY
// ═══════════════════════════════════════════════════

async function loadHistory() {
    try {
        const res = await fetch('/api/history?limit=30');
        const data = await res.json();

        const list = document.getElementById('historyList');

        if (!data.history || data.history.length === 0) {
            list.innerHTML = `
                <div style="text-align:center;padding:40px;color:rgba(255,255,255,0.4);">
                    <i class="fas fa-inbox" style="font-size:3rem;opacity:0.3;display:block;margin-bottom:15px;"></i>
                    No analyses yet. Try analyzing some text!
                </div>`;
            return;
        }

        list.innerHTML = data.history.map(h => {
            const emoji = sentimentEmojis[h.sentiment] || '😐';
            const color = sentimentColors[h.sentiment] || '#fff';
            const text = h.text.length > 90
                ? h.text.substring(0, 90) + '...'
                : h.text;

            return `
                <div class="history-item">
                    <div class="history-emoji" style="color:${color};">${emoji}</div>
                    <div class="history-body">
                        <div class="history-text">${escapeHtml(text)}</div>
                        <div class="history-meta">
                            <span class="history-pill">${h.sentiment}</span>
                            <span><i class="fas fa-wave-square"></i> ${h.polarity.toFixed(2)}</span>
                            <span><i class="fas fa-clock"></i> ${formatDate(h.created_at)}</span>
                        </div>
                    </div>
                    <button class="btn-delete" onclick="deleteAnalysis(${h.id})">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>`;
        }).join('');
    } catch (err) {
        console.error(err);
    }
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ═══════════════════════════════════════════════════
//                 DELETE ANALYSIS
// ═══════════════════════════════════════════════════

async function deleteAnalysis(id) {
    try {
        await fetch(`/api/history/${id}`, { method: 'DELETE' });
        showToast('Deleted');
        loadHistory();
        loadStats();
    } catch (err) {
        showToast('Delete failed', true);
    }
}

// ═══════════════════════════════════════════════════
//                   LOAD STATS
// ═══════════════════════════════════════════════════

async function loadStats() {
    try {
        const res = await fetch('/api/stats');
        const data = await res.json();

        document.getElementById('statTotal').textContent = data.total;

        const dist = data.distribution || {};
        const pos = (dist['Very Positive'] || 0) + (dist['Positive'] || 0);
        const neu = dist['Neutral'] || 0;
        const neg = (dist['Very Negative'] || 0) + (dist['Negative'] || 0);

        animateNumber('statPositive', pos);
        animateNumber('statNeutral', neu);
        animateNumber('statNegative', neg);
    } catch (err) {
        console.error(err);
    }
}

function animateNumber(id, target) {
    const el = document.getElementById(id);
    const start = parseInt(el.textContent) || 0;
    const duration = 600;
    const startTime = performance.now();

    function step(t) {
        const progress = Math.min((t - startTime) / duration, 1);
        const current = Math.round(start + (target - start) * progress);
        el.textContent = current;
        if (progress < 1) requestAnimationFrame(step);
    }
    requestAnimationFrame(step);
}

// ═══════════════════════════════════════════════════
//                 RANDOM EXAMPLE
// ═══════════════════════════════════════════════════

let examplesCache = [];

async function fillRandomExample() {
    try {
        if (examplesCache.length === 0) {
            const res = await fetch('/api/examples');
            const data = await res.json();
            examplesCache = data.examples;
        }
        const random = examplesCache[Math.floor(Math.random() * examplesCache.length)];
        document.getElementById('textInput').value = random;
        updateCharCount();
    } catch (err) {
        console.error(err);
    }
}

// ═══════════════════════════════════════════════════
//                  CHAR COUNTER
// ═══════════════════════════════════════════════════

function updateCharCount() {
    const len = document.getElementById('textInput').value.length;
    document.getElementById('charCount').textContent = len;
}

// ═══════════════════════════════════════════════════
//                 CLEAR HISTORY
// ═══════════════════════════════════════════════════

async function clearHistory() {
    if (!confirm('Delete ALL history? This cannot be undone.')) return;
    try {
        await fetch('/api/history/clear', { method: 'POST' });
        showToast('History cleared');
        loadHistory();
        loadStats();
    } catch (err) {
        showToast('Failed to clear', true);
    }
}

// ═══════════════════════════════════════════════════
//                    INIT
// ═══════════════════════════════════════════════════

document.addEventListener('DOMContentLoaded', () => {
    createParticles();
    loadHistory();
    loadStats();

    // Event listeners
    document.getElementById('analyzeBtn').addEventListener('click', analyzeText);
    document.getElementById('randomBtn').addEventListener('click', fillRandomExample);
    document.getElementById('clearBtn').addEventListener('click', () => {
        document.getElementById('textInput').value = '';
        updateCharCount();
        document.getElementById('resultContent').style.display = 'none';
        document.getElementById('emptyResult').style.display = 'block';
    });
    document.getElementById('clearHistoryBtn').addEventListener('click', clearHistory);

    document.getElementById('exportCsvBtn').addEventListener('click', () => {
        window.location.href = '/api/export/csv';
    });
    document.getElementById('exportJsonBtn').addEventListener('click', () => {
        window.location.href = '/api/export/json';
    });

    // Char counter
    document.getElementById('textInput').addEventListener('input', updateCharCount);

    // Ctrl+Enter to analyze
    document.getElementById('textInput').addEventListener('keydown', (e) => {
        if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
            analyzeText();
        }
    });
});