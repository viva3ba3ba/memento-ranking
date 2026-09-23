(() => {
  const form = document.getElementById("exchangeForm");
  if (!form) return;

  const comments = document.getElementById("exchangeComments");
  const status = document.getElementById("exchangeStatus");
  const submit = document.getElementById("exchangeSubmit");
  const reload = document.getElementById("exchangeReload");
  const PASSWORD_KEY = "valhalla-ranking-password";
  let api = "";
  let capabilityPromise = null;

  const escapeHtml = value => String(value ?? "").replace(/[&<>"']/g, char => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
  })[char]);

  const formatDate = value => {
    const date = new Date(value);
    return Number.isNaN(date.getTime()) ? "" : new Intl.DateTimeFormat("ja-JP", {
      year: "numeric", month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit",
      timeZone: "Asia/Tokyo"
    }).format(date);
  };

  async function resolveApi() {
    if (api) return api;
    if (typeof chrome !== "undefined" && chrome.runtime?.id) {
      api = (await chrome.storage.local.get("formationsApiUrl")).formationsApiUrl || "";
    } else {
      const config = await fetch(`./data/formations-config.json?t=${Date.now()}`, { cache: "no-store" }).then(response => response.json());
      api = config.api_url || "";
    }
    if (!api) throw Error("情報交換の保存先が設定されていません。");
    return api;
  }

  async function requireExchangeApi() {
    if (!capabilityPromise) capabilityPromise = (async () => {
      const endpoint = await resolveApi();
      const result = await fetch(`${endpoint}?action=health&t=${Date.now()}`, { cache: "no-store" }).then(response => response.json());
      if (!result.ok || result.exchangeComments !== true || result.anonymousExchange !== true) {
        throw Error("情報交換の保存先が旧版です。管理者が付属のgoogle-apps-script.gsへ更新し、新バージョンとして再デプロイしてください。");
      }
      return endpoint;
    })().catch(error => {
      capabilityPromise = null;
      throw error;
    });
    return capabilityPromise;
  }

  function render(items) {
    comments.innerHTML = items.length ? items.map(item => `
      <article class="exchangeComment">
        <div class="exchangeCommentHead"><span class="exchangeCommentName">${escapeHtml(item.name)}</span><time class="exchangeCommentTime">${escapeHtml(formatDate(item.createdAt))}</time></div>
        <p class="exchangeCommentBody">${escapeHtml(item.message)}</p>
      </article>`).join("") : '<p class="exchangeEmpty">まだコメントはありません。</p>';
  }

  async function load() {
    reload.disabled = true;
    status.textContent = "コメントを読み込んでいます…";
    try {
      const endpoint = await requireExchangeApi();
      const result = await fetch(`${endpoint}?action=exchangeList&t=${Date.now()}`, { cache: "no-store" }).then(response => response.json());
      if (!result.ok) throw Error(result.error || "コメントを読み込めませんでした。");
      render(Array.isArray(result.comments) ? result.comments : []);
      status.textContent = "";
    } catch (error) {
      comments.innerHTML = '<p class="exchangeEmpty">コメントを表示できません。</p>';
      status.textContent = error.message || "コメントを読み込めませんでした。";
    } finally {
      reload.disabled = false;
    }
  }

  form.addEventListener("submit", async event => {
    event.preventDefault();
    const data = new FormData(form);
    const body = {
      action: "exchangePost",
      name: String(data.get("name") || "").trim(),
      message: String(data.get("message") || "").trim(),
      guildPassword: sessionStorage.getItem(PASSWORD_KEY) || ""
    };
    submit.disabled = true;
    status.textContent = "投稿中…";
    try {
      if (!body.guildPassword && location.protocol !== "chrome-extension:") {
        throw Error("ログイン情報を更新するため、アプリを一度閉じてから開き直してください。");
      }
      const endpoint = await requireExchangeApi();
      const result = await fetch(endpoint, {
        method: "POST",
        headers: { "Content-Type": "text/plain;charset=utf-8" },
        body: JSON.stringify(body)
      }).then(response => response.json());
      if (!result.ok) throw Error(result.error || "投稿できませんでした。");
      document.getElementById("exchangeMessage").value = "";
      status.textContent = "投稿しました。";
      await load();
    } catch (error) {
      status.textContent = error.message || "投稿できませんでした。";
    } finally {
      submit.disabled = false;
    }
  });

  reload.addEventListener("click", load);
  load();
})();
