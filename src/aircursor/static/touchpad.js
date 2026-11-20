'use strict';
const $ = id => document.getElementById(id);
const state = {paired:false, down:false, moved:false, long:false, scroll:false, lastX:0,lastY:0, lastAvg:0, accX:0,accY:0, sending:false,timer:null,lastTap:0,orientation:null,lastMotionSent:0, motion:false};
const defaults = {sensitivity:'1.5',tap:'left',hold:'right',motionSpeed:'2'};
let settings;
try { settings = Object.assign({},defaults,JSON.parse(localStorage.getItem('aircursor-settings') || '{}')); }
catch (_) { settings = Object.assign({},defaults); }
function save(){try{localStorage.setItem('aircursor-settings',JSON.stringify(settings));}catch (_){}}
function message(value,error=false){$('feedback').textContent=value;$('feedback').className=error?'small error':'small';}
function motionMessage(value,error=false){$('motion-message').textContent=value;$('motion-message').className=error?'small error':'small';}
async function api(path,method='GET',data){
 const response=await fetch('/api/v1/'+path,{method,credentials:'same-origin',headers:{'Content-Type':'application/json','X-AirCursor-Client':'1'},body:data===undefined?undefined:JSON.stringify(data)});
 const result=await response.json();
 if(!response.ok) {if(response.status===401 && path!=='pair') paired(false);throw new Error(result.message||result.error||'Request failed');}
 return result;
}
function paired(value){state.paired=value;$('pairing').classList.toggle('hidden',value);$('dashboard').classList.toggle('hidden',!value);$('badge').textContent=value?'Connected':'Not paired';if(!value)stopMotion();}
async function start(){try{const s=await api('status');paired(!!s.paired);}catch(e){$('pair-message').textContent=e.message;}}
$('pair-form').addEventListener('submit',async e=>{e.preventDefault();try{await api('pair','POST',{pin:$('pin').value});$('pin').value='';$('pair-message').textContent='';paired(true);}catch(err){$('pair-message').textContent=err.message;}});
$('logout').addEventListener('click',async()=>{try{await api('logout','POST',{});paired(false);}catch(e){message(e.message,true);}});
function setOptions(){for(const [id,key] of [['sensitivity','sensitivity'],['tap-action','tap'],['hold-action','hold'],['motion-speed','motionSpeed']]){$(id).value=settings[key];$(id).addEventListener('input',()=>{settings[key]=$(id).value;save();updateOutputs();});}updateOutputs();}
function updateOutputs(){$('sensitivity-value').value=settings.sensitivity;$('motion-value').value=settings.motionSpeed;}
async function click(button,count=1){try{await api('click','POST',{button,count});}catch(e){message(e.message,true);}}
$('left').onclick=()=>click('left');$('right').onclick=()=>click('right');$('double').onclick=()=>click('left',2);
document.querySelectorAll('[data-action]').forEach(button=>button.onclick=async()=>{try{await api('action','POST',{action:button.dataset.action});}catch(e){message(e.message,true);}});
function queueMove(dx,dy){state.accX+=dx;state.accY+=dy;flushMove();}
async function flushMove(){if(state.sending)return;const dx=Math.max(-800,Math.min(800,Math.round(state.accX))),dy=Math.max(-800,Math.min(800,Math.round(state.accY)));if(!dx&&!dy)return;state.accX-=dx;state.accY-=dy;state.sending=true;try{await api('cursor','PATCH',{dx,dy});}catch(e){message(e.message,true);}finally{state.sending=false;if(Math.abs(state.accX)>=1||Math.abs(state.accY)>=1)flushMove();}}
const pad=$('pad');
function clearHold(){clearTimeout(state.timer);state.timer=null;}
pad.addEventListener('pointerdown',e=>{if(state.scroll||!state.paired)return;pad.setPointerCapture(e.pointerId);state.down=true;state.moved=false;state.long=false;state.lastX=e.clientX;state.lastY=e.clientY;pad.classList.add('active');clearHold();state.timer=setTimeout(()=>{if(state.down&&!state.moved&&!state.scroll){state.long=true;if(settings.hold!=='none')click(settings.hold);}},550);});
pad.addEventListener('pointermove',e=>{if(!state.down||state.scroll)return;const dx=e.clientX-state.lastX,dy=e.clientY-state.lastY;state.lastX=e.clientX;state.lastY=e.clientY;if(Math.abs(dx)+Math.abs(dy)>0){state.moved=true;clearHold();queueMove(dx*Number(settings.sensitivity),dy*Number(settings.sensitivity));}});
function pointerEnd(e){if(!state.down)return;state.down=false;clearHold();try{pad.releasePointerCapture(e.pointerId);}catch(_){}pad.classList.remove('active');if(!state.moved&&!state.long&&!state.scroll){const now=Date.now();const wasDouble=now-state.lastTap<320;state.lastTap=now;if(settings.tap==='double'){click('left',2);}else if(wasDouble){clearTimeout(state.tapTimer);click('left',2);}else{state.tapTimer=setTimeout(()=>click(settings.tap),320);}}}
pad.addEventListener('pointerup',pointerEnd);pad.addEventListener('pointercancel',pointerEnd);
pad.addEventListener('touchstart',e=>{if(e.touches.length>=2){state.scroll=true;state.down=false;clearHold();state.lastAvg=(e.touches[0].clientY+e.touches[1].clientY)/2;}},{passive:false});
pad.addEventListener('touchmove',e=>{if(!state.scroll||e.touches.length<2)return;e.preventDefault();const avg=(e.touches[0].clientY+e.touches[1].clientY)/2;const dy=Math.max(-12,Math.min(12,Math.round((state.lastAvg-avg)/5)));state.lastAvg=avg;if(dy)api('scroll','POST',{dy}).catch(err=>message(err.message,true));},{passive:false});
pad.addEventListener('touchend',e=>{if(e.touches.length<2)state.scroll=false;});
pad.addEventListener('touchcancel',()=>{state.scroll=false;});
function stopMotion(){state.motion=false;state.orientation=null;window.removeEventListener('deviceorientation',onOrientation);$('motion-start').disabled=false;$('motion-stop').disabled=true;$('motion-calibrate').disabled=true;}
function onOrientation(e){if(!state.motion||!state.paired||e.gamma===null||e.beta===null)return;const now=performance.now();if(!state.orientation){state.orientation={gamma:e.gamma,beta:e.beta};return;}if(now-state.lastMotionSent<45)return;const dg=e.gamma-state.orientation.gamma,db=e.beta-state.orientation.beta;state.orientation={gamma:e.gamma,beta:e.beta};state.lastMotionSent=now;const speed=Number(settings.motionSpeed);if(Math.abs(dg)<.2&&Math.abs(db)<.2)return;queueMove(Math.max(-35,Math.min(35,dg*speed*2)),Math.max(-35,Math.min(35,db*speed*2)));}
$('motion-start').onclick=async()=>{if(!window.isSecureContext){motionMessage('Motion requires a trusted HTTPS connection (HTTP works for the touchpad).',true);return;}if(!('DeviceOrientationEvent' in window)){motionMessage('This browser does not support phone orientation sensors.',true);return;}try{if(typeof DeviceOrientationEvent.requestPermission==='function'){const permission=await DeviceOrientationEvent.requestPermission();if(permission!=='granted')throw new Error('Sensor permission denied');}state.motion=true;state.orientation=null;window.addEventListener('deviceorientation',onOrientation);$('motion-start').disabled=true;$('motion-stop').disabled=false;$('motion-calibrate').disabled=false;motionMessage('Motion enabled. Move your phone gently; tap Calibrate to reset.');}catch(e){motionMessage(e.message,true);}};
$('motion-stop').onclick=()=>{stopMotion();motionMessage('Motion stopped.');};
$('motion-calibrate').onclick=()=>{state.orientation=null;motionMessage('Calibrated. Move your phone to control the cursor.');};
setOptions();start();
