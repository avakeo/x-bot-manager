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
        <div class="card" style="cursor: pointer; position: relative;" onclick="location.href='account_detail.html?id=${acc.id}'">
            <button onclick="event.stopPropagation(); editAccount(${acc.id})" 
                    style="position:absolute; top:10px; right:10px; background:none; border:none; cursor:pointer; font-size:20px; color:#666;">
                ⚙️
            </button>
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

// アカウント編集（編集ページへリダイレクト）
function editAccount(accountId) {
    location.href = `edit_account.html?id=${accountId}`;
}

// 3. 詳細画面のデータを読み込む
async function loadAccountDetail(id) {
    const res = await fetch(`/accounts/${id}/tweets`);
    const data = await res.json();
    
    document.getElementById('account-name').innerText = `${data.account_name} の投稿管理`;

    // タイムライン表示（予約と履歴を統合）
    renderTimeline(data.tweets);
    
    // 画像読み込み
    loadImages(id);
    
    // 画像アップロード機能の初期化
    setupImageUpload(id);
    
    // 予約時間の最小値を現在時刻に設定
    setMinimumDateTime();
    
    // テキストエリアの文字数カウント
    setupCharCounter();
}

// 予約時間の最小値を現在時刻に設定（過去時間は選択不可）
function setMinimumDateTime() {
    const scheduledAtInput = document.getElementById('scheduled_at');
    const bulkStartTimeInput = document.getElementById('bulk_start_time');
    const megaStartTimeInput = document.getElementById('mega_start_time');
    
    // 現在時刻を取得して5分後の時刻を設定（推奨値）
    const now = new Date();
    now.setMinutes(now.getMinutes() + 5);
    
    // datetime-local形式（YYYY-MM-DDTHH:mm）
    const year = now.getFullYear();
    const month = String(now.getMonth() + 1).padStart(2, '0');
    const day = String(now.getDate()).padStart(2, '0');
    const hours = String(now.getHours()).padStart(2, '0');
    const minutes = String(now.getMinutes()).padStart(2, '0');
    
    const minDateTime = `${year}-${month}-${day}T${hours}:${minutes}`;
    
    // 最小値を設定（過去は選択不可）
    if (scheduledAtInput) {
        scheduledAtInput.min = minDateTime;
        scheduledAtInput.value = minDateTime;
    }
    if (bulkStartTimeInput) {
        bulkStartTimeInput.min = minDateTime;
        bulkStartTimeInput.value = minDateTime;
    }
    if (megaStartTimeInput) {
        megaStartTimeInput.min = minDateTime;
        megaStartTimeInput.value = minDateTime;
    }
}

// テキストエリアの文字数カウント
function setupCharCounter() {
    const contentInput = document.getElementById('content');
    const charCount = document.getElementById('char-count');
    
    if (!contentInput || !charCount) return;
    
    const updateCount = () => {
        const count = contentInput.value.length;
        charCount.textContent = `${count} / 280`;
        charCount.style.color = count > 280 ? '#dc3545' : '#666';
    };
    
    contentInput.addEventListener('input', updateCount);
    updateCount();
}

// グローバル変数で選択画像を管理
let selectedImages = []; // 通常/小規模用（最大4枚）
let megaSelectedImages = []; // メガ予約用（最大150枚想定）
let isMegaMode = false;
const MEGA_MAX = 150;

// 画像一覧の読み込み
async function loadImages(accountId) {
    const res = await fetch(`/accounts/${accountId}/images`);
    const images = await res.json();
    
    const gallery = document.getElementById('image-gallery');
    if (!gallery) return;
    
    gallery.innerHTML = images.map(img => `
        <img src="/uploads/${accountId}/${img}" alt="${img}" class="gallery-img" onclick="selectImage('${accountId}', '${img}', this)">
    `).join('');
}

// 画像アップロード設定
function setupImageUpload(accountId) {
    const dropZone = document.getElementById('drop-zone');
    if (!dropZone) return;
    
    // クリックでファイル選択（複数対応）
    dropZone.onclick = () => {
        const input = document.createElement('input');
        input.type = 'file';
        input.accept = 'image/*';
        input.multiple = true; // 複数ファイル選択を許可
        input.onchange = (e) => uploadImages(accountId, e.target.files);
        input.click();
    };
    
    // ドラッグ&ドロップ（複数ファイル対応）
    dropZone.ondragover = (e) => {
        e.preventDefault();
        dropZone.style.background = '#e0e0e0';
    };
    
    dropZone.ondragleave = () => {
        dropZone.style.background = '';
    };
    
    dropZone.ondrop = (e) => {
        e.preventDefault();
        dropZone.style.background = '';
        if (e.dataTransfer.files.length > 0) {
            uploadImages(accountId, e.dataTransfer.files);
        }
    };
}

