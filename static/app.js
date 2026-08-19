const $ = (s) => document.querySelector(s);
const $$ = (s) => [...document.querySelectorAll(s)];
let selection = null;

function toast(message){
  const el = $('#toast');
  if(!el){ alert(message); return; }
  el.textContent = message; el.classList.add('show');
  clearTimeout(window.__toastTimer); window.__toastTimer = setTimeout(()=>el.classList.remove('show'), 2600);
}

$('#mobileMenu')?.addEventListener('click', ()=>$('#navLinks')?.classList.toggle('open'));

function setSelected(btn){
  $$('.pick-btn').forEach(b=>b.classList.remove('selected'));
  btn.classList.add('selected');
  selection={match_id:Number(btn.dataset.match),pick:btn.dataset.pick,label:btn.dataset.label,matchlabel:btn.dataset.matchlabel};
  $('#emptySlip')?.classList.add('hidden'); $('#slipContent')?.classList.remove('hidden');
  if($('#slipMatch')) $('#slipMatch').textContent=selection.matchlabel;
  if($('#slipPick')) $('#slipPick').textContent=selection.label;
}
function clearSlip(){selection=null;$$('.pick-btn').forEach(b=>b.classList.remove('selected'));$('#emptySlip')?.classList.remove('hidden');$('#slipContent')?.classList.add('hidden')}
$$('.pick-btn').forEach(btn=>btn.addEventListener('click',()=>setSelected(btn)));
$('#clearSlip')?.addEventListener('click',clearSlip);
$('#confirmPrediction')?.addEventListener('click',async()=>{
  if(!selection) return;
  const res=await fetch('/make-prediction',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({match_id:selection.match_id,pick:selection.pick})});
  const data=await res.json();
  if(res.status===401){location.href='/login';return}
  if(!res.ok){toast(data.message||'Não foi possível registrar.');return}
  toast(data.message);clearSlip();
});
$('#settleDemo')?.addEventListener('click',async()=>{
  const res=await fetch('/api/settle-demo',{method:'POST'});const data=await res.json();
  if(res.status===401){location.href='/login';return} if(!res.ok){toast(data.message||'Nada para simular.');return}
  toast(data.result==='won'?'Acertou! +100 pontos.':'Resultado simulado: palpite incorreto. Nenhum ponto perdido.');setTimeout(()=>location.reload(),900);
});

async function saveArcade(game,score){
  const res=await fetch('/api/arcade-score',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({game,score})});
  const data=await res.json();
  if(res.status===401){toast('Entre na conta para salvar a pontuação.');setTimeout(()=>location.href='/login',900);return}
  if(!res.ok){toast(data.message||'Não foi possível salvar.');return}
  if($('#headerScore')) $('#headerScore').textContent=data.total;
  toast(`Rodada salva: +${data.bonus} pontos no ranking.`);
}

function openGame(slug){
  $('#stagePlaceholder')?.classList.add('hidden');$$('.stage-game').forEach(g=>g.classList.add('hidden'));$('#stage-'+slug)?.classList.remove('hidden');
  $('#gameStage')?.scrollIntoView({behavior:'smooth',block:'center'});
}
$$('[data-open-game]').forEach(btn=>btn.addEventListener('click',()=>openGame(btn.dataset.openGame)));

let tigerRunning=false,tigerHits=0,tigerInterval=null;
function moveTiger(){const t=$('#tigerTarget'),z=$('#tigerZone');if(!t||!z)return;const maxX=Math.max(0,z.clientWidth-58),maxY=Math.max(0,z.clientHeight-58);t.style.left=Math.floor(Math.random()*maxX)+'px';t.style.top=Math.floor(Math.random()*maxY)+'px'}
$('#tigerTarget')?.addEventListener('click',()=>{if(tigerRunning){tigerHits++;if($('#tigerHits'))$('#tigerHits').textContent=tigerHits+' acertos';moveTiger()}});
function startTiger(){if(tigerRunning)return;tigerRunning=true;tigerHits=0;let left=10;if($('#tigerHits'))$('#tigerHits').textContent='0 acertos';moveTiger();$('#tigerTimer').textContent='10s';tigerInterval=setInterval(()=>{left--;$('#tigerTimer').textContent=left+'s';if(left<=0){clearInterval(tigerInterval);tigerRunning=false;saveArcade('Tiger Dash',Math.min(tigerHits,50))}},1000)}

