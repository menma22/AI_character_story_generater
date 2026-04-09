/**
 * レンダラー
 * 脚本パッケージ・日記データをHTML要素にレンダリングする
 */

const Renderer = {
    /**
     * concept_packageを表示
     */
    renderConcept(concept) {
        if (!concept) return '<p class="text-muted">未生成</p>';
        const cc = concept.character_concept || {};
        const ps = concept.psychological_hints || {};
        const so = concept.story_outline || {};
        return `
            <div class="content-card">
                <h3>キャラクターコンセプト</h3>
                <div class="label">核心</div>
                <div class="value">${cc.core_identity || ''}</div>
                <div style="margin-top: var(--space-md)">
                    <div class="label">Want（自覚的欲求）</div>
                    <div class="value">${cc.want || ''}</div>
                </div>
                <div style="margin-top: var(--space-md)">
                    <div class="label">Need（無自覚の必要）</div>
                    <div class="value">${cc.need || ''}</div>
                </div>
                <div style="margin-top: var(--space-md)">
                    <div class="label">内部矛盾</div>
                    <div class="value">${cc.internal_contradiction || ''}</div>
                </div>
            </div>
            <div class="content-card">
                <h3>ジャンル・世界観</h3>
                <div class="value">${concept.genre_and_world || ''}</div>
            </div>
            <div class="content-card">
                <h3>心理学的方向性</h3>
                <div class="label">気質方向性</div>
                <div class="value">${ps.temperament_direction || ''}</div>
                <div style="margin-top: var(--space-sm)">
                    <div class="label">価値観方向性</div>
                    <div class="value">${ps.values_direction || ''}</div>
                </div>
                <div style="margin-top: var(--space-sm)">
                    <div class="label">キーテンション</div>
                    <div class="value">${ps.key_tension || ''}</div>
                </div>
            </div>
            <div class="content-card">
                <h3>物語骨格</h3>
                <div class="label">テーマ</div>
                <div class="value">${so.narrative_theme || ''}</div>
                <div style="margin-top: var(--space-sm)">
                    <div class="label">Day5山場</div>
                    <div class="value">${so.day5_climax_hint || ''}</div>
                </div>
                <div style="margin-top: var(--space-sm)">
                    <div class="label">感情アーク</div>
                    <div class="value">${so.emotional_arc || ''}</div>
                </div>
            </div>
            ${concept.interestingness_hooks?.length ? `
            <div class="content-card">
                <h3>面白さのフック</h3>
                <ul>${concept.interestingness_hooks.map(h => `<li>${h}</li>`).join('')}</ul>
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
        return `
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

        return renderParamList(params.temperament, '気質パラメータ（23個）') +
               renderParamList(params.personality, '性格パラメータ（27個）') +
               renderParamList(params.other_cognition, '対他者認知（2個）');
    },

    /**
     * 自伝的エピソードを表示
     */
    renderEpisodes(episodes) {
        if (!episodes?.episodes?.length) return '<p class="text-muted">未生成</p>';
        return episodes.episodes.map(ep => `
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
        const byDay = {};
        store.events.forEach(evt => {
            if (!byDay[evt.day]) byDay[evt.day] = [];
            byDay[evt.day].push(evt);
        });

        return Object.keys(byDay).sort((a, b) => a - b).map(day => `
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
