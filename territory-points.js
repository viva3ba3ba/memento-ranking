(()=>{
  "use strict";
  const page=document.getElementById("territoryPoints");
  if(!page)return;
  const status=document.getElementById("territoryStatus"),summary=document.getElementById("territorySummary"),rows=document.getElementById("territoryRows");
  let history=null,world="all",period="daily",loaded=false;
  const esc=value=>String(value??"").replace(/[&<>"']/g,ch=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[ch]));
  function jstKey(value=Date.now()){
    const parts=new Intl.DateTimeFormat("en-CA",{timeZone:"Asia/Tokyo",year:"numeric",month:"2-digit",day:"2-digit"}).formatToParts(new Date(value));
    const get=type=>parts.find(part=>part.type===type).value;
    return `${get("year")}-${get("month")}-${get("day")}`;
  }
  function addDays(key,amount){const [y,m,d]=key.split("-").map(Number),date=new Date(Date.UTC(y,m-1,d+amount));return date.toISOString().slice(0,10)}
  function range(){
    const end=jstKey(),[y,m,d]=end.split("-").map(Number);
    if(period==="daily")return {start:end,end,label:`${end} 当日`};
    if(period==="weekly"){const date=new Date(Date.UTC(y,m-1,d)),offset=(date.getUTCDay()+6)%7,start=addDays(end,-offset);return {start,end,label:`${start}～${end} 週間`};}
    if(period==="monthly"){const start=`${y}-${String(m).padStart(2,"0")}-01`;return {start,end,label:`${y}年${m}月`};}
    const firstThis=new Date(Date.UTC(y,m-1,1)),lastPrev=new Date(firstThis.getTime()-86400000),py=lastPrev.getUTCFullYear(),pm=lastPrev.getUTCMonth()+1,pd=lastPrev.getUTCDate();
    return {start:`${py}-${String(pm).padStart(2,"0")}-01`,end:`${py}-${String(pm).padStart(2,"0")}-${String(pd).padStart(2,"0")}`,label:`${py}年${pm}月（前月）`};
  }
  function aggregate(){
    const span=range(),wanted=world==="all"?[177,178,179,180]:[Number(world)],totals=new Map(),dates=new Set();
    for(const [date,worlds] of Object.entries(history?.days||{})){
      if(date<span.start||date>span.end)continue;
      for(const number of wanted){const record=worlds?.[String(number)];if(!record)continue;dates.add(date);for(const item of record.rows||[]){const out=totals.get(item.guild)||{guild:item.guild,church:0,castle:0,temple:0,total:0};for(const key of ["church","castle","temple","total"])out[key]+=Number(item[key]||0);totals.set(item.guild,out)}}
    }
    return {span,days:dates.size,rows:[...totals.values()].sort((a,b)=>b.total-a.total||a.guild.localeCompare(b.guild,"ja"))};
  }
  function render(){
    if(!history)return;
    const data=aggregate(),worldLabel=world==="all"?"4鯖統合":`W${world}`;
    status.classList.remove("is-error");status.textContent=data.rows.length?`${worldLabel}・${data.span.label}`:`${worldLabel}・${data.span.label}のデータはありません。`;
    summary.hidden=false;summary.innerHTML=`<span>集計日数：${data.days}日</span><span>最終更新：${esc(history.updated_at?new Date(history.updated_at).toLocaleString("ja-JP"):"-")}</span>`;
    rows.innerHTML=data.rows.map((item,index)=>`<tr><td>${index+1}</td><td>${esc(item.guild)}</td><td>${item.church}</td><td>${item.castle}</td><td>${item.temple}</td><td>${item.total}</td></tr>`).join("");
  }
  async function load(){
    if(loaded)return;loaded=true;
    try{const response=await fetch(`./data/territory-points.json?t=${Date.now()}`,{cache:"no-store"});if(!response.ok)throw new Error(`HTTP ${response.status}`);history=await response.json();render();}
    catch(error){status.classList.add("is-error");status.textContent=`ポイントデータを読み込めません。マクロで「ポイント取得・更新」を実行してください。（${error.message}）`;}
  }
  page.querySelectorAll("[data-territory-world]").forEach(button=>button.addEventListener("click",()=>{world=button.dataset.territoryWorld;page.querySelectorAll("[data-territory-world]").forEach(item=>item.classList.toggle("is-selected",item===button));render()}));
  page.querySelectorAll("[data-territory-period]").forEach(button=>button.addEventListener("click",()=>{period=button.dataset.territoryPeriod;page.querySelectorAll("[data-territory-period]").forEach(item=>item.classList.toggle("is-selected",item===button));render()}));
  window.addEventListener("hashchange",()=>{if(location.hash==="#territoryPoints")load()});
  if(location.hash==="#territoryPoints")load();
})();