// 複数画像アップロード実行
async function uploadImages(accountId, files) {
    let uploadedCount = 0;
    
    for (const file of files) {
        if (!file.type.startsWith('image/')) {
            alert(`${file.name} は画像ファイルではありません`);
            continue;
        }
        
        const formData = new FormData();
        formData.append('file', file);
        
        try {
            const res = await fetch(`/accounts/${accountId}/upload`, {
                method: 'POST',
                body: formData
            });
            
            if (res.ok) {
                uploadedCount++;
            }
        } catch (err) {
            alert(`${file.name} のアップロードに失敗しました`);
        }
    }
    
    if (uploadedCount > 0) {
        alert(`${uploadedCount}枚の画像をアップロードしました`);
        loadImages(accountId); // 再読み込み
    }
}

// 画像選択（複数対応、最大4枚）
function selectImage(accountId, imageName, imgElement) {
    const imageUrl = imgElement.src;

    // メガモード: 150枚まで選択可能（プレビュー簡易）
    if (isMegaMode) {
        const idx = megaSelectedImages.findIndex(img => img.src === imageUrl);
        if (idx === -1) {
            if (megaSelectedImages.length >= MEGA_MAX) {
                alert(`最大${MEGA_MAX}枚まで選択できます`);
                return;
            }
            megaSelectedImages.push({ src: imageUrl, name: imageName });
            imgElement.classList.add('selected');
        } else {
            megaSelectedImages.splice(idx, 1);
            imgElement.classList.remove('selected');
        }
        updateMegaSelectionStatus();
        return;
    }

    // 通常/小規模モード: 4枚まで
    const index = selectedImages.findIndex(img => img.src === imageUrl);
    
    if (index === -1) {
        if (selectedImages.length < 4) {
            selectedImages.push({ src: imageUrl, name: imageName });
            imgElement.classList.add('selected');
        } else {
            alert('最大4枚までです');
            return;
        }
    } else {
        selectedImages.splice(index, 1);
        imgElement.classList.remove('selected');
    }
    
    updateSelectedImagesPreview();
}

// 選択画像のプレビューを更新
function updateSelectedImagesPreview() {
    const preview = document.getElementById('selected-image-preview');
    if (!preview) return;
    
    if (selectedImages.length === 0) {
        preview.innerHTML = '<p style="color:#999; margin:0;">画像を選択してください（最大4枚）</p>';
        document.getElementById('image-count').textContent = '0 / 4';
        return;
    }
    
    // 画像プレビューを4つのスロットに表示
    let html = '<div class="image-preview-multi">';
    
    for (let i = 0; i < 4; i++) {
        if (i < selectedImages.length) {
            html += `
                <div class="image-item">
                    <img src="${selectedImages[i].src}" alt="${selectedImages[i].name}">
                    <button type="button" class="remove-btn" onclick="removeSelectedImage(${i})">×</button>
                </div>
            `;
        } else {
            html += '<div class="image-item" style="background:#f0f0f0; border-radius:4px;"></div>';
        }
    }
    
    html += '</div>';
    preview.innerHTML = html;
    
    // 画像数を表示
    document.getElementById('image-count').textContent = `${selectedImages.length} / 4`;
}

// 選択画像を削除（インデックス指定）
function removeSelectedImage(index) {
    if (index >= 0 && index < selectedImages.length) {
        const imageSrc = selectedImages[index].src;
        selectedImages.splice(index, 1);
        
        // ギャラリー内の対応する画像の選択状態を解除
        document.querySelectorAll('.gallery-img').forEach(img => {
            if (img.src === imageSrc) {
                img.classList.remove('selected');
            }
        });
        
        updateSelectedImagesPreview();
    }
}

// 選択画像をすべて解除
function clearSelectedImage() {
    selectedImages = [];
    document.querySelectorAll('.gallery-img').forEach(i => i.classList.remove('selected'));
    updateSelectedImagesPreview();
}

