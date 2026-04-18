/**
 * レンダラー
 * 脚本パッケージ・日記データをHTML要素にレンダリングする
 */

/**
 * アーティファクトごとのアクションバー（再生成・編集ボタン）
 */
function artifactActionBar(artifactName) {
    return `
        <div class="artifact-actions">
            <button class="btn-artifact" onclick="openRegenerateModal('${artifactName}')" title="AIで再生成">
                <span class="btn-artifact-icon">&#x21bb;</span> 再生成
            </button>
            <button class="btn-artifact" onclick="openEditModal('${artifactName}')" title="JSONを直接編集">
                <span class="btn-artifact-icon">&#x270E;</span> 編集
            </button>
        </div>
    `;
}

const Renderer = {
    /**
     * concept_packageを表示
     */
    renderConcept(concept) {
        if (!concept) return '<p class="text-muted">未生成</p>';
        const ps = concept.psychological_hints || {};
        const wn = ps.want_and_need || {};
        return artifactActionBar('concept_package') + `
            <div class="content-card">
                <h3>キャラクターコンセプト</h3>
                <div class="value" style="white-space:pre-wrap; line-height:1.7">${concept.character_concept || ''}</div>
            </div>
            <div class="content-card">
                <h3>物語骨格</h3>
                <div class="value" style="white-space:pre-wrap; line-height:1.7">${concept.story_outline || ''}</div>
                ${concept.narrative_theme ? `<div style="margin-top:var(--space-md)"><div class="label">通奏低音テーマ</div><div class="value">${concept.narrative_theme}</div></div>` : ''}
            </div>
            <div class="content-card">
                <h3>ジャンル・世界観</h3>
                <div class="value">${concept.genre_and_world || ''}</div>
            </div>
            <div class="content-card">
                <h3>心理学的方向性</h3>
                <div class="label">気質方向性（Cloninger系）</div>
                <div class="value">${ps.temperament_direction || ''}</div>
                <div style="margin-top: var(--space-sm)">
                    <div class="label">価値観方向性（Schwartz系）</div>
                    <div class="value">${ps.values_direction || ''}</div>
                </div>
                ${wn.want ? `
                <div style="margin-top: var(--space-md)">
                    <div class="label">Want（外的目標）</div>
                    <div class="value">${wn.want}</div>
                </div>
                <div style="margin-top: var(--space-sm)">
                    <div class="label">Need（内的必要）</div>
                    <div class="value">${wn.need || ''}</div>
                </div>
                <div style="margin-top: var(--space-sm)">
                    <div class="label">テンション</div>
                    <div class="value">${wn.tension || ''}</div>
                </div>` : ''}
                ${ps.ghost_wound_hint ? `<div style="margin-top: var(--space-sm)"><div class="label">Ghost / Wound（過去の傷）</div><div class="value">${ps.ghost_wound_hint}</div></div>` : ''}
                ${ps.lie_hint ? `<div style="margin-top: var(--space-sm)"><div class="label">Lie / Misbelief（誤った信念）</div><div class="value">${ps.lie_hint}</div></div>` : ''}
            </div>
            ${concept.interestingness_hooks?.length ? `
            <div class="content-card">
                <h3>面白さのフック</h3>
                <ul>${concept.interestingness_hooks.map(h => `<li>${h}</li>`).join('')}</ul>
            </div>` : ''}
            ${concept.reference_stories?.length ? `
            <div class="content-card">
                <h3>参考作品</h3>
                ${concept.reference_stories.map(r => `<div style="margin-bottom:8px"><strong>${r.title}</strong> (${r.author_or_source || ''}) — <span style="color:var(--text-muted)">${r.relevance || ''}</span></div>`).join('')}
            </div>` : ''}
        `;
    },

    /**
     * macro_profileを表示
     */
    renderProfile(profile) {
        if (!profile) return '<p class="text-muted">未生成</p>';
        const bi = profile.basic_info || {};
        const vf = profile.voice_fingerprint || {};
        const vc = profile.values_core || {};
        return artifactActionBar('macro_profile') + `
            <div class="content-card">
                <h3>基本情報</h3>
                <div class="label">名前</div><div class="value">${bi.name || ''}</div>
                <div class="label" style="margin-top:8px">年齢</div><div class="value">${bi.age || ''}</div>
                <div class="label" style="margin-top:8px">性別</div><div class="value">${bi.gender || ''}</div>
                <div class="label" style="margin-top:8px">職業</div><div class="value">${bi.occupation || ''}</div>
                <div class="label" style="margin-top:8px">外見</div><div class="value">${bi.appearance || ''}</div>
            </div>
            <div class="content-card">
                <h3>言語的指紋</h3>
                <div class="label">一人称</div><div class="value">${vf.first_person || ''}</div>
                <div class="label" style="margin-top:8px">口癖</div><div class="value">${(vf.speech_patterns || []).join('、')}</div>
                <div class="label" style="margin-top:8px">文末表現</div><div class="value">${(vf.sentence_endings || []).join('、')}</div>
                <div class="label" style="margin-top:8px">避ける語彙</div>
                <div class="value" style="color: var(--accent-error)">${(vf.avoided_words || []).join('、')}</div>
            </div>
            <div class="content-card">
                <h3>価値観の核</h3>
                <div class="label">最も大事なこと</div><div class="value">${vc.most_important || ''}</div>
                <div class="label" style="margin-top:8px">絶対に許せないこと</div><div class="value">${vc.absolutely_unforgivable || ''}</div>
                <div class="label" style="margin-top:8px">誇り</div><div class="value">${vc.pride || ''}</div>
                <div class="label" style="margin-top:8px">恥</div><div class="value">${vc.shame || ''}</div>
            </div>
        `;
    },

    /**
     * ミクロパラメータを可視化
     */
    renderParameters(params) {
        if (!params) return '<p class="text-muted">未生成</p>';

        const actionBar = artifactActionBar('micro_parameters');
        const renderParamList = (list, title) => {
            if (!list?.length) return '';
            return `
                <div class="content-card">
                    <h3>${title}</h3>
                    ${list.map(p => {
                        const pct = ((p.value - 1) / 4) * 100;
                        const color = p.value >= 4 ? 'var(--accent-primary)' :
                                      p.value >= 3 ? 'var(--accent-secondary)' :
                                      p.value >= 2 ? 'var(--accent-warning)' : 'var(--accent-error)';
                        return `
                            <div class="param-bar-container" title="${p.natural_language || ''}">
                                <span class="param-name">#${p.id} ${p.name}</span>
                                <div class="param-bar">
                                    <div class="param-bar-fill" style="width:${pct}%; background:${color}"></div>
                                </div>
                                <span class="param-value-label">${p.value?.toFixed(1)}</span>
                            </div>
                        `;
                    }).join('')}
                </div>
            `;
        };

        return actionBar +
               renderParamList(params.temperament, '気質パラメータ（23個）') +
               renderParamList(params.personality, '性格パラメータ（27個）') +
               renderParamList(params.other_cognition, '対他者認知（2個）');
    },

    /**
     * 自伝的エピソードを表示
     */
    renderEpisodes(episodes) {
        if (!episodes?.episodes?.length) return '<p class="text-muted">未生成</p>';
        return artifactActionBar('autobiographical_episodes') + episodes.episodes.map(ep => `
            <div class="content-card">
                <h3>${ep.id} — ${ep.metadata?.category || ''}</h3>
                <div class="event-meta" style="margin-bottom: var(--space-sm)">
                    <span class="event-badge medium">${ep.metadata?.life_period || ''}</span>
                    <span class="event-badge ${ep.metadata?.category === 'contamination' ? 'low' : ep.metadata?.category === 'redemption' ? 'high' : 'medium'}">${ep.metadata?.category || ''}</span>
                    ${ep.metadata?.unresolved ? '<span class="event-badge low">unresolved</span>' : ''}
                </div>
                <p>${ep.narrative || ''}</p>
            </div>
        `).join('');
    },

    /**
     * イベント列をタイムライン表示
     */
    renderEvents(store) {
        if (!store?.events?.length) return '<p class="text-muted">未生成</p>';
        const actionBar = artifactActionBar('weekly_events_store');
        const byDay = {};
        store.events.forEach(evt => {
            if (!byDay[evt.day]) byDay[evt.day] = [];
            byDay[evt.day].push(evt);
        });

        return actionBar + Object.keys(byDay).sort((a, b) => a - b).map(day => `
            <div class="event-day-group">
                <div class="event-day-label">Day ${day}</div>
                ${byDay[day].map(evt => `
                    <div class="event-item">
                        <span class="event-time">${evt.time_slot}</span>
                        <div>
                            <div class="event-content">${evt.content}</div>
                            <div class="event-meta">
                                <span class="event-badge ${evt.expectedness}">${evt.expectedness}</span>
                                <span class="event-badge ${evt.known_to_protagonist ? 'high' : 'low'}">
                                    ${evt.known_to_protagonist ? '既知' : '未知'}
                                </span>
                                <span class="event-badge medium">${evt.narrative_arc_role}</span>
                            </div>
                            ${evt.meaning_to_character ? `<div style="font-size:0.78rem; color:var(--text-muted); margin-top:4px; font-style:italic">${evt.meaning_to_character}</div>` : ''}
                        </div>
                    </div>
                `).join('')}
            </div>
        `).join('');
    },

    /**
     * 所持品・能力・可能行動を表示
     */
    renderCapabilities(caps) {
        if (!caps) return '';
        
        const possessions = caps.possessions || [];
        const abilities = caps.abilities || [];
        const actions = caps.available_actions || [];
        
        if (!possessions.length && !abilities.length && !actions.length) return '';
        
        let html = '<div class="content-card" style="margin-bottom: 1.5rem; border-left: 3px solid var(--accent-secondary);">';
        html += '<h3 style="color: var(--accent-secondary);">所持品・能力・可能行動</h3>';
        
        if (possessions.length) {
            html += '<div style="margin-bottom: 1rem;"><div class="label" style="margin-bottom: 0.5rem;">所持品</div>';
            html += possessions.map(p => `
                <div style="margin-bottom: 0.5rem; padding: 0.5rem; background: rgba(255,255,255,0.03); border-radius: 6px;">
                    <strong>${p.name || ''}</strong>${p.always_carried ? ' <span class="event-badge high" style="font-size:0.7rem;">常に携帯</span>' : ''}
                    <div style="font-size:0.85rem; color:var(--text-muted); margin-top:2px;">${p.description || ''}</div>
                    ${p.emotional_significance ? `<div style="font-size:0.8rem; color:var(--accent-primary); margin-top:2px; font-style:italic;">${p.emotional_significance}</div>` : ''}
                </div>
            `).join('');
            html += '</div>';
        }
        
        if (abilities.length) {
            html += '<div style="margin-bottom: 1rem;"><div class="label" style="margin-bottom: 0.5rem;">能力</div>';
            html += abilities.map(a => `
                <div style="margin-bottom: 0.5rem; padding: 0.5rem; background: rgba(255,255,255,0.03); border-radius: 6px;">
                    <strong>${a.name || ''}</strong> <span class="event-badge medium" style="font-size:0.7rem;">${a.proficiency || ''}</span>
                    <div style="font-size:0.85rem; color:var(--text-muted); margin-top:2px;">${a.description || ''}</div>
                </div>
            `).join('');
            html += '</div>';
        }
        
        if (actions.length) {
            html += '<div><div class="label" style="margin-bottom: 0.5rem;">可能行動</div>';
            html += actions.map(a => `
                <div style="margin-bottom: 0.5rem; padding: 0.5rem; background: rgba(255,255,255,0.03); border-radius: 6px;">
                    <strong>${a.action || ''}</strong>
                    <div style="font-size:0.85rem; color:var(--text-muted); margin-top:2px;">${a.context || ''}</div>
                </div>
            `).join('');
            html += '</div>';
        }
        
        html += '</div>';
        return html;
    },

    /**
     * 日記を表示
     */
    renderDiary(diaries) {
        if (!diaries?.length) return '';
        return diaries.map(d => `
            <div class="diary-entry-card" data-day="Day ${d.day}">
                <div class="diary-text">${d.content}</div>
            </div>
        `).join('');
    }
};
