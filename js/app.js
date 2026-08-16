
const S={data:null,date:new Date(),lesson:null};
const $=s=>document.querySelector(s);
const AC={violet:'#7c5cff',cyan:'#29c4b6',lime:'#7dbd54',orange:'#ff8d6c',rose:'#eb6f93',blue:'#6a97ff'};
function ymd(d){return`${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`}
function fd(d){return new Intl.DateTimeFormat('en-US',{weekday:'long',month:'long',day:'numeric'}).format(d).replace(',','')}
function minlabel(n){n=Number(n||0);return n>=60?`${Math.floor(n/60)}h ${String(n%60).padStart(2,'0')}m`:`${n}m`}
function svc(url=''){let h='';try{h=new URL(url).hostname.toLowerCase()}catch{};for(const [r,c,n] of [[/youtube|youtu\.be/,'YT','YouTube'],[/quizlet/,'QZ','Quizlet'],[/baamboozle/,'BZ','Baamboozle'],[/github/,'GH','GitHub'],[/docs\.google|drive\.google/,'GD','Google Docs'],[/forms\.google/,'GF','Google Forms'],[/meet\.google/,'GM','Google Meet'],[/zoom/,'ZM','Zoom'],[/yandex|ya\.ru/,'YA','Yandex']])if(r.test(h))return{c,n};return{c:'↗',n:'Open link'}}
function illus(l){const t=(l.topic||'').toLowerCase();if(t.includes('routine'))return'assets/illus/routine.svg';if(t.includes('character')||t.includes('personality'))return'assets/illus/personality.svg';if(t.includes('camp'))return'assets/illus/camping.svg';if(t.includes('travel'))return'assets/illus/travel.svg';if(t.includes('animal')||t.includes('literature')||t.includes('read'))return'assets/illus/book.svg';return'assets/illus/game.svg'}
function day(){return(S.data?.lessons||[]).filter(l=>l.date===ymd(S.date)).sort((a,b)=>String(a.time).localeCompare(String(b.time)))}
function tm(t){const m=String(t||'0:0').match(/(\d{1,2}):(\d{2})/);if(!m)return 0;return Number(m[1])*60+Number(m[2])}
function stat(l,ls){if(ymd(new Date())!==l.date)return{key:'scheduled',label:'Scheduled'};const n=new Date(),cur=n.getHours()*60+n.getMinutes(),s=tm(l.time),e=s+Number(l.duration||0);if(cur>=e)return{key:'completed',label:'Done'};if(cur>=s&&cur<e)return{key:'now',label:'Now'};const f=ls.filter(x=>tm(x.time)>cur);if(f[0]?.id===l.id)return{key:'next',label:'Next'};return{key:'scheduled',label:'Scheduled'}}
function dk(id,o){return`lf.final.${id}.${o}`}
function isDone(id,o){return localStorage.getItem(dk(id,o))==='1'}
function mc(a){return(a.images?.length||0)+(a.audio?.src?1:0)+(a.url?1:0)}
function render(){const ls=day();$('#dateLabel').textContent=fd(S.date);$('#lessonCount').textContent=ls.length;$('#totalTime').textContent=minlabel(ls.reduce((s,l)=>s+Number(l.duration||0),0));$('#materialCount').textContent=ls.reduce((s,l)=>s+(l.activities||[]).reduce((z,a)=>z+mc(a),0),0);$('#flowTitle').textContent=`${ls.length} lesson${ls.length===1?'':'s'} for ${fd(S.date)}`;const now=new Date(),cur=now.getHours()*60+now.getMinutes();const nx=ymd(now)===ymd(S.date)?ls.find(l=>tm(l.time)>cur):ls[0];$('#nextLesson').textContent=nx?`${nx.time} · ${nx.student}`:'—';const g=$('#lessonGrid');g.innerHTML='';ls.forEach((l,idx)=>{const st=stat(l,ls),ac=AC[l.accent]||AC.violet,materials=(l.activities||[]).reduce((s,a)=>s+mc(a),0);const route=(l.activities||[]).slice(0,4).map(a=>{const v=svc(a.url),n=(a.images?.length||0)+(a.audio?.src?1:0);return`<div class="rrow"><span class="rlogo">${a.url?v.c:(a.audio?.src?'AU':'IMG')}</span><span class="rname">${a.title}</span><span class="rmeta">${a.minutes?`${a.minutes}m`:''}${n?` <i class="mat">+${n}</i>`:''}</span></div>`}).join('');const c=document.createElement('article');c.className=`lesson-card ${st.key==='now'?'current':''} ${st.key==='completed'?'completed':''}`;c.style.setProperty('--ac',ac);c.innerHTML=`<div class="cover"><img src="${illus(l)}" alt=""><span class="material-pill">${materials} material${materials===1?'':'s'}</span></div><div class="card-body"><div class="topline"><span class="time">${l.time}</span><span class="badge ${st.key}">${st.label}</span></div><div class="person">${l.student}</div><h3>${l.topic}</h3><div class="focus">${l.focus||''}</div><div class="tags"><span class="tag">${l.level||'—'}</span><span class="tag">${l.duration||0} MIN</span><span class="tag">STAGES ${(l.activities||[]).length}</span></div><div class="route">${route}${(l.activities||[]).length>4?`<div class="more">+ ${(l.activities||[]).length-4} more stage</div>`:''}</div><button class="open" data-id="${l.id}">Open lesson</button></div>`;g.appendChild(c)});for(let i=ls.length;i<6;i++){const e=document.createElement('article');e.className='lesson-card empty';e.innerHTML='<div><b>Free slot</b><span>No lesson scheduled</span></div>';g.appendChild(e)}document.querySelectorAll('.open').forEach(b=>b.onclick=()=>openLesson(b.dataset.id))}
function openLesson(id){const l=(S.data?.lessons||[]).find(x=>x.id===id);if(!l)return;S.lesson=l;$('#lessonContent').innerHTML=`<section class="lesson-head"><div class="meta"><span>${l.time}</span><span>•</span><span>${l.student}</span><span>•</span><span>${l.level}</span><span>•</span><span>${l.duration} min</span></div><h2>${l.topic}</h2><p>${l.focus||''}</p></section><section class="activity-list">${(l.activities||[]).map(a=>{const v=svc(a.url),imgs=a.images||[],has=imgs.length||a.audio?.src;return`<article class="activity"><div class="activity-main"><div class="num">${String(a.order).padStart(2,'0')}</div><div class="activity-title"><b>${a.title}</b><span>${a.minutes?`${a.minutes} min · `:''}${a.note||''}</span></div><div class="actions">${a.url?`<a class="link" href="${a.url}" target="_blank" rel="noopener">${v.n}</a>`:''}<button class="done ${isDone(l.id,a.order)?'done':''}" data-order="${a.order}">${isDone(l.id,a.order)?'Done ✓':'Mark done'}</button></div></div>${has?`<div class="materials">${imgs.length?`<div class="gallery ${imgs.length===1?'one':''}">${imgs.map((s,i)=>`<button class="thumb" data-img="${s}"><img src="${s}" alt="${a.title} material ${i+1}"></button>`).join('')}</div>`:'<div></div>'}${a.audio?.src?`<div class="audio"><strong>${a.audio.label||'AUDIO'}</strong><audio controls preload="metadata" src="${a.audio.src}"></audio></div>`:''}</div>`:''}</article>`}).join('')}</section>`;$('#lessonModal').classList.remove('hidden');up();document.querySelectorAll('.done').forEach(b=>b.onclick=()=>{const k=dk(l.id,b.dataset.order),v=localStorage.getItem(k)!=='1';localStorage.setItem(k,v?'1':'0');b.classList.toggle('done',v);b.textContent=v?'Done ✓':'Mark done';up()});document.querySelectorAll('.thumb').forEach(b=>b.onclick=()=>{$('#fullImage').src=b.dataset.img;$('#imageModal').classList.remove('hidden')})}
function up(){const a=S.lesson?.activities||[],d=a.filter(x=>isDone(S.lesson.id,x.order)).length;$('#progressText').textContent=`${d} / ${a.length} complete`;$('#progressBar').style.width=`${a.length?d/a.length*100:0}%`}
function repoInfo(){
  const host=location.hostname;
  if(!host.endsWith('.github.io')) return null;
  const owner=host.split('.')[0];
  const repo=location.pathname.split('/').filter(Boolean)[0]||'';
  return owner&&repo?{owner,repo}:null;
}
function absoluteAsset(path,rawBase){
  if(!path||/^https?:\/\//i.test(path)||!rawBase) return path;
  return rawBase+String(path).replace(/^\.\//,'');
}
function normaliseRemoteAssets(data,rawBase){
  if(!rawBase) return data;
  for(const lesson of data.lessons||[]){
    for(const activity of lesson.activities||[]){
      activity.images=(activity.images||[]).map(x=>absoluteAsset(x,rawBase));
      if(activity.audio?.src) activity.audio.src=absoluteAsset(activity.audio.src,rawBase);
    }
  }
  return data;
}
async function fetchData(preferRaw=false){
  const repo=repoInfo();
  if(preferRaw&&repo){
    const rawBase=`https://raw.githubusercontent.com/${repo.owner}/${repo.repo}/main/`;
    try{
      const r=await fetch(`${rawBase}data/lessons.json?ts=${Date.now()}`,{cache:'no-store',headers:{'Cache-Control':'no-cache'}});
      if(r.ok) return normaliseRemoteAssets(await r.json(),rawBase);
    }catch(e){console.warn('Raw GitHub refresh failed; falling back to Pages.',e)}
  }
  const r=await fetch(`data/lessons.json?v=${Date.now()}`,{cache:'no-store',headers:{'Cache-Control':'no-cache'}});
  if(!r.ok) throw Error('Could not load lesson data');
  return await r.json();
}
function applyData(data){
  S.data=data;
  const u=S.data.updatedAt?new Date(S.data.updatedAt):null;
  $('#syncStamp').textContent=u&&!isNaN(u)?`updated ${u.toLocaleString()}`:'data loaded';
  $('#sourceMode').textContent=S.data.sourceMode==='private-api'?'Private Yandex API':S.data.sourceMode==='public-link'?'Yandex public sync':'Demo mode';
  render();
}
async function load(){
  try{applyData(await fetchData(true))}
  catch(e){console.error(e);$('#lessonGrid').innerHTML='<article class="lesson-card empty"><div><b>Data unavailable</b><span>Check GitHub Actions sync</span></div></article>'}
}
$('#prevDay').onclick=()=>{S.date.setDate(S.date.getDate()-1);render()};
$('#nextDay').onclick=()=>{S.date.setDate(S.date.getDate()+1);render()};
$('#todayBtn').onclick=()=>{S.date=new Date();render()};


$('#themeBtn').onclick=()=>{document.body.classList.toggle('dark');localStorage.setItem('lf.dark',document.body.classList.contains('dark')?'1':'0')};
if(localStorage.getItem('lf.dark')==='1')document.body.classList.add('dark');
$('#closeLesson').onclick=()=>$('#lessonModal').classList.add('hidden');$('#lessonModal').onclick=e=>{if(e.target.id==='lessonModal')$('#lessonModal').classList.add('hidden')};$('#closeImage').onclick=()=>$('#imageModal').classList.add('hidden');$('#imageModal').onclick=e=>{if(e.target.id==='imageModal')$('#imageModal').classList.add('hidden')};$('#helpBtn').onclick=()=>$('#helpModal').classList.remove('hidden');$('#closeHelp').onclick=()=>$('#helpModal').classList.add('hidden');$('#helpModal').onclick=e=>{if(e.target.id==='helpModal')$('#helpModal').classList.add('hidden')};
const h=new Date().getHours();$('#greeting').textContent=h<12?'GOOD MORNING':h<18?'GOOD AFTERNOON':'GOOD EVENING';
load();
setInterval(load, 10*60*1000);