function clearMegaSelectedImages() {
    megaSelectedImages = [];
    document.querySelectorAll('.gallery-img').forEach(i => i.classList.remove('selected'));
    updateMegaSelectionStatus();
}

function updateMegaSelectionStatus() {
    const counter = document.getElementById('mega-image-count');
    if (counter) {
        counter.textContent = `${megaSelectedImages.length} / ${MEGA_MAX}`;
    }
}

// タイムライン描画（次回投稿を真ん中に配置）
function renderTimeline(tweets) {
    const timeline = document.getElementById('combined-timeline');
    if (!timeline) return;
    
    // 最新20件を上限に表示して負荷を軽減
    const posted = tweets.filter(t => t.is_posted).sort((a, b) => new Date(b.posted_at) - new Date(a.posted_at));
    const scheduled = tweets.filter(t => !t.is_posted).sort((a, b) => new Date(a.scheduled_at) - new Date(b.scheduled_at));

    const MAX_ITEMS = 20;
    const postedLimited = posted.slice(0, 5); // 投稿済みは最新5件まで
    const remainingSlots = Math.max(MAX_ITEMS - postedLimited.length, 0);
    const scheduledLimited = scheduled.slice(0, remainingSlots);
    const truncated = posted.length > postedLimited.length || scheduled.length > scheduledLimited.length;

    const nextTweet = scheduledLimited.length > 0 ? scheduledLimited[0] : null;
    const otherScheduled = scheduledLimited.slice(1);

    let html = '';

    if (postedLimited.length > 0) {
        html += '<h4 style="color:#666; font-size:0.9em; margin:15px 0 10px 0;">最近の投稿</h4>';
        postedLimited.forEach(t => {
            html += renderTweetItem(t, true);
        });
    }

    if (nextTweet) {
        html += '<h4 style="color:#1da1f2; font-size:0.9em; margin:20px 0 10px 0;">📍 次回投稿</h4>';
        html += renderTweetItem(nextTweet, false, true);
    }

    if (otherScheduled.length > 0) {
        html += '<h4 style="color:#666; font-size:0.9em; margin:20px 0 10px 0;">予約済み</h4>';
        otherScheduled.forEach(t => {
            html += renderTweetItem(t, false);
        });
    }

    if (truncated) {
        html += '<p style="color:#999; margin-top:10px; font-size:0.85em;">※ 最新20件のみ表示しています。残りは省略。</p>';
    }

    timeline.innerHTML = html || '<p style="color:#999;">まだ投稿がありません</p>';
}

// ツイートアイテムを描画（画像サムネイル付き）
function renderTweetItem(tweet, isPosted, isNext = false) {
    const urlParams = new URLSearchParams(window.location.search);
    const accountId = urlParams.get('id');
    
    // 画像サムネイル生成
    let imagesHtml = '';
    try {
        const imageNames = JSON.parse(tweet.image_names || '[]');
        if (imageNames.length > 0) {
            imagesHtml = '<div style="display:flex; gap:4px; margin-top:8px; flex-wrap:wrap;">';
            imageNames.slice(0, 4).forEach(img => {
                imagesHtml += `<img src="/uploads/${accountId}/${img}" style="width:50px; height:50px; object-fit:cover; border-radius:4px; border:1px solid #ddd;">`;
            });
            imagesHtml += '</div>';
        }
    } catch (e) {
        // JSON解析失敗時は無視
    }
    
    const date = new Date(tweet.scheduled_at || tweet.posted_at);
    const borderStyle = isNext ? 'border-left: 4px solid #1da1f2;' : '';
    
    return `
        <div class="timeline-item ${isPosted ? 'posted' : 'scheduled'}" style="${borderStyle}">
            <div class="status-badge">${isPosted ? '✓' : '⏰'}</div>
            <p>${tweet.content || '(画像のみ)'}</p>
            ${imagesHtml}
            <small>${date.toLocaleString('ja-JP', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })}</small>
        </div>
    `;
}

