/**
 * メインアプリケーションロジック
 * 画面遷移、WebSocketイベント処理、データ管理
 */

let currentPackage = null;
let currentSessionId = null;
let diaryEntries = [];
let isWSHandlersSetup = false;
let recentThoughts = new Set(); // 重複排除用

// ─── 初期化 ──────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {
    wsManager.connect();
    setupWSHandlers();
});

function setupWSHandlers() {
    if (isWSHandlersSetup) return;
    
    wsManager.on('agent_thought', (data) => {
        addThought(data.agent, data.content, data.status, data.model);
        
        // Session IDの抽出（バックエンドからの通知）
        if (data.agent === 'System' && data.content.includes('Session ID:')) {
            currentSessionId = data.content.split('Session ID:')[1].trim();
        }
    });

    wsManager.on('progress', (data) => {
        updateProgress(data.phase, data.progress, data.detail);
        updatePhaseTracker(data.phase, data.progress);
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
        
        // キャラクター生成中のエラーなら再開ボタンを表示
        if (currentSessionId && !currentPackage) {
            showResumeButton();
        }
    });

    isWSHandlersSetup = true;
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

function regenerateCharacter() {
    if (confirm("現在作成したDay 0のキャラクター設定を破棄して、もう一度最初から作り直しますか？")) {
        currentPackage = null;
        diaryEntries = [];
        backToStart();
    }
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

function toggleAllEvaluators() {
    const checkboxes = document.querySelectorAll('#evaluator-checkboxes input[type="checkbox"]');
    if (!checkboxes || checkboxes.length === 0) return;
    
    // Check if at least one is unchecked. If so, turn all ON. Otherwise turn all OFF.
    let anyUnchecked = false;
    checkboxes.forEach(cb => { if (!cb.checked) anyUnchecked = true; });
    
    checkboxes.forEach(cb => { cb.checked = anyUnchecked; });
}

// ─── キャラクター生成 ────────────────────────────────────

function startGeneration(mode) {
    showScreen('generation-screen');
    document.getElementById('thought-log').innerHTML = '';
    document.getElementById('progress-bar').style.width = '0%';
    document.getElementById('phase-tracker-container').style.display = 'flex';
    resetPhaseTracker();

    const profileSelect = document.getElementById('profile-select');
    const profile = profileSelect ? profileSelect.value : 'draft';

    const evaluators = {
        schema_validator_enabled: document.getElementById('eval-schema')?.checked ?? true,
        consistency_checker_enabled: document.getElementById('eval-consistency')?.checked ?? false,
        bias_auditor_enabled: document.getElementById('eval-bias')?.checked ?? false,
        interestingness_evaluator_enabled: document.getElementById('eval-interestingness')?.checked ?? false,
        event_metadata_auditor_enabled: document.getElementById('eval-event')?.checked ?? false,
        distribution_validator_enabled: document.getElementById('eval-distribution')?.checked ?? true,
        narrative_connection_auditor_enabled: document.getElementById('eval-narrative')?.checked ?? false
    };

    if (mode === 'theme') {
        const theme = document.getElementById('theme-input').value.trim();
        wsManager.send('generate_character', { profile, theme: theme || null, evaluators_override: evaluators });
        addThought('System', `テーマ指定モードで生成開始 (${profile})`, 'thinking');
    } else {
        wsManager.send('generate_character', { profile, theme: null, evaluators_override: evaluators });
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
                currentPackage._package_name = result.package_name;
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
function resumeGeneration() {
    if (!currentSessionId) {
        alert("再開可能なセッションが見つかりません");
        return;
    }
    
    // UIを生成中モードに維持/再セット
    document.querySelector('.thought-entry.error')?.remove();
    const btn = document.getElementById('resume-btn');
    if (btn) btn.remove();
    
    const profileSelect = document.getElementById('profile-select');
    const profile = profileSelect ? profileSelect.value : 'draft';

    const evaluators = {};
    document.querySelectorAll('#evaluator-checkboxes input[type="checkbox"]').forEach(cb => {
        evaluators[cb.name] = cb.checked;
    });

    wsManager.send('resume_generation', {
        character_name: currentSessionId,
        profile: profile,
        evaluators_override: evaluators
    });
    
    addThought('System', 'チェックポイントから再開中...', 'thinking');
}

function showResumeButton() {
    const log = document.getElementById('thought-log');
    if (!log) return;
    
    if (document.getElementById('resume-btn')) return;

    const container = document.createElement('div');
    container.id = 'resume-btn-container';
    container.style.padding = '1.5rem';
    container.style.background = 'var(--bg-secondary)';
    container.style.border = '1px solid rgba(239, 68, 68, 0.2)';
    container.style.borderRadius = '12px';
    container.style.marginTop = '1rem';
    container.style.textAlign = 'center';

    const msg = document.createElement('p');
    msg.textContent = 'エラーが発生しましたが、チェックポイントが保存されています。';
    msg.style.marginBottom = '1rem';
    msg.style.color = 'var(--accent-error)';
    msg.style.fontSize = '0.9rem';
    container.appendChild(msg);

    const btn = document.createElement('button');
    btn.id = 'resume-btn';
    btn.className = 'btn-primary';
    btn.style.padding = '0.8rem 1.5rem';
    btn.textContent = '🔄 中断した箇所から再開する';
    btn.onclick = resumeGeneration;
    container.appendChild(btn);
    
    log.appendChild(container);
    log.scrollTop = log.scrollHeight;
}

// ─── 日記生成 ─────────────────────────────────────────────

function generateDiary() {
    if (!currentPackage?.metadata) {
        alert('先にキャラクターを生成してください');
        return;
    }
    
    // UIをインライン生成モードに切り替え
    document.getElementById('diary-start-panel').style.display = 'none';
    document.getElementById('diary-generation-area').style.display = 'block';
    document.getElementById('diary-thought-log').innerHTML = '';
    document.getElementById('diary-progress-bar').style.width = '0%';
    document.getElementById('diary-gen-detail').textContent = '開始準備中...';
    
    // 既存の日記表示をクリア
    diaryEntries = [];
    document.getElementById('diary-content').innerHTML = '';
    
    const pkgName = currentPackage._package_name || 'unknown';
    wsManager.send('generate_diary', { package_name: pkgName, days: 7 });
    
    addThought('System', '7日分の日記生成を開始', 'thinking');
}

function cancelDiary() {
    wsManager.send('cancel_diary', {});
    
    // UIを初期状態へ戻す
    document.getElementById('diary-generation-area').style.display = 'none';
    document.getElementById('diary-start-panel').style.display = 'block';
    
    diaryEntries = [];
    document.getElementById('diary-content').innerHTML = '';
    
    addThought('System', '日記生成をキャンセルしてリセットしました', 'error');
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

function addThought(agent, content, status, model = null) {
    // 重複排除ロジック
    const hash = `${agent}|${content}|${status}|${model}`;
    if (recentThoughts.has(hash)) return;
    recentThoughts.add(hash);
    setTimeout(() => recentThoughts.delete(hash), 500);

    // 日記生成エリアがアクティブならそちらに出力、それ以外はDay0用に出力
    const isDiaryMode = document.getElementById('diary-generation-area')?.style.display === 'block';
    const log = isDiaryMode ? document.getElementById('diary-thought-log') : document.getElementById('thought-log');
    
    if (!log) return;

    const entry = document.createElement('div');
    entry.className = `thought-entry ${status || ''}`;
    
    const time = new Date().toLocaleTimeString('ja-JP', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    const modelBadge = model ? `<span class="model-badge">${model}</span>` : '';
    
    entry.innerHTML = `
        <span style="color:var(--text-muted)">${time}</span> 
        <span class="agent-name">${agent}</span>
        ${modelBadge}
        ${content.replace(/\n/g, '<br>')}
    `;
    
    log.appendChild(entry);
    log.scrollTop = log.scrollHeight;
}

// ─── 進捗更新 ─────────────────────────────────────────────

function updateProgress(phase, progress, detail) {
    const bar = document.getElementById('progress-bar');
    const diaryBar = document.getElementById('diary-progress-bar');
    const phaseEl = document.getElementById('gen-phase');
    const detailEl = document.getElementById('gen-detail');
    const diaryDetailEl = document.getElementById('diary-gen-detail');
    
    const percent = `${Math.min(progress * 100, 100)}%`;
    if (bar) bar.style.width = percent;
    if (diaryBar) diaryBar.style.width = percent;
    
    const phaseNames = {
        'creative_director': 'Creative Director',
        'phase_a1': 'Phase A-1: マクロプロフィール',
        'phase_a2': 'Phase A-2: ミクロパラメータ',
        'phase_a3': 'Phase A-3: 自伝的エピソード',
        'phase_d': 'Phase D: イベント列',
        'daily_loop': '日記生成',
        'complete': '完了！',
    };
    
    // 「完了」や「daily_loop」の時、日記側の詳細表示も更新する
    if (phaseEl) phaseEl.textContent = phaseNames[phase] || phase;
    if (detailEl) detailEl.textContent = detail || '';
    if (diaryDetailEl && (phase === 'daily_loop' || phase === 'complete')) {
        diaryDetailEl.textContent = detail || '';
    }
}

// ─── フェーズトラッカー ────────────────────────────────ーー

const PHASE_ORDER = ['creative_director', 'phase_a1', 'phase_a2', 'phase_a3', 'phase_d'];

function resetPhaseTracker() {
    PHASE_ORDER.forEach(p => {
        const el = document.getElementById(`step-${p}`);
        if (el) {
            el.classList.remove('active', 'completed');
        }
    });
}

function updatePhaseTracker(phase, progress) {
    if (phase === 'init') {
        resetPhaseTracker();
        return;
    }
    
    const currentIndex = PHASE_ORDER.indexOf(phase);
    
    PHASE_ORDER.forEach((p, index) => {
        const el = document.getElementById(`step-${p}`);
        if (!el) return;
        
        if (index < currentIndex || (index === currentIndex && progress >= 1.0)) {
            el.classList.add('completed');
            el.classList.remove('active');
        } else if (index === currentIndex) {
            el.classList.add('active');
            el.classList.remove('completed');
        } else {
            el.classList.remove('active', 'completed');
        }
    });
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