let snakeSequence=[],snakeInput=[],snakeLevel=0,snakeBusy=false;const snakeButtons=$$('#snakeBoard button');
function flashCell(i){const b=snakeButtons[i];b?.classList.add('flash');setTimeout(()=>b?.classList.remove('flash'),330)}
async function showSnakeSequence(){snakeBusy=true;for(const i of snakeSequence){flashCell(i);await new Promise(r=>setTimeout(r,500))}snakeBusy=false;snakeInput=[]}
function startSnake(){snakeLevel=1;snakeSequence=[Math.floor(Math.random()*4)];$('#snakeLevel').textContent='Nível 1';showSnakeSequence()}
snakeButtons.forEach((b,i)=>b.addEventListener('click',async()=>{if(snakeBusy||snakeLevel===0)return;flashCell(i);snakeInput.push(i);const pos=snakeInput.length-1;if(snakeInput[pos]!==snakeSequence[pos]){const score=(snakeLevel-1)*10;snakeLevel=0;$('#snakeLevel').textContent='Fim';saveArcade('Snake Trail',Math.min(score,100));return}if(snakeInput.length===snakeSequence.length){if(snakeLevel>=10){saveArcade('Snake Trail',100);snakeLevel=0;$('#snakeLevel').textContent='Concluído';return}snakeLevel++;snakeSequence.push(Math.floor(Math.random()*4));$('#snakeLevel').textContent='Nível '+snakeLevel;await new Promise(r=>setTimeout(r,450));showSnakeSequence()}}));

const dragonSymbols=['🐉','🪭','🧧','🏮','🐼','🎋'];let dragonOpen=[],dragonPairs=0,dragonLocked=false;
function buildDragon(){const board=$('#dragonBoard');if(!board)return;dragonPairs=0;dragonOpen=[];dragonLocked=false;$('#dragonScore').textContent='0 pares';const cards=[...dragonSymbols,...dragonSymbols].sort(()=>Math.random()-.5);board.innerHTML='';cards.forEach((s,idx)=>{const b=document.createElement('button');b.className='memory-card';b.dataset.symbol=s;b.dataset.idx=idx;b.textContent='✦';b.onclick=()=>openDragon(b);board.appendChild(b)})}
function openDragon(b){if(dragonLocked||b.classList.contains('matched')||b.classList.contains('open'))return;b.classList.add('open');b.textContent=b.dataset.symbol;dragonOpen.push(b);if(dragonOpen.length===2){dragonLocked=true;const[a,c]=dragonOpen;if(a.dataset.symbol===c.dataset.symbol){a.classList.add('matched');c.classList.add('matched');dragonPairs++;dragonOpen=[];dragonLocked=false;$('#dragonScore').textContent=dragonPairs+' pares';if(dragonPairs===6)saveArcade('Dragon Match',24)}else setTimeout(()=>{a.classList.remove('open');c.classList.remove('open');a.textContent='✦';c.textContent='✦';dragonOpen=[];dragonLocked=false},600)}}

