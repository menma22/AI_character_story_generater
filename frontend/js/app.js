/**
 * メインアプリケーションロジック
 * 画面遷移、WebSocketイベント処理、データ管理
 */

let currentPackage = null;
let diaryEntries = [];

// ─── 初期化 ──────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {
    wsManager.connect();
    setupWSHandlers();
});

function setupWSHandlers() {
    wsManager.on('agent_thought', (data) => {
        addThought(data.agent, data.content, data.status);
    });

    wsManager.on('progress', (data) => {
        updateProgress(data.phase, data.progress, data.detail);
    });

    wsManager.on('phase_result', (data) => {
        if (data.phase === 'complete') {
            onGenerationComplete(data.result);
        }
    });

    wsManager.on('diary_entry', (data) => {
        addDiaryEntry(data.day, data.content);
    });

    wsManager.on('cost_update', (data) => {
        document.getElementById('cost-value').textContent = `$${(data.data?.estimated_cost_usd || 0).toFixed(2)}`;
    });

    wsManager.on('error', (data) => {
        addThought('System', data.content, 'error');
    });
}

// ─── 画面遷移 ────────────────────────────────────────────

function showScreen(screenId) {
    document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
    const target = document.getElementById(screenId);
    if (target) target.classList.add('active');
}

function backToStart() {
    showScreen('start-screen');
}

function showThemeInput() {
    document.getElementById('theme-input-area').classList.remove('hidden');
}

function hideThemeInput() {
    document.getElementById('theme-input-area').classList.add('hidden');
}

function showHistory() {
    showScreen('history-screen');
    loadHistory();
}

// ─── キャラクター生成 ────────────────────────────────────

function startGeneration(mode) {
    showScreen('generation-screen');
    document.getElementById('thought-log').innerHTML = '';
    document.getElementById('progress-bar').style.width = '0%';

    const profileSelect = document.getElementById('profile-select');
    const profile = profileSelect ? profileSelect.value : 'draft';

    if (mode === 'theme') {
        const theme = document.getElementById('theme-input').value.trim();
        wsManager.send('generate_character', { profile, theme: theme || null });
        addThought('System', `テーマ指定モードで生成開始 (${profile})`, 'thinking');
    } else {
        wsManager.send('generate_character', { profile, theme: null });
        addThought('System', `フルオート生成開始 (${profile})`, 'thinking');
    }
}

function onGenerationComplete(result) {
    addThought('System', '✨ キャラクター生成完了！', 'complete');
    
    // パッケージデータを取得
    if (result?.package_name) {
        fetch(`/api/packages/${result.package_name}`)
            .then(r => r.json())
            .then(data => {
                currentPackage = data;
                renderResults(data);
                setTimeout(() => showScreen('result-screen'), 1500);
            })
            .catch(err => {
                console.error('Package fetch error:', err);
                setTimeout(() => showScreen('result-screen'), 1500);
            });
    } else {
        setTimeout(() => showScreen('result-screen'), 1500);
    }
}

// ─── 日記生成 ─────────────────────────────────────────────

function generateDiary() {
    if (!currentPackage?.metadata) {
        addThought('System', '先にキャラクターを生成してください', 'error');
        return;
    }
    
    showScreen('generation-screen');
    document.getElementById('thought-log').innerHTML = '';
    document.getElementById('gen-phase').textContent = '日記生成中...';
    
    // TODO: package_name を適切に取得
    const pkgName = currentPackage._package_name || 'unknown';
    wsManager.send('generate_diary', { package_name: pkgName, days: 7 });
    addThought('System', '7日分の日記生成を開始', 'thinking');
}

function addDiaryEntry(day, content) {
    diaryEntries.push({ day, content });
    
    const diaryContent = document.getElementById('diary-content');
    if (diaryContent) {
        diaryContent.innerHTML = Renderer.renderDiary(diaryEntries);
    }
    
    addThought(`Day ${day} 日記`, content.substring(0, 80) + '...', 'complete');
}

