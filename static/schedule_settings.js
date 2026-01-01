// URLパラメータからアカウントIDを取得
const urlParams = new URLSearchParams(window.location.search);
const accountId = urlParams.get("account_id");

if (!accountId) {
  alert("アカウントIDが指定されていません");
  window.location.href = "/";
}

// 戻るリンクにアカウントIDを設定
document.getElementById(
  "backToAccount"
).href = `account_detail.html?account_id=${accountId}`;

// 選択された時間を保持する配列
let selectedHours = [];

// 初期化
document.addEventListener("DOMContentLoaded", () => {
  loadSchedules();
});

// 間隔に基づいて時間を生成
function generateHours() {
  const interval = parseInt(document.getElementById("intervalSelect").value);

  if (!interval) {
    document.getElementById("hoursGrid").innerHTML =
      '<p style="color:#999;">間隔を選択してください</p>';
    selectedHours = [];
    return;
  }

  const grid = document.getElementById("hoursGrid");
  grid.innerHTML = "";
  selectedHours = [];

  // 指定された間隔で時間を生成
  for (let hour = 0; hour < 24; hour += interval) {
    const hourStr = String(hour).padStart(2, "0") + ":00";

    const label = document.createElement("label");
    label.style.display = "flex";
    label.style.alignItems = "center";
    label.style.gap = "8px";
    label.style.padding = "8px";
    label.style.marginBottom = "4px";
    label.style.cursor = "pointer";

    const checkbox = document.createElement("input");
    checkbox.type = "checkbox";
    checkbox.value = hourStr;
    checkbox.style.cursor = "pointer";
    checkbox.style.width = "18px";
    checkbox.style.height = "18px";

    checkbox.addEventListener("change", function (e) {
      if (this.checked) {
        selectedHours.push(this.value);
      } else {
        selectedHours = selectedHours.filter((h) => h !== this.value);
      }
      selectedHours.sort();
    });

    const text = document.createElement("span");
    text.textContent = hourStr;
    text.style.fontSize = "1em";

    label.appendChild(checkbox);
    label.appendChild(text);
    grid.appendChild(label);
  }
}

// スケジュール設定を作成
async function createSchedule() {
  const name = document.getElementById("scheduleName").value.trim();
  const interval = document.getElementById("intervalSelect").value;

  if (!name) {
    alert("設定名を入力してください");
    return;
  }

  if (!interval) {
    alert("間隔を選択してください");
    return;
  }

  if (selectedHours.length === 0) {
    alert("少なくとも1つの時間を選択してください");
    return;
  }

  try {
    const response = await fetch(`/accounts/${accountId}/hourly-schedules`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        name: name,
        hours: selectedHours,
        is_active: true,
      }),
    });

    if (response.ok) {
      alert("スケジュール設定を作成しました");
      // フォームをリセット
      document.getElementById("scheduleName").value = "";
      document.getElementById("intervalSelect").value = "";
      selectedHours = [];
      document.getElementById("hoursGrid").innerHTML =
        '<p style="color:#999;">間隔を選択してください</p>';
      // 一覧を再読み込み
      loadSchedules();
    } else {
      const error = await response.json();
      alert(`エラー: ${error.detail}`);
    }
  } catch (error) {
    console.error("スケジュール作成エラー:", error);
    alert("スケジュールの作成に失敗しました");
  }
}

// スケジュール一覧を読み込み
async function loadSchedules() {
  try {
    const response = await fetch(`/accounts/${accountId}/hourly-schedules`);
    const schedules = await response.json();

    const list = document.getElementById("schedulesList");

    if (schedules.length === 0) {
      list.innerHTML =
        '<p class="empty-message">スケジュール設定がありません</p>';
      return;
    }

    list.innerHTML = schedules
      .map(
        (schedule) => `
            <div class="schedule-card ${schedule.is_active ? "" : "inactive"}">
                <div class="schedule-header">
                    <h3>${escapeHtml(schedule.name)}</h3>
                    <div class="schedule-actions">
                        <button onclick="toggleScheduleActive(${
                          schedule.id
                        }, ${!schedule.is_active})" 
                                class="btn-small ${
                                  schedule.is_active
                                    ? "btn-warning"
                                    : "btn-success"
                                }">
                            ${schedule.is_active ? "無効化" : "有効化"}
                        </button>
                        <button onclick="editSchedule(${
                          schedule.id
                        })" class="btn-small">編集</button>
                        <button onclick="deleteSchedule(${
                          schedule.id
                        })" class="btn-small btn-danger">削除</button>
                    </div>
                </div>
                <div class="schedule-hours">
                    ${schedule.hours
                      .map((h) => `<span class="hour-tag">${h}</span>`)
                      .join("")}
                </div>
                <div class="schedule-info">
                    <small>作成: ${new Date(schedule.created_at).toLocaleString(
                      "ja-JP"
                    )}</small>
                </div>
            </div>
        `
      )
      .join("");
  } catch (error) {
    console.error("スケジュール読み込みエラー:", error);
    alert("スケジュールの読み込みに失敗しました");
  }
}

// スケジュールの有効/無効を切り替え
async function toggleScheduleActive(scheduleId, isActive) {
  try {
    const response = await fetch(
      `/accounts/${accountId}/hourly-schedules/${scheduleId}`,
      {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ is_active: isActive }),
      }
    );

    if (response.ok) {
      loadSchedules();
    } else {
      alert("更新に失敗しました");
    }
  } catch (error) {
    console.error("更新エラー:", error);
    alert("更新に失敗しました");
  }
}

// スケジュールを編集（シンプルな実装）
async function editSchedule(scheduleId) {
  const newName = prompt("新しい設定名を入力してください:");
  if (!newName || !newName.trim()) {
    return;
  }

  try {
    const response = await fetch(
      `/accounts/${accountId}/hourly-schedules/${scheduleId}`,
      {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: newName.trim() }),
      }
    );

    if (response.ok) {
      alert("更新しました");
      loadSchedules();
    } else {
      alert("更新に失敗しました");
    }
  } catch (error) {
    console.error("更新エラー:", error);
    alert("更新に失敗しました");
  }
}

// スケジュールを削除
async function deleteSchedule(scheduleId) {
  if (!confirm("このスケジュール設定を削除しますか？")) {
    return;
  }

  try {
    const response = await fetch(
      `/accounts/${accountId}/hourly-schedules/${scheduleId}`,
      {
        method: "DELETE",
      }
    );

    if (response.ok) {
      alert("削除しました");
      loadSchedules();
    } else {
      alert("削除に失敗しました");
    }
  } catch (error) {
    console.error("削除エラー:", error);
    alert("削除に失敗しました");
  }
}

// HTMLエスケープ
function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}
