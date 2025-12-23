// 1. ダッシュボードの読み込み
async function loadAccounts() {
    const grid = document.getElementById('account-grid');
    if (!grid) return; // 登録画面では実行しない

    const res = await fetch('/accounts');
    const accounts = await res.json();

    if (accounts.length === 0) {
        grid.innerHTML = '<p>アカウントがありません。「追加」から登録してください。</p>';
        return;
    }

    grid.innerHTML = accounts.map(acc => `
        <div class="card" style="cursor: pointer;" onclick="location.href='account_detail.html?id=${acc.id}'">
            <h3>${acc.name}</h3>
            <p><span class="label">最終ツイート</span> ${acc.last_tweet}</p>
            <p><span class="label">次回予定</span> ${acc.next_scheduled}</p>
            <button onclick="event.stopPropagation(); testPost(${acc.id})" style="margin-top:10px; cursor:pointer;">Hello Worldテスト</button>
        </div>
    `).join('');
}

// 2. テスト投稿
async function testPost(accountId) {
    const res = await fetch(`/accounts/${accountId}/test-tweet`, { method: 'POST' });
    if (res.ok) alert('ツイート成功！');
    else alert('エラーが発生しました');
}

// 3. 詳細画面のデータを読み込む
async function loadAccountDetail(id) {
    const res = await fetch(`/accounts/${id}/tweets`);
    const data = await res.json();
    
    document.getElementById('account-name').innerText = `${data.account_name} の投稿管理`;

    const scheduledList = document.getElementById('scheduled-list');
    const historyList = document.getElementById('history-list');

    // 予約(is_posted: false)と履歴(is_posted: true)に振り分け
    const scheduled = data.tweets.filter(t => !t.is_posted);
    const history = data.tweets.filter(t => t.is_posted);

    scheduledList.innerHTML = scheduled.map(t => `
        <div class="card">
            <p>${t.content}</p>
            <p class="label">予定: ${new Date(t.scheduled_at).toLocaleString()}</p>
        </div>
    `).join('') || '<p>予定はありません</p>';

    historyList.innerHTML = history.map(t => `
        <div class="card" style="background: #f0f0f0;">
            <p>${t.content}</p>
            <p class="label">投稿済: ${new Date(t.posted_at).toLocaleString()}</p>
        </div>
    `).join('') || '<p>履歴はありません</p>';
}

// 4. 予約フォームの送信処理
const tweetForm = document.getElementById('tweetForm');
if (tweetForm) {
    tweetForm.onsubmit = async (e) => {
        e.preventDefault();
        const urlParams = new URLSearchParams(window.location.search);
        const id = urlParams.get('id');

        const data = {
            content: document.getElementById('content').value,
            scheduled_at: document.getElementById('scheduled_at').value
        };

        const res = await fetch(`/accounts/${id}/tweets`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        if (res.ok) {
            alert('予約しました！');
            location.reload(); // 再読み込みして一覧を更新
        }
    };
}

// ダッシュボード読み込み（index.htmlで実行）
loadAccounts();