// ─── 思考ログ ─────────────────────────────────────────────

function addThought(agent, content, status) {
    const log = document.getElementById('thought-log');
    if (!log) return;

    const entry = document.createElement('div');
    entry.className = `thought-entry ${status || ''}`;
    
    const time = new Date().toLocaleTimeString('ja-JP', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    entry.innerHTML = `<span style="color:var(--text-muted)">${time}</span> <span class="agent-name">${agent}</span> ${content.replace(/\n/g, '<br>')}`;
    
    log.appendChild(entry);
    log.scrollTop = log.scrollHeight;
}

// ─── 進捗更新 ─────────────────────────────────────────────

function updateProgress(phase, progress, detail) {
    const bar = document.getElementById('progress-bar');
    const phaseEl = document.getElementById('gen-phase');
    const detailEl = document.getElementById('gen-detail');
    
    if (bar) bar.style.width = `${Math.min(progress * 100, 100)}%`;
    
    const phaseNames = {
        'creative_director': 'Creative Director',
        'phase_a1': 'Phase A-1: マクロプロフィール',
        'phase_a2': 'Phase A-2: ミクロパラメータ',
        'phase_a3': 'Phase A-3: 自伝的エピソード',
        'phase_d': 'Phase D: イベント列',
        'daily_loop': '日記生成',
        'complete': '完了！',
    };
    
    if (phaseEl) phaseEl.textContent = phaseNames[phase] || phase;
    if (detailEl) detailEl.textContent = detail || '';
}

// ─── 結果表示 ──────────────────────────────────────────────

function renderResults(pkg) {
    document.getElementById('concept-content').innerHTML = Renderer.renderConcept(pkg?.concept_package);
    document.getElementById('profile-content').innerHTML = Renderer.renderProfile(pkg?.macro_profile);
    document.getElementById('parameters-content').innerHTML = Renderer.renderParameters(pkg?.micro_parameters);
    document.getElementById('episodes-content').innerHTML = Renderer.renderEpisodes(pkg?.autobiographical_episodes);
    document.getElementById('events-content').innerHTML = Renderer.renderEvents(pkg?.weekly_events_store);
}

// ─── タブ切替 ──────────────────────────────────────────────

function switchTab(tabName) {
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
    
    document.querySelector(`[data-tab="${tabName}"]`)?.classList.add('active');
    document.getElementById(`tab-${tabName}`)?.classList.add('active');
}

// ─── 履歴 ──────────────────────────────────────────────────

async function loadHistory() {
    const list = document.getElementById('history-list');
    if (!list) return;
    
    try {
        const res = await fetch('/api/packages');
        const data = await res.json();
        
        if (data.packages?.length) {
            list.innerHTML = data.packages.map(pkg => `
                <div class="history-item" onclick="loadPackage('${pkg.name}')">
                    <div>
                        <strong>${pkg.character_name || pkg.name}</strong>
                        <div style="font-size:0.8rem; color:var(--text-muted)">${pkg.generated_at || ''}</div>
                    </div>
                    <span style="color:var(--text-muted)">→</span>
                </div>
            `).join('');
        } else {
            list.innerHTML = '<p style="color:var(--text-muted); text-align:center; padding:40px">まだパッケージがありません</p>';
        }
    } catch (e) {
        list.innerHTML = '<p style="color:var(--accent-error); text-align:center">読み込みエラー</p>';
    }
}

async function loadPackage(name) {
    try {
        const res = await fetch(`/api/packages/${name}`);
        currentPackage = await res.json();
        currentPackage._package_name = name;
        renderResults(currentPackage);
        showScreen('result-screen');
    } catch (e) {
        console.error('Package load error:', e);
    }
}

// ─── ダウンロード ────────────────────────────────────────

function downloadPackage() {
    if (!currentPackage) return;
    
    const blob = new Blob([JSON.stringify(currentPackage, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `character_package_${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
}
