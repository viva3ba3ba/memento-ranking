const detailStyle=document.createElement("style");
detailStyle.textContent=`.char{font:inherit;color:inherit;text-align:left;cursor:pointer}.char:hover{outline:2px solid #4aa3ff}.charDetail{padding:16px}.detailGrid{display:grid;gap:12px}.detailCard{background:var(--p2);border:1px solid var(--line);border-radius:12px;padding:14px}.detailCard h3{margin:0 0 10px}.detailCard h3 small{color:var(--muted)}.detailCard p{line-height:1.65}.detailCard details{border-top:1px solid var(--line);padding:9px 0}.detailCard summary{cursor:pointer;color:#cfe7ff;font-weight:700}#charDialog{width:min(1000px,96vw);height:min(92vh,1000px);overflow-y:auto}`;
document.head.append(detailStyle);
const iconStyle=document.createElement("style");
iconStyle.textContent=`.detailCard h3{display:flex;align-items:center;gap:10px}.detailSkillIcon{width:52px;height:52px;border-radius:10px;border:1px solid var(--line);object-fit:cover}.weaponMark{width:52px;height:52px;border-radius:10px;display:grid;place-items:center;background:#5b491f;border:1px solid #ffd36b;font-size:28px}`;
document.head.append(iconStyle);
const weaponIconRule=document.createElement("style");
weaponIconRule.textContent=".weaponMark{display:none!important}";
document.head.append(weaponIconRule);
document.addEventListener("click",event=>{
  const button=event.target.closest("[data-char-id]");
  if(!button)return;
  event.stopPropagation();
  showCharacter(button.dataset.charId);
});
$("cclose").onclick=()=>{$("charDialog").close();document.body.style.overflow=""};
loadMaster();
