(()=>{
  if(location.protocol==="chrome-extension:")return;
  const SESSION_KEY="valhalla-ranking-auth-v1";
  const isPcHistoryMode=()=>window.matchMedia(
    "(min-width: 761px) and (hover: hover) and (pointer: fine)"
  ).matches;
  const restorePcView=()=>{
    if(!isPcHistoryMode())return;
    document.querySelectorAll("dialog[open]").forEach(dialog=>dialog.close());
    const gate=document.getElementById("siteAuthGate");
    document.body.style.overflow=gate&&!gate.hidden?"hidden":"";
  };
  window.addEventListener("pageshow",restorePcView);
  window.addEventListener("popstate",()=>requestAnimationFrame(restorePcView));
  const showGate=()=>{
    if(document.getElementById("siteAuthGate"))return;
    const gate=document.createElement("div");
    gate.id="siteAuthGate";
    gate.innerHTML='<form class="siteAuthBox" id="siteAuthForm"><h1>Valhallaランキング</h1><p>閲覧するには共通パスワードを入力してください。</p><label>Valhalla共通パスワード<input name="guildPassword" type="password" autocomplete="current-password" required autofocus></label><p class="siteAuthMessage" id="siteAuthMessage"></p><button type="submit">ランキングへ入る</button><p class="siteAuthNote">認証後は、このタブを閉じるまで入力を省略できます。</p></form>';
    document.body.appendChild(gate);
    document.body.style.overflow="hidden";
    document.getElementById("siteAuthForm").onsubmit=async e=>{
      e.preventDefault();
      const form=e.currentTarget,message=document.getElementById("siteAuthMessage"),password=new FormData(form).get("guildPassword");
      message.textContent="確認中…";
      try{
        const cfg=await fetch("./data/formations-config.json?t="+Date.now(),{cache:"no-store"}).then(r=>r.json());
        if(!cfg.api_url)throw Error("認証機能が設定されていません。");
        const result=await fetch(cfg.api_url,{method:"POST",headers:{"Content-Type":"text/plain;charset=utf-8"},body:JSON.stringify({action:"verifyAccess",guildPassword:password})}).then(r=>r.json());
        if(!result.ok||!result.authorized)throw Error(result.error||"パスワードが違います。");
        sessionStorage.setItem(SESSION_KEY,"1");
        gate.hidden=true;
        document.body.style.overflow="";
      }catch(error){message.textContent=error.message||"認証できませんでした。";form.guildPassword.select()}
    };
  };
  if(sessionStorage.getItem(SESSION_KEY)==="1")return;
  if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",showGate,{once:true});else showGate();
})();
