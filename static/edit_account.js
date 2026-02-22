// パスワード表示/非表示のトグル
function togglePasswordVisibility(inputId, toggleButton) {
  const input = document.getElementById(inputId);
  const isPassword = input.type === "password";

  input.type = isPassword ? "text" : "password";
  toggleButton.textContent = isPassword ? "🙉" : "🙈";
}

// URLからアカウントIDを取得
const urlParams = new URLSearchParams(window.location.search);
const accountId = urlParams.get("id");

// ページ読み込み時にアカウント情報を取得
async function loadAccountData() {
  if (!accountId) {
    showToast("アカウントIDが指定されていません", "error");
    location.href = "index.html";
    return;
  }

  const res = await fetch(`/accounts/${accountId}`);
  if (!res.ok) {
    showToast("アカウント情報の取得に失敗しました", "error");
    location.href = "index.html";
    return;
  }

  const account = await res.json();

  // アカウント名をフォームに設定
  document.getElementById("name").value = account.name;

  // APIキーはマスク表示されているので、プレースホルダーのまま
}

// アカウント更新処理
const editForm = document.getElementById("editForm");
if (editForm) {
  editForm.onsubmit = async (e) => {
    e.preventDefault();

    const data = {
      name: document.getElementById("name").value.trim(),
    };

    // APIキーフィールドが空でない場合のみ追加
    const apiKey = document.getElementById("api_key").value.trim();
    const apiSecret = document.getElementById("api_secret").value.trim();
    const accessToken = document.getElementById("access_token").value.trim();
    const accessTokenSecret = document
      .getElementById("access_token_secret")
      .value.trim();

    if (apiKey) data.api_key = apiKey;
    if (apiSecret) data.api_secret = apiSecret;
    if (accessToken) data.access_token = accessToken;
    if (accessTokenSecret) data.access_token_secret = accessTokenSecret;

    const res = await fetch(`/accounts/${accountId}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });

    if (res.ok) {
      showToast("アカウント情報を更新しました！", "success");
      location.href = "index.html";
    } else {
      const error = await res.json();
      showToast(`更新に失敗しました: ${error.detail || "不明なエラー"}`, "error");
    }
  };
}

// アカウント削除
const deleteAccountBtn = document.getElementById("deleteAccountBtn");
if (deleteAccountBtn) {
  deleteAccountBtn.onclick = async () => {
    if (
      !confirm(
        "このアカウントを削除しますか？\n紐づくツイート・スケジュール・CSVテキストもすべて削除されます。"
      )
    )
      return;

    const res = await fetch(`/accounts/${accountId}`, { method: "DELETE" });
    if (res.ok) {
      showToast("アカウントを削除しました", "success");
      location.href = "index.html";
    } else {
      const err = await res.json();
      showToast(`削除に失敗しました: ${err.detail || "不明なエラー"}`, "error");
    }
  };
}

// ページ読み込み時に実行
loadAccountData();