// 4. 予約フォームの送信処理
const tweetForm = document.getElementById('tweetForm');
if (tweetForm) {
    tweetForm.onsubmit = async (e) => {
        e.preventDefault();
        const urlParams = new URLSearchParams(window.location.search);
        const id = urlParams.get('id');

        const content = document.getElementById('content').value.trim();
        const scheduledAtValue = document.getElementById('scheduled_at').value;
        
        // テキストと画像の両方が空でないか確認
        if (!content && selectedImages.length === 0) {
            alert('テキストまたは画像を選択してください');
            return;
        }

        // 予約時刻が現在時刻より前でないかチェック
        const scheduledDate = new Date(scheduledAtValue);
        const now = new Date();
        if (scheduledDate <= now) {
            alert('予約時刻は現在時刻より後に設定してください');
            return;
        }

        // 画像ファイル名を取得（URLから抽出）
        const imageNames = selectedImages.map(img => {
            const parts = img.src.split('/');
            return parts[parts.length - 1]; // ファイル名のみを取得
        });

        const data = {
            content: content,
            image_names: imageNames,
            scheduled_at: scheduledAtValue
        };

        try {
            const res = await fetch(`/accounts/${id}/tweets`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });

            if (res.ok) {
                alert('✅ 予約しました！');
                selectedImages = [];  // リセット
                clearSelectedImage();
                document.getElementById('content').value = '';
                updateSelectedImagesPreview();
                location.reload(); // 再読み込みして一覧を更新
            } else {
                const error = await res.json();
                alert(`❌ エラーが発生しました:\n${error.detail || '不明なエラー'}`);
            }
        } catch (err) {
            alert(`❌ 通信エラーが発生しました:\n${err.message}`);
        }
    };
}

// ダッシュボード読み込み（index.htmlで実行）
loadAccounts();

// === 一括予約モード関連関数 ===

// 一括予約モードの切り替え
function toggleBulkMode() {
    const isBulkMode = document.getElementById('bulkModeToggle').checked;
    document.getElementById('tweetForm').style.display = isBulkMode ? 'none' : 'block';
    document.getElementById('bulkTweetForm').style.display = isBulkMode ? 'block' : 'none';
    
    // ヒントセクションも切り替え
    const normalHint = document.getElementById('normalModeHint');
    const bulkHint = document.getElementById('bulkModeHint');
    if (normalHint) normalHint.style.display = isBulkMode ? 'none' : 'block';
    if (bulkHint) bulkHint.style.display = isBulkMode ? 'block' : 'none';
    
    // モード切り替え時にプレビューをリセット
    if (isBulkMode) {
        updateBulkPreview();
    }
}

// メガ予約モードの切り替え（大量画像用）
function toggleMegaMode() {
    isMegaMode = document.getElementById('megaModeToggle')?.checked || false;
    clearSelectedImage();
    clearMegaSelectedImages();
    const normalSelectedLabel = document.getElementById('image-count');
    if (normalSelectedLabel) normalSelectedLabel.textContent = '選択中：0 / 4';
    updateMegaSelectionStatus();

    const megaPanel = document.getElementById('megaSchedulerPanel');
    if (megaPanel) megaPanel.style.display = isMegaMode ? 'block' : 'none';
}

// 一括予約のテキストプレビューを更新
function updateBulkTextPreview() {
    const textMode = document.getElementById('bulk_text_mode').value;
    const textInputGroup = document.getElementById('bulk_text_input_group');
    
    if (textMode === 'fixed') {
        // 固定テキスト：テキスト入力が必須
        textInputGroup.style.display = 'block';
        document.getElementById('bulk_text').placeholder = '全ツイート共通のテキストを入力';
        document.getElementById('bulk_text').required = true;
    } else if (textMode === 'number') {
        // 連番：テキスト入力は任意（プレフィックス）
        textInputGroup.style.display = 'block';
        document.getElementById('bulk_text').placeholder = 'テキストなしでも OK（例：「Day」と入力すると「Day (1/3)」のようになります）';
        document.getElementById('bulk_text').required = false;
    } else if (textMode === 'filename') {
        // ファイル名モード：テキスト入力は不要
        textInputGroup.style.display = 'none';
        document.getElementById('bulk_text').required = false;
    } else {
        textInputGroup.style.display = 'none';
        document.getElementById('bulk_text').required = false;
    }
    
    updateBulkPreview();
}

