let selected = null;
async function loadRovers(){
  const data = await (await fetch('/api/ui/rovers')).json();
  const root = document.getElementById('rovers');
  root.innerHTML='';
  data.forEach(r=>{
    const el=document.createElement('div');
    el.textContent=`${r.id} | ${r.pdd_state}`;
    el.onclick=()=>{selected=r.id; updateStatus(r)};
    root.appendChild(el);
  });
  if(!selected && data.length){selected=data[0].id; updateStatus(data[0]);}
}
function updateStatus(r){
  document.getElementById('status').textContent=`mode_desired: ${r.mode_desired} / mode_reported: ${r.mode_reported}`;
}
async function sendMode(mode){
  if(USER_ROLE==='viewer') return alert('viewer cannot control');
  if(!selected) return;
  const seq_id=crypto.randomUUID();
  document.getElementById('status').textContent=`MODE_REQUESTED_${mode} (pending)`;
  await fetch(`/api/rovers/${selected}/command`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({mode,seq_id,timestamp:Date.now()})});
  setTimeout(loadRovers,1000);
}
function sendStop(){return sendMode('MANUAL');}
setInterval(loadRovers,2000);loadRovers();
