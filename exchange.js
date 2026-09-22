(()=>{
  const $=selector=>document.querySelector(selector);
  const root=$("#knowledgeExchange");
  if(!root)return;
  let api="",loaded=false,loading=false;
  const form=$("#exchangeForm"),status=$("#exchangeStatus"),list=$("#exchangeComments"),submit=$("#exchangeSubmit");
  const esc=value=>String(value??"").replace(/[&<>"']/g,char=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[char]));
  const formatDate=value=>{const date=new Date(value);return Number.isNaN(date.getTime())?"日時不明":new Intl.DateTimeFormat("ja-JP",{timeZone:"Asia/Tokyo",year:"numeric",month:"2-digit",day:"2-digit",hour:"2-digit",minute:"2-digit"}).format(date)};
  async function resolveApi(){
    if(api)return api;
    if(globalThis.chrome?.runtime?.id){const saved=await chrome.storage.local.get("formationsApiUrl");api=saved.formationsApiUrl||""}
    else{const config=await fetch(`./data/formations-config.json?t=${Date.now()}`,{cache:"no-store"}).then(response=>response.json());api=config.api_url||""}
    if(!api)throw Error("コメント機能は初期設定中です。");
    return api;
  }
  async function post(body){
    const endpoint=await resolveApi(),response=await fetch(endpoint,{method:"POST",headers:{"Content-Type":"text/plain;charset=utf-8"},body:JSON.stringify(body)}),text=await response.text();
    let result;try{result=JSON.parse(text)}catch(_error){throw Error("保存先から正しい応答が返されませんでした。Apps Scriptを最新版で再デプロイしてください。")}
    if(!result.ok)throw Error(result.error||"処理に失敗しました。");
    return result;
  }
  function render(comments){
    list.innerHTML=comments.length?comments.map(comment=>`<article class="exchangeComment"><div class="exchangeCommentHead"><b>${esc(comment.playerName)}</b><time datetime="${esc(comment.createdAt)}">${esc(formatDate(comment.createdAt))}</time></div><p>${esc(comment.body).replace(/\n/g,"<br>")}</p><button type="button" class="exchangeDelete" data-id="${esc(comment.id)}">管理者削除</button></article>`).join(""):"<p class=\"exchangeEmpty\">まだコメントはありません。</p>";
    list.querySelectorAll(".exchangeDelete").forEach(button=>button.onclick=()=>removeComment(button.dataset.id));
  }
  async function load(force=false){
    if(loading||loaded&&!force)return;loading=true;status.textContent="コメントを読み込んでいます…";
    try{const endpoint=await resolveApi(),result=await fetch(`${endpoint}?action=comments&t=${Date.now()}`,{cache:"no-store"}).then(response=>response.json());if(!result.ok)throw Error(result.error||"読込失敗");render(result.comments||[]);status.textContent=`${(result.comments||[]).length}件のコメント`;
    }catch(error){status.textContent=`読込エラー：${error.message}`;render([])}finally{loading=false;loaded=true}
  }
  async function removeComment(id){
    const guildPassword=prompt("Valhalla共通パスワードを入力してください。");if(guildPassword===null)return;
    const adminPassword=prompt("管理者専用パスワードを入力してください。");if(adminPassword===null)return;
    if(!confirm("このコメントを削除しますか？"))return;
    status.textContent="削除中…";
    try{await post({action:"commentDelete",commentId:id,guildPassword,adminPassword});loaded=false;await load(true)}catch(error){status.textContent=`削除エラー：${error.message}`}
  }
  form.addEventListener("submit",async event=>{
    event.preventDefault();const data=new FormData(form),playerName=String(data.get("playerName")||"").trim(),body=String(data.get("body")||"").trim(),guildPassword=String(data.get("guildPassword")||"");
    submit.disabled=true;status.textContent="投稿中…";
    try{await post({action:"commentCreate",playerName,body,guildPassword});localStorage.setItem("exchangePlayerName",playerName);form.elements.body.value="";loaded=false;await load(true)}catch(error){status.textContent=`投稿エラー：${error.message}`}finally{submit.disabled=false}
  });
  form.elements.playerName.value=localStorage.getItem("exchangePlayerName")||"";
  addEventListener("hashchange",()=>{if(location.hash==="#knowledgeExchange")load(true)});
  if(location.hash==="#knowledgeExchange")load();
})();
