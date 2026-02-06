let selected = null;
let roverCache = [];
let map;
let marker;

function initMap(){
  map = L.map('map').setView([60.1699, 24.9384], 13);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '&copy; OpenStreetMap'
  }).addTo(map);
  marker = L.marker([60.1699, 24.9384]).addTo(map).bindPopup('Rover position');
}

function openAddForm(){
  document.getElementById('add-form')?.scrollIntoView({behavior:'smooth', block:'start'});
}

function selectRover(id){
  selected = id;
  const active = roverCache.find(r => r.id === selected);
  if(active){
    updateStatus(active);
    updateMap(active);
  }
}

function renderSelect(){
  const select = document.getElementById('rover-select');
  if(!select) return;
  select.innerHTML = roverCache.map(r => `<option value="${r.id}">${r.id} (${r.ip_address || '-'})</option>`).join('');
  if(selected){
    select.value = selected;
  }
}

async function loadRovers(){
  const search = (document.getElementById('search')?.value || '').toLowerCase();
  roverCache = await (await fetch('/api/ui/rovers')).json();
  const root = document.getElementById('rovers');
  root.innerHTML='';

  roverCache
    .filter(r => r.id.toLowerCase().includes(search) || r.name.toLowerCase().includes(search) || (r.ip_address || '').toLowerCase().includes(search))
    .forEach(r=>{
      const el=document.createElement('div');
      const badge = r.online ? '<span class="rover-health ok">✔</span>' : '<span class="rover-health bad">✖</span>';
      el.innerHTML=`<span>${r.id}<br><small>${r.ip_address || '-'}</small></span>${badge}`;
      el.onclick=()=>{selected=r.id; renderSelect(); updateStatus(r); updateMap(r)};
      root.appendChild(el);
    });

  if(!selected && roverCache.length){
    selected = roverCache[0].id;
  }
  const active = roverCache.find(r => r.id === selected);
  renderSelect();
  if(active){
    updateStatus(active);
    updateMap(active);
  }
}

function updateStatus(r){
  document.getElementById('status').textContent=`mode_desired: ${r.mode_desired} / mode_reported: ${r.mode_reported}`;
  const c = document.getElementById('connectivity');
  if(r.online){
    c.innerHTML = 'Связь: <span class="ok">✔ онлайн</span>';
  } else {
    c.innerHTML = 'Связь: <span class="bad">✖ офлайн</span>';
  }
}

function updateMap(r){
  if(!map || !marker) return;
  const lat = r?.location?.lat;
  const lon = r?.location?.lon;
  if(typeof lat === 'number' && typeof lon === 'number'){
    marker.setLatLng([lat, lon]);
    map.setView([lat, lon], 16);
  }
}

async function sendCommand(payload){
  if(!selected) return;
  if(USER_ROLE==='viewer') return alert('viewer cannot control');
  await fetch(`/api/rovers/${selected}/command`,{
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body:JSON.stringify({...payload, seq_id:crypto.randomUUID(), timestamp:Date.now()})
  });
  setTimeout(loadRovers, 600);
}

async function sendMode(mode){
  document.getElementById('status').textContent=`MODE_REQUESTED_${mode} (pending)`;
  return sendCommand({mode});
}

async function move(direction){
  return sendCommand({mode:'MANUAL', action:'move', direction});
}

function sendStop(){
  return sendCommand({mode:'MANUAL', action:'stop'});
}

async function openLid(){
  return sendCommand({mode:'MANUAL', action:'open_lid', motor:'aux'});
}

async function addRover(){
  if(USER_ROLE!=='admin') return alert('Только admin может добавлять ровер');
  const id = document.getElementById('new-id').value.trim();
  const name = document.getElementById('new-name').value.trim() || id;
  const ip_address = document.getElementById('new-ip').value.trim();
  if(!id || !ip_address) return alert('Нужны ID и IP');

  const res = await fetch('/api/admin/rovers', {
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body:JSON.stringify({id, name, ip_address, api_token:'CHANGE_ME'})
  });
  if(!res.ok){
    return alert('Ошибка добавления ровера');
  }
  document.getElementById('new-id').value = '';
  document.getElementById('new-name').value = '';
  document.getElementById('new-ip').value = '';
  await loadRovers();
}

async function deleteRover(){
  if(USER_ROLE!=='admin') return alert('Только admin может удалять ровер');
  if(!selected) return;
  if(!confirm(`Удалить ровер ${selected}?`)) return;
  const res = await fetch(`/api/admin/rovers/${selected}`, {method:'DELETE'});
  if(!res.ok) return alert('Не удалось удалить ровер');
  selected = null;
  await loadRovers();
}

async function checkConnectivity(){
  if(!selected) return;
  const res = await fetch(`/api/rovers/${selected}/connectivity-check`, {method:'POST'});
  const data = await res.json();
  const c = document.getElementById('connectivity');
  c.innerHTML = data.online ? 'Связь: <span class="ok">✔ онлайн</span>' : 'Связь: <span class="bad">✖ офлайн</span>';
}

initMap();
setInterval(loadRovers,2000);
loadRovers();