let lanternTargets=new Set(),lanternActive=false,lanternFound=0;
function buildLantern(){const board=$('#lanternBoard');if(!board)return;board.innerHTML='';lanternTargets=new Set();lanternFound=0;lanternActive=false;$('#lanternScore').textContent='0/8';while(lanternTargets.size<8)lanternTargets.add(Math.floor(Math.random()*16));for(let i=0;i<16;i++){const b=document.createElement('button');b.dataset.i=i;b.onclick=()=>chooseLantern(b,i);board.appendChild(b)}[...board.children].forEach((b,i)=>{if(lanternTargets.has(i)){b.classList.add('preview');b.textContent='🏮'}});setTimeout(()=>{[...board.children].forEach(b=>{b.classList.remove('preview');b.textContent=''});lanternActive=true},1400)}
function chooseLantern(b,i){if(!lanternActive||b.classList.contains('done'))return;b.classList.add('done');if(lanternTargets.has(i)){b.textContent='🏮';b.classList.add('correct');lanternFound++;$('#lanternScore').textContent=lanternFound+'/8';if(lanternFound===8){lanternActive=false;saveArcade('Lantern Memory',16)}}else{b.textContent='×';b.classList.add('wrong');lanternActive=false;saveArcade('Lantern Memory',lanternFound*2)}}

let pandaRunning=false,pandaScore=0,pandaLeft=15,pandaTicker=null,pandaFlip=null,pandaIsTarget=false;
function randomPandaSignal(){pandaIsTarget=Math.random()>.42;const el=$('#pandaSignal');if(!el)return;el.textContent=pandaIsTarget?'🐼':'🎋';el.classList.toggle('ready',pandaIsTarget);el.classList.toggle('danger',!pandaIsTarget)}
$('#pandaSignal')?.addEventListener('click',()=>{if(!pandaRunning)return;if(pandaIsTarget){pandaScore=Math.min(30,pandaScore+2);$('#pandaScore').textContent=pandaScore+' pts';randomPandaSignal()}else{pandaScore=Math.max(0,pandaScore-1);$('#pandaScore').textContent=pandaScore+' pts'}});
function startPanda(){if(pandaRunning)return;pandaRunning=true;pandaScore=0;pandaLeft=15;$('#pandaScore').textContent='0 pts';$('#pandaTimer').textContent='15s';randomPandaSignal();pandaFlip=setInterval(randomPandaSignal,700);pandaTicker=setInterval(()=>{pandaLeft--;$('#pandaTimer').textContent=pandaLeft+'s';if(pandaLeft<=0){clearInterval(pandaTicker);clearInterval(pandaFlip);pandaRunning=false;$('#pandaSignal').textContent='✓';$('#pandaSignal').className='panda-signal';saveArcade('Panda Tap',Math.min(pandaScore,30))}},1000)}

let jadeNext=1,jadeLeft=20,jadeRunning=false,jadeTimerInt=null;
function buildJade(){const board=$('#jadeBoard');if(!board)return;const nums=Array.from({length:20},(_,i)=>i+1).sort(()=>Math.random()-.5);board.innerHTML='';jadeNext=1;$('#jadeScore').textContent='0/20';nums.forEach(n=>{const b=document.createElement('button');b.textContent=n;b.onclick=()=>{if(!jadeRunning||n!==jadeNext)return;b.classList.add('done');jadeNext++;$('#jadeScore').textContent=(jadeNext-1)+'/20';if(jadeNext===21){clearInterval(jadeTimerInt);jadeRunning=false;saveArcade('Jade Steps',20)}};board.appendChild(b)})}
function startJade(){if(jadeRunning)return;jadeRunning=true;jadeLeft=20;buildJade();$('#jadeTimer').textContent='20s';jadeTimerInt=setInterval(()=>{jadeLeft--;$('#jadeTimer').textContent=jadeLeft+'s';if(jadeLeft<=0){clearInterval(jadeTimerInt);jadeRunning=false;saveArcade('Jade Steps',Math.min(jadeNext-1,20))}},1000)}

$$('.game-start').forEach(btn=>btn.addEventListener('click',()=>{const g=btn.dataset.game;if(g==='tiger')startTiger();if(g==='snake')startSnake();if(g==='dragon')buildDragon();if(g==='lantern')buildLantern();if(g==='panda')startPanda();if(g==='jade')startJade()}));