// 一括予約プレビューを更新
function updateBulkPreview() {
    if (selectedImages.length === 0) {
        document.getElementById('bulk_preview').innerHTML = '<p style="color: #999;">画像を選択してください</p>';
        document.getElementById('bulk_tweet_count').textContent = '0';
        return;
    }

    const startTime = document.getElementById('bulk_start_time').value;
    const interval = parseInt(document.getElementById('bulk_interval').value) || 0;
    const textMode = document.getElementById('bulk_text_mode').value;
    const textContent = document.getElementById('bulk_text').value;

    if (!startTime || !interval || !textMode) {
        document.getElementById('bulk_preview').innerHTML = '<p style="color: #999;">開始日時、間隔、テキスト設定を選択してください</p>';
        document.getElementById('bulk_tweet_count').textContent = '0';
        return;
    }

    const startDate = new Date(startTime);
    let html = '<div style="max-height: 300px; overflow-y: auto;">';

    selectedImages.forEach((img, index) => {
        const scheduleDate = new Date(startDate);
        scheduleDate.setHours(scheduleDate.getHours() + interval * index);

        let text = '';
        if (textMode === 'fixed') {
            text = textContent;
        } else if (textMode === 'number') {
            text = `${textContent ? textContent + ' ' : ''}(${index + 1}/${selectedImages.length})`;
        } else if (textMode === 'filename') {
            text = img.name.replace(/\.[^/.]+$/, ''); // 拡張子を除去
        }

        // 予約内容のサマリーを生成
        const timeStr = scheduleDate.toLocaleString('ja-JP', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit'
        });

        html += `
            <div style="padding: 10px; border-bottom: 1px solid #eee; background: ${index % 2 === 0 ? '#fff' : '#f9f9f9'};">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 5px;">
                    <small style="color: #1da1f2; font-weight: bold; font-size: 0.8em;">投稿 ${index + 1}/${selectedImages.length}</small>
                    <small style="color: #666; font-size: 0.75em;">${timeStr}</small>
                </div>
                <p style="margin: 3px 0; font-size: 0.85em; word-break: break-word; color: #333;">${text || '(テキストなし)'}</p>
                <small style="color: #999; font-size: 0.75em;">📷 ${img.name}</small>
            </div>
        `;
    });

    html += '</div>';
    document.getElementById('bulk_preview').innerHTML = html;
    document.getElementById('bulk_tweet_count').textContent = selectedImages.length;
}

// 一括予約フォーム送信
const bulkTweetForm = document.getElementById('bulkTweetForm');
if (bulkTweetForm) {
    bulkTweetForm.onsubmit = async (e) => {
        e.preventDefault();
        const urlParams = new URLSearchParams(window.location.search);
        const id = urlParams.get('id');

        if (selectedImages.length === 0) {
            alert('画像を選択してください');
            return;
        }

        const startTime = document.getElementById('bulk_start_time').value;
        const interval = parseInt(document.getElementById('bulk_interval').value);
        const textMode = document.getElementById('bulk_text_mode').value;
        const textContent = document.getElementById('bulk_text').value;

        if (!startTime || !interval || !textMode) {
            alert('すべての項目を入力してください');
            return;
        }

        // ツイート生成
        const tweets = [];
        const startDate = new Date(startTime);

        selectedImages.forEach((img, index) => {
            const scheduleDate = new Date(startDate);
            scheduleDate.setHours(scheduleDate.getHours() + interval * index);

            let text = '';
            if (textMode === 'fixed') {
                text = textContent;
            } else if (textMode === 'number') {
                text = `${textContent ? textContent + ' ' : ''}(${index + 1}/${selectedImages.length})`;
            } else if (textMode === 'filename') {
                text = img.name.replace(/\.[^/.]+$/, '');
            }

            // 日時をローカル時刻でフォーマット（YYYY-MM-DDTHH:mm）
            const year = scheduleDate.getFullYear();
            const month = String(scheduleDate.getMonth() + 1).padStart(2, '0');
            const day = String(scheduleDate.getDate()).padStart(2, '0');
            const hours = String(scheduleDate.getHours()).padStart(2, '0');
            const minutes = String(scheduleDate.getMinutes()).padStart(2, '0');
            const scheduledAtFormatted = `${year}-${month}-${day}T${hours}:${minutes}`;

            tweets.push({
                content: text,
                image_names: [img.name],
                scheduled_at: scheduledAtFormatted
            });
        });

        // バックエンドに送信
        try {
            const res = await fetch(`/accounts/${id}/bulk-tweets`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ tweets })
            });

            if (res.ok) {
                const result = await res.json();
                alert(`✅ ${tweets.length}件の投稿を予約しました！\n\nアカウント詳細ページで確認できます。`);
                selectedImages = [];
                clearSelectedImage();
                // フォームをリセット
                document.getElementById('bulk_start_time').value = '';
                document.getElementById('bulk_interval').value = '';
                document.getElementById('bulk_text_mode').value = '';
                document.getElementById('bulk_text').value = '';
                updateBulkPreview();
                location.reload();
            } else {
                const error = await res.json();
                alert(`❌ エラーが発生しました:\n${error.detail || '不明なエラー'}`);
            }
        } catch (err) {
            alert(`❌ 通信エラーが発生しました:\n${err.message}`);
        }
    };
}

