/**
 * WebSocket接続管理
 * エージェント思考のリアルタイムストリーミングを処理する
 */

class WSManager {
    constructor() {
        this.ws = null;
        this.connected = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.handlers = {};
    }

    connect() {
        // 既存の接続があれば閉じる（重複防止）
        if (this.ws) {
            console.log('[WS] Closing existing connection before re-connect');
            this.ws.onclose = null; // 切断時のリトライを一時停止
            this.ws.close();
            this.ws = null;
        }

        const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:';
        const url = `${protocol}//${location.host}/ws`;

        try {
            this.ws = new WebSocket(url);

            this.ws.onopen = () => {
                this.connected = true;
                this.reconnectAttempts = 0;
                this._updateStatus(true);
                console.log('[WS] Connected');
            };

            this.ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    this._dispatch(data);
                } catch (e) {
                    console.error('[WS] Parse error:', e);
                }
            };

            this.ws.onclose = () => {
                this.connected = false;
                this._updateStatus(false);
                console.log('[WS] Disconnected');
                this._tryReconnect();
            };

            this.ws.onerror = (err) => {
                console.error('[WS] Error:', err);
            };
        } catch (e) {
            console.error('[WS] Connection failed:', e);
            this._updateStatus(false);
        }
    }

    send(action, data = {}) {
        if (this.ws && this.connected) {
            this.ws.send(JSON.stringify({ action, ...data }));
        } else {
            console.warn('[WS] Not connected, queuing message');
        }
    }

    on(type, handler) {
        if (!this.handlers[type]) this.handlers[type] = [];
        // 同じ関数が既に登録されている場合はスキップ（多重登録防止）
        if (this.handlers[type].includes(handler)) {
            console.warn(`[WS] Handler for ${type} already registered, skipping`);
            return;
        }
        this.handlers[type].push(handler);
    }

    _dispatch(data) {
        const handlers = this.handlers[data.type] || [];
        handlers.forEach(fn => fn(data));
    }

    _updateStatus(online) {
        const indicator = document.getElementById('status-indicator');
        const text = indicator?.querySelector('.status-text');
        if (indicator) {
            indicator.className = `status-dot ${online ? 'online' : 'offline'}`;
        }
        if (text) {
            text.textContent = online ? 'Online' : 'Offline';
        }
    }

    _tryReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 10000);
            console.log(`[WS] Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`);
            setTimeout(() => this.connect(), delay);
        }
    }
}

// グローバルインスタンス
const wsManager = new WSManager();
