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
    loadSettings(); // APIキーの読み込み
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
        } else if (data.phase === 'regenerate_complete') {
            onRegenerationComplete(data.result);
        } else if (data.phase === 'concept_review') {
            onConceptReview(data.result);
        }
    });

    wsManager.on('edit_saved', (data) => {
        addThought('System', data.message || `${data.artifact} の編集を保存しました`, 'complete');
        // パッケージを再取得して再描画
        if (data.package_name && currentPackage) {
            fetch(`/api/packages/${data.package_name}`)
                .then(r => r.json())
                .then(pkg => {
                    currentPackage = pkg;
                    currentPackage._package_name = data.package_name;
                    renderResults(pkg);
                });
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

    // キャラクター生成中断完了のハンドラ
    wsManager.on('generation_cancelled', (data) => {
        addThought('System', '⏹ 生成が中断されました。そこまでのデータをダッシュボードに表示します。', 'complete');
        
        const pkgName = data.package_name;
        if (pkgName) {
            // 中断時点までのデータを取得してダッシュボードに表示
            fetch(`/api/packages/${pkgName}`)
                .then(r => r.json())
                .then(pkg => {
                    currentPackage = pkg;
                    currentPackage._package_name = pkgName;
                    renderResults(pkg);
                    setTimeout(() => showScreen('result-screen'), 800);
                })
                .catch(err => {
                    console.error('Partial package fetch error:', err);
                    addThought('System', 'パーシャルデータの取得に失敗しました。履歴から確認してください。', 'error');
                });
        } else {
            addThought('System', '保存されたデータが見つかりませんでした。', 'error');
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

    // 構成プリファレンスの収集
    const compositionPreferences = collectCompositionPreferences();

    if (mode === 'theme') {
        const theme = document.getElementById('theme-input').value.trim();
        wsManager.send('generate_character', {
            profile,
            theme: theme || null,
            evaluators_override: evaluators,
            api_keys: getApiKeys(),
            composition_preferences: compositionPreferences,
        });
        addThought('System', `テーマ指定モードで生成開始 (${profile})`, 'thinking');
    } else {
        wsManager.send('generate_character', {
            profile,
            theme: null,
            evaluators_override: evaluators,
            api_keys: getApiKeys(),
            composition_preferences: compositionPreferences,
        });
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
        evaluators_override: evaluators,
        api_keys: getApiKeys()
    });
    
    addThought('System', 'チェックポイントから再開中...', 'thinking');
}

function cancelCharacterGeneration() {
    if (!confirm('生成を中断しますか？\nここまでの生成データは保存され、ダッシュボードに表示されます。')) return;
    
    // キャンセルボタンを無効化
    const btn = document.getElementById('cancel-generation-btn');
    if (btn) {
        btn.disabled = true;
        btn.textContent = '⏳ 中断処理中...';
    }
    
    // バックエンドにキャンセル指示を送信
    wsManager.send('cancel_character_generation', {});
    addThought('System', '⏹ 生成中断リクエストを送信しました...', 'thinking');
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
    wsManager.send('generate_diary', { 
        package_name: pkgName, 
        days: 7,
        api_keys: getApiKeys()
    });
    
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
    // イベントタブ: capabilities + events を表示
    let eventsHtml = '';
    if (pkg?.character_capabilities) {
        eventsHtml += Renderer.renderCapabilities(pkg.character_capabilities);
    }
    eventsHtml += Renderer.renderEvents(pkg?.weekly_events_store);
    document.getElementById('events-content').innerHTML = eventsHtml;
}

// ─── タブ切替 ──────────────────────────────────────────────

function switchTab(tabName) {
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
    
    document.querySelector(`[data-tab="${tabName}"]`)?.classList.add('active');
    document.getElementById(`tab-${tabName}`)?.classList.add('active');
}

// ─── チェックポイントフェーズのラベル ────────────

const PHASE_LABELS = {
    "creative_director": "コンセプト生成中",
    "phase_a1": "マクロプロフィール生成中",
    "phase_a2": "ミクロパラメータ生成中",
    "phase_a3": "エピソード生成中",
    "phase_d": "イベント列生成中",
    "complete": "生成完了",
    "unknown": "不明",
};

// ─── 履歴 ──────────────────────────────────────────────────

async function loadHistory() {
    const list = document.getElementById('history-list');
    if (!list) return;

    try {
        const res = await fetch('/api/packages');
        const data = await res.json();

        if (data.packages?.length) {
            // 完了と未完了を分離
            const complete = data.packages.filter(p => p.status === 'complete');
            const incomplete = data.packages.filter(p => p.status === 'incomplete');

            let html = '';

            // 未完了パッケージセクション
            if (incomplete.length > 0) {
                html += '<div style="margin-bottom: 30px;"><h3 style="margin-bottom: 15px; color: var(--text-muted); font-size: 0.9rem; text-transform: uppercase;">生成中/中断中</h3>';
                html += incomplete.map(pkg => {
                    const phaseLabel = PHASE_LABELS[pkg.checkpoint_phase] || pkg.checkpoint_phase;
                    return `
                        <div class="history-item history-item-incomplete" style="display: flex; justify-content: space-between; align-items: center;">
                            <div style="flex: 1;">
                                <strong>${pkg.character_name || pkg.name}</strong>
                                <div style="font-size:0.8rem; color:var(--text-muted)">
                                    ${pkg.generated_at || ''} — <span class="status-badge incomplete">${phaseLabel}</span>
                                </div>
                            </div>
                            <button class="btn-resume" onclick="resumeFromCheckpoint('${pkg.name}', '${pkg.checkpoint_phase}')">再開</button>
                        </div>
                    `;
                }).join('');
                html += '</div>';
            }

            // 完了パッケージセクション
            if (complete.length > 0) {
                html += '<div><h3 style="margin-bottom: 15px; color: var(--text-muted); font-size: 0.9rem; text-transform: uppercase;">生成完了</h3>';
                html += complete.map(pkg => `
                    <div class="history-item" onclick="loadPackage('${pkg.name}')">
                        <div>
                            <strong>${pkg.character_name || pkg.name}</strong>
                            <div style="font-size:0.8rem; color:var(--text-muted)">${pkg.generated_at || ''}</div>
                        </div>
                        <span style="color:var(--text-muted)">→</span>
                    </div>
                `).join('');
                html += '</div>';
            }

            list.innerHTML = html;
        } else {
            list.innerHTML = '<p style="color:var(--text-muted); text-align:center; padding:40px">まだパッケージがありません</p>';
        }
    } catch (e) {
        console.error('History load error:', e);
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

async function resumeFromCheckpoint(name, phase) {
    // チェックポイントから再開
    const apiKeys = getApiKeys();
    
    // 現在のプロファイルを取得
    const profileSelect = document.getElementById('profile-select');
    const profile = profileSelect ? profileSelect.value : 'draft';

    // Evaluator設定の収集
    const evaluators = {
        schema_validator_enabled: document.getElementById('eval-schema')?.checked ?? true,
        consistency_checker_enabled: document.getElementById('eval-consistency')?.checked ?? false,
        bias_auditor_enabled: document.getElementById('eval-bias')?.checked ?? false,
        interestingness_evaluator_enabled: document.getElementById('eval-interestingness')?.checked ?? false,
        event_metadata_auditor_enabled: document.getElementById('eval-event')?.checked ?? false,
        distribution_validator_enabled: document.getElementById('eval-distribution')?.checked ?? true,
        narrative_connection_auditor_enabled: document.getElementById('eval-narrative')?.checked ?? false
    };

    // 生成画面へ移動
    showScreen('generation-screen');
    
    // UIを初期化
    document.getElementById('thought-log').innerHTML = '';
    document.getElementById('progress-bar').style.width = '0%';
    document.getElementById('phase-tracker-container').style.display = 'flex';
    resetPhaseTracker();
    
    document.querySelector('.thought-entry.error')?.remove();
    const btn = document.getElementById('resume-btn');
    if (btn) btn.remove();

    // WebSocket で resume_generation を送信
    wsManager.send('resume_generation', {
        character_name: name,
        profile: profile,
        evaluators_override: evaluators,
        api_keys: apiKeys
    });
    
    addThought('System', 'チェックポイントから再開中...', 'thinking');
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

// ─── アーティファクト再生成 ──────────────────────────────────

const ARTIFACT_LABELS = {
    concept_package: 'コンセプト',
    macro_profile: 'マクロプロフィール + 言語的表現',
    linguistic_expression: 'マクロプロフィール + 言語的表現',
    micro_parameters: 'ミクロパラメータ',
    autobiographical_episodes: '自伝的エピソード',
    weekly_events_store: 'イベント列',
};

const ARTIFACT_DEPENDENTS = {
    concept_package: ['macro_profile', 'linguistic_expression', 'micro_parameters', 'autobiographical_episodes', 'weekly_events_store'],
    macro_profile: ['micro_parameters', 'autobiographical_episodes', 'weekly_events_store'],
    linguistic_expression: [],
    micro_parameters: ['autobiographical_episodes', 'weekly_events_store'],
    autobiographical_episodes: ['weekly_events_store'],
    weekly_events_store: [],
};

// アーティファクト名 → パッケージJSONのキー
const ARTIFACT_PKG_KEYS = {
    concept_package: 'concept_package',
    macro_profile: 'macro_profile',
    linguistic_expression: 'linguistic_expression',
    micro_parameters: 'micro_parameters',
    autobiographical_episodes: 'autobiographical_episodes',
    weekly_events_store: 'weekly_events_store',
};

let currentRegenArtifact = null;
let isRegenerating = false;

function openRegenerateModal(artifactName) {
    if (isRegenerating) return;
    currentRegenArtifact = artifactName;

    const label = ARTIFACT_LABELS[artifactName] || artifactName;
    document.getElementById('regen-modal-title').textContent = `再生成: ${label}`;
    document.getElementById('regen-instructions').value = '';
    document.getElementById('regen-progress-area').classList.add('hidden');
    document.getElementById('regen-progress-bar').style.width = '0%';
    document.getElementById('regen-detail').textContent = '';
    document.getElementById('regen-submit-btn').disabled = false;

    // 下流依存の警告
    const dependents = ARTIFACT_DEPENDENTS[artifactName] || [];
    const cascadeWarning = document.getElementById('regen-cascade-warning');
    const cascadeList = document.getElementById('regen-cascade-list');
    const cascadeCheck = document.getElementById('regen-cascade-check');

    if (dependents.length > 0) {
        const depLabels = dependents.map(d => ARTIFACT_LABELS[d] || d);
        cascadeList.textContent = `影響を受けるアーティファクト: ${depLabels.join(', ')}`;
        cascadeCheck.checked = false;
        cascadeWarning.classList.remove('hidden');
    } else {
        cascadeWarning.classList.add('hidden');
    }

    document.getElementById('regenerate-modal').classList.remove('hidden');
}

function closeRegenerateModal() {
    if (isRegenerating) return;
    document.getElementById('regenerate-modal').classList.add('hidden');
    currentRegenArtifact = null;
}

function executeRegeneration() {
    if (!currentRegenArtifact || !currentPackage?._package_name || isRegenerating) return;

    isRegenerating = true;
    const instructions = document.getElementById('regen-instructions').value.trim();
    const cascade = document.getElementById('regen-cascade-check')?.checked || false;

    document.getElementById('regen-submit-btn').disabled = true;
    document.getElementById('regen-progress-area').classList.remove('hidden');
    document.getElementById('regen-detail').textContent = '再生成を開始しています...';

    wsManager.send('regenerate_artifact', {
        package_name: currentPackage._package_name,
        artifact_name: currentRegenArtifact,
        instructions: instructions,
        cascade: cascade,
        profile: document.getElementById('profile-select')?.value || 'draft',
        api_keys: getApiKeys(),
    });

    addThought('System', `「${ARTIFACT_LABELS[currentRegenArtifact]}」の再生成を開始しました`, 'thinking');
}

function onRegenerationComplete(result) {
    isRegenerating = false;

    // モーダルを閉じる
    document.getElementById('regenerate-modal').classList.add('hidden');
    currentRegenArtifact = null;

    const regenerated = (result.regenerated || []).map(a => ARTIFACT_LABELS[a] || a).join(', ');
    addThought('System', `再生成完了: ${regenerated}`, 'complete');

    // パッケージを再取得して再描画
    if (result.package_name) {
        fetch(`/api/packages/${result.package_name}`)
            .then(r => r.json())
            .then(pkg => {
                currentPackage = pkg;
                currentPackage._package_name = result.package_name;
                renderResults(pkg);
            })
            .catch(err => console.error('Package reload error:', err));
    }
}

// 再生成プログレスの更新（既存のupdateProgressと共用）
// progressイベントの phase が 'regeneration' の場合にモーダル内のプログレスバーを更新
const _originalUpdateProgress = updateProgress;
updateProgress = function(phase, progress, detail) {
    _originalUpdateProgress(phase, progress, detail);
    if (phase === 'regeneration') {
        const bar = document.getElementById('regen-progress-bar');
        const detailEl = document.getElementById('regen-detail');
        if (bar) bar.style.width = `${Math.min(progress * 100, 100)}%`;
        if (detailEl) detailEl.textContent = detail || '';
    }
};

// ─── アーティファクト編集 ──────────────────────────────────

let currentEditArtifact = null;

function openEditModal(artifactName) {
    if (!currentPackage) return;
    currentEditArtifact = artifactName;

    const key = ARTIFACT_PKG_KEYS[artifactName];
    const data = currentPackage[key];

    const label = ARTIFACT_LABELS[artifactName] || artifactName;
    document.getElementById('edit-modal-title').textContent = `JSON\u7de8\u96c6: ${label}`;
    document.getElementById('edit-json-textarea').value = JSON.stringify(data, null, 2);
    document.getElementById('edit-error-msg').classList.add('hidden');
    document.getElementById('edit-save-btn').disabled = false;

    document.getElementById('edit-modal').classList.remove('hidden');
}

function closeEditModal() {
    document.getElementById('edit-modal').classList.add('hidden');
    currentEditArtifact = null;
}

function saveArtifactEdit() {
    if (!currentEditArtifact || !currentPackage?._package_name) return;

    const textarea = document.getElementById('edit-json-textarea');
    const errorMsg = document.getElementById('edit-error-msg');

    let parsed;
    try {
        parsed = JSON.parse(textarea.value);
    } catch (e) {
        errorMsg.textContent = `JSON\u30d1\u30fc\u30b9\u30a8\u30e9\u30fc: ${e.message}`;
        errorMsg.classList.remove('hidden');
        return;
    }

    errorMsg.classList.add('hidden');
    document.getElementById('edit-save-btn').disabled = true;

    wsManager.send('save_artifact_edit', {
        package_name: currentPackage._package_name,
        artifact_name: currentEditArtifact,
        data: parsed,
    });

    addThought('System', `「${ARTIFACT_LABELS[currentEditArtifact]}」の編集を送信中...`, 'thinking');

    // モーダルを閉じる
    closeEditModal();
}
// ─── システム設定 (APIキー) ──────────────────────────────

function openSettingsModal() {
    document.getElementById('settings-modal').classList.remove('hidden');
}

function closeSettingsModal() {
    document.getElementById('settings-modal').classList.add('hidden');
}

function saveSettings() {
    const keys = {
        openai: document.getElementById('key-openai').value.trim(),
        anthropic: document.getElementById('key-anthropic').value.trim(),
        google_ai: document.getElementById('key-google_ai').value.trim(),
    };
    
    localStorage.setItem('script_ai_api_keys', JSON.stringify(keys));
    addThought('System', 'APIキー設定を保存しました', 'complete');
    closeSettingsModal();
}

function loadSettings() {
    const saved = localStorage.getItem('script_ai_api_keys');
    if (saved) {
        try {
            const keys = JSON.parse(saved);
            document.getElementById('key-openai').value = keys.openai || '';
            document.getElementById('key-anthropic').value = keys.anthropic || '';
            document.getElementById('key-google_ai').value = keys.google_ai || '';
        } catch (e) {
            console.error('Settings load error:', e);
        }
    }
}

function getApiKeys() {
    const saved = localStorage.getItem('script_ai_api_keys');
    if (!saved) return {};
    try {
        return JSON.parse(saved);
    } catch (e) {
        return {};
    }
}

// ═══════════════════════════════════════════════════════════
// Human in the Loop: 物語構成プリファレンス
// ═══════════════════════════════════════════════════════════

const COMP_FIELD_NAMES = [
    'narrative_structure', 'emotional_tone', 'character_arc',
    'theme_weight', 'climax_structure', 'genre', 'pacing', 'narrative_voice'
];

const COMP_DISPLAY_NAMES = {
    narrative_structure: '物語構造',
    emotional_tone: '感情トーン',
    character_arc: 'キャラクターアーク',
    theme_weight: 'テーマの重さ',
    climax_structure: 'クライマックス構造',
    genre: 'ジャンル',
    pacing: 'ペーシング',
    narrative_voice: '語り口',
};

function toggleCompositionPrefs() {
    const prefs = document.getElementById('composition-prefs');
    const icon = document.getElementById('comp-toggle-icon');
    if (prefs.classList.contains('hidden')) {
        prefs.classList.remove('hidden');
        icon.classList.add('open');
    } else {
        prefs.classList.add('hidden');
        icon.classList.remove('open');
    }
    updateCompositionSummary();
}

function resetAllCompositionPrefs() {
    COMP_FIELD_NAMES.forEach(name => {
        const radios = document.querySelectorAll(`input[name="comp_${name}"]`);
        radios.forEach(r => r.checked = false);
    });
    const freeNotes = document.getElementById('comp-free-notes');
    if (freeNotes) freeNotes.value = '';
    updateCompositionSummary();
}

function collectCompositionPreferences() {
    const prefs = {};
    let hasAny = false;

    COMP_FIELD_NAMES.forEach(name => {
        const checked = document.querySelector(`input[name="comp_${name}"]:checked`);
        if (checked) {
            prefs[name] = checked.value;
            hasAny = true;
        }
    });

    const freeNotes = document.getElementById('comp-free-notes')?.value?.trim();
    if (freeNotes) {
        prefs.free_notes = freeNotes;
        hasAny = true;
    }

    return hasAny ? prefs : null;
}

function updateCompositionSummary() {
    const summary = document.getElementById('composition-summary');
    if (!summary) return;

    const parts = [];
    COMP_FIELD_NAMES.forEach(name => {
        const checked = document.querySelector(`input[name="comp_${name}"]:checked`);
        if (checked) {
            // カード名を取得
            const card = checked.closest('.comp-card');
            const cardName = card?.querySelector('.comp-card-name')?.textContent || checked.value;
            parts.push(cardName);
        }
    });

    if (parts.length > 0) {
        summary.textContent = parts.join(' / ');
        summary.classList.remove('hidden');
    } else {
        summary.classList.add('hidden');
    }
}

// ラジオボタンの変更時にサマリーを更新
document.addEventListener('change', (e) => {
    if (e.target.name?.startsWith('comp_')) {
        updateCompositionSummary();
    }
});


// ═══════════════════════════════════════════════════════════
// Human in the Loop: コンセプトレビュー画面
// ═══════════════════════════════════════════════════════════

let reviewConceptData = null;

function onConceptReview(result) {
    reviewConceptData = result.concept_package;
    addThought('System', result.message || 'コンセプトレビューの準備ができました', 'complete');

    // レビュー画面にコンセプトを描画
    const content = document.getElementById('review-concept-content');
    if (content && reviewConceptData) {
        content.innerHTML = Renderer.renderConcept(reviewConceptData);
    }

    // フィードバックパネルをリセット
    hideRevisePanel();

    // レビュー画面に遷移
    showScreen('concept-review-screen');
}

function approveConceptReview() {
    wsManager.send('approve_concept', {});
    addThought('System', 'コンセプトを承認しました。下流Phaseの生成に進みます...', 'thinking');
    showScreen('generation-screen');
}

function showRevisePanel() {
    document.getElementById('revise-panel').classList.remove('hidden');
    document.getElementById('revise-feedback').value = '';
    document.getElementById('revise-feedback').focus();
}

function hideRevisePanel() {
    document.getElementById('revise-panel').classList.add('hidden');
}

function submitRevision() {
    const feedback = document.getElementById('revise-feedback').value.trim();
    if (!feedback) {
        alert('フィードバック内容を入力してください');
        return;
    }

    wsManager.send('revise_concept', { feedback });
    addThought('System', `フィードバックを送信しました: ${feedback.substring(0, 60)}...`, 'thinking');

    // 生成画面に戻してCreative Directorの再実行を表示
    showScreen('generation-screen');
}

function editConceptDirect() {
    if (!reviewConceptData) return;

    // 編集モーダルを開く（concept_packageとして）
    currentEditArtifact = 'concept_package';

    document.getElementById('edit-modal-title').textContent = 'JSON編集: コンセプト（レビュー中）';
    document.getElementById('edit-json-textarea').value = JSON.stringify(reviewConceptData, null, 2);
    document.getElementById('edit-error-msg').classList.add('hidden');
    document.getElementById('edit-save-btn').disabled = false;

    // 保存ボタンの動作をレビュー用にオーバーライド
    document.getElementById('edit-save-btn').onclick = saveConceptEditDuringReview;
    document.getElementById('edit-modal').classList.remove('hidden');
}

function saveConceptEditDuringReview() {
    const textarea = document.getElementById('edit-json-textarea');
    const errorMsg = document.getElementById('edit-error-msg');

    let parsed;
    try {
        parsed = JSON.parse(textarea.value);
    } catch (e) {
        errorMsg.textContent = `JSONパースエラー: ${e.message}`;
        errorMsg.classList.remove('hidden');
        return;
    }

    errorMsg.classList.add('hidden');

    // edit_concept_directアクションでバックエンドに送信
    wsManager.send('edit_concept_direct', { concept_package: parsed });
    addThought('System', '編集したコンセプトを適用して続行します...', 'thinking');

    // モーダルを閉じて生成画面に遷移
    document.getElementById('edit-modal').classList.add('hidden');
    // 保存ボタンの動作を元に戻す
    document.getElementById('edit-save-btn').onclick = saveArtifactEdit;
    showScreen('generation-screen');
}