// === メガ予約（大量画像を1枚ずつ順次送信） ===
const megaScheduleButton = document.getElementById('mega_schedule_btn');
if (megaScheduleButton) {
    megaScheduleButton.onclick = async () => {
        const urlParams = new URLSearchParams(window.location.search);
        const id = urlParams.get('id');

        if (megaSelectedImages.length === 0) {
            alert('画像を選択してください（最大150枚）');
            return;
        }

        const startTime = document.getElementById('mega_start_time')?.value;
        const interval = parseInt(document.getElementById('mega_interval')?.value || '0', 10);
        const text = document.getElementById('mega_text')?.value || '';

        if (!startTime || !interval) {
            alert('開始日時と間隔を入力してください');
            return;
        }

        const startDate = new Date(startTime);
        const total = megaSelectedImages.length;

        const progressText = document.getElementById('mega-progress-text');
        const progressBar = document.getElementById('mega-progress-bar');
        const statusArea = document.getElementById('mega-progress-status');

        if (progressText) progressText.textContent = '開始準備中...';
        if (progressBar) progressBar.style.width = '0%';
        if (statusArea) statusArea.textContent = '';

        let success = 0;
        let failed = 0;

        // 順次送信（await で1件ずつ）
        for (let i = 0; i < megaSelectedImages.length; i++) {
            const img = megaSelectedImages[i];
            const scheduleDate = new Date(startDate);
            scheduleDate.setHours(scheduleDate.getHours() + interval * i);

            const year = scheduleDate.getFullYear();
            const month = String(scheduleDate.getMonth() + 1).padStart(2, '0');
            const day = String(scheduleDate.getDate()).padStart(2, '0');
            const hours = String(scheduleDate.getHours()).padStart(2, '0');
            const minutes = String(scheduleDate.getMinutes()).padStart(2, '0');
            const scheduledAtFormatted = `${year}-${month}-${day}T${hours}:${minutes}`;

            const content = text ? `${text} (${i + 1}/${total})` : `(${i + 1}/${total})`;

            // 進捗表示
            if (progressText) progressText.textContent = `${i + 1} / ${total} アップロード中...`;
            if (progressBar) progressBar.style.width = `${Math.round(((i + 1) / total) * 100)}%`;

            try {
                const res = await fetch(`/accounts/${id}/bulk-schedule-single`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        content,
                        image_name: img.name,
                        scheduled_at: scheduledAtFormatted
                    })
                });

                if (res.ok) {
                    success += 1;
                } else {
                    failed += 1;
                }
            } catch (err) {
                failed += 1;
            }
        }

        if (progressText) progressText.textContent = `完了: 成功 ${success} / 失敗 ${failed}`;
        if (progressBar) progressBar.style.width = '100%';
        if (statusArea) statusArea.textContent = failed === 0 ? '✅ 全件予約しました' : `⚠️ 一部失敗しました（成功 ${success}, 失敗 ${failed}）`;

        if (success > 0) {
            alert(`✅ ${success}件を予約しました${failed ? `（失敗 ${failed}件）` : ''}`);
            clearMegaSelectedImages();
            location.reload();
        } else {
            alert('❌ 予約に失敗しました。入力内容を確認してください。');
        }
    };
}

// 画像選択時にプレビューを更新（一括モードの場合）
const originalUpdateSelectedImagesPreview = updateSelectedImagesPreview;
updateSelectedImagesPreview = function() {
    originalUpdateSelectedImagesPreview.call(this);
    if (document.getElementById('bulkModeToggle')?.checked) {
        updateBulkPreview();
    }
};

// 一括モード関連フィールドの変更を監視
document.addEventListener('change', (e) => {
    if (['bulk_start_time', 'bulk_interval', 'bulk_text_mode', 'bulk_text'].includes(e.target.id)) {
        updateBulkPreview();
    }
});

document.addEventListener('input', (e) => {
    if (e.target.id === 'bulk_text') {
        updateBulkPreview();
    }
});
