import React, {useEffect, useState, useRef} from 'react';
import {createRoot} from 'react-dom/client';
import './style.css';
import {ArcadeBar, HarvestEffects, quip, useHarvestSound} from './Arcade';

async function api(path, body) {
  const response = await fetch('/api/'+path, body ? {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)} : {});
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || 'Unable to reach the game server.');
  return data;
}
function Leaf(){return <svg viewBox="0 0 32 32" fill="currentColor" aria-hidden="true"><path d="M28 3C10 3 3 10 5 23c7-6 12-9 17-12C14 17 9 22 5 29l3 1 3-6C24 25 28 16 28 3Z"/></svg>}
function ScanIcon(){return <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" aria-hidden="true"><path d="M8 3H3v5m13-5h5v5M3 16v5h5m13-5v5h-5M3 12h18"/><circle cx="12" cy="12" r="4"/></svg>}
function Scene({state,session,busy,config,events}){
  const phase=config.phases[state.phase];
  return <section className="field"><div className="scene-heading"><h1>{phase.name}</h1><span>Fase {String(state.phase+1).padStart(2,'0')} / {String(config.phases.length).padStart(2,'0')}</span></div>
    <div className={'camera '+(busy?'scanning':'')}>
      <img className="scene-image" src={`/api/frame?session=${session}&v=${state.revision}`} alt={`${phase.short}: fruit-bearing branches in a realistic orchard`} />
      <div className="camera-top"><span><i/> CÂMERA DO POMAR · {phase.light.toUpperCase()}</span><span>1200 × 800</span></div>
      {events.map((e,i)=><div key={i} className={'detection '+(e.correct?'good':e.scored?'bad':'ignored')} style={{left:e.box[0]/12+'%',top:e.box[1]/8+'%',width:(e.box[2]-e.box[0])/12+'%',height:(e.box[3]-e.box[1])/8+'%'}}><span>{e.reason==='decoy'?'ISCA: ':''}{e.label} {Math.round(e.confidence*100)}% · {e.points>0?'+':''}{e.points}</span></div>)}
      <HarvestEffects events={events} revision={state.revision}/>
      {busy&&<div className="scan-line"/>}
      <div className="camera-bottom"><span>{busy?'Zé está procurando frutas…':state.done?'Fase concluída · Confira a colheita':'Visão YOLO · Pronto para colher'}</span><span>{state.scans} / {state.max_scans} leituras</span></div>
    </div><div className="field-description">{phase.description}<span>Limiar de acerto: IoU ≥ 0.40</span></div>
  </section>
}
function Controls({state,config,model,setModel,confidence,setConfidence,busy,onScan,onNext,feedback}){
  return <aside className="controls"><h2>Central da colheita</h2>{state.decoys>0&&<p className="trap-warning">{state.decoys} iscas no cenário · decoração não é fruta!</p>}<div className="score-block"><span>Pontuação</span><strong className={state.score<0?'negative':''}>{String(state.score).padStart(4,'0')}</strong></div>
    <div className="metrics"><div><span>{state.total===0?'Frutas reais':'Colhidas'}</span><strong>{state.harvested}<small> / {state.total}</small></strong></div><div><span>Precisão</span><strong>{state.precision===null?'—':`${Math.round(state.precision)}%`}</strong></div></div>
    <div className="setting"><label htmlFor="confidence">Confiança do modelo <b>{confidence.toFixed(2)}</b></label><input id="confidence" type="range" min=".05" max=".95" step=".05" value={confidence} disabled={busy} onChange={e=>setConfidence(Number(e.target.value))}/><div className="range-labels"><span>0.05</span><span>0.50</span><span>0.95</span></div></div>
    <div className="setting model-setting"><label htmlFor="model">Modelo de detecção</label><select id="model" value={model} onChange={e=>setModel(e.target.value)} disabled={busy}>{config.models.map(m=><option key={m}>{m}</option>)}</select></div>
    <div className="action-area"><button className="primary" onClick={state.done?onNext:onScan} disabled={busy||!model}><ScanIcon/>{busy?'Analisando…':state.done?(state.phase===config.phases.length-1?'Encerrar colheita':'Próxima fase'):'Analisar e colher'}</button>
    <p className="feedback" role="status" aria-live="polite">{feedback || 'Acertou? Vai para o cesto. Errou? Vai para o currículo.'}</p></div>
  </aside>
}
function PhaseRail({state,phases}){
  const rail=useRef(null);
  useEffect(()=>{const current=rail.current?.children[state.phase];if(current)rail.current.scrollTo({left:current.offsetLeft-rail.current.offsetLeft-18,behavior:window.matchMedia('(prefers-reduced-motion: reduce)').matches?'instant':'smooth'})},[state.phase]);
  return <nav ref={rail} className="phase-rail" aria-label="Progresso da campanha">{phases.map((p,i)=><div key={p.short} className={'phase-tile '+(i===state.phase?'active':'')+(i<state.phase?' completed':'')} aria-current={i===state.phase?'step':undefined}><img src={`/api/thumbnail/${i}`} alt=""/><div><span className="phase-number">{i<state.phase?'✓':String(i+1).padStart(2,'0')}</span><span>{p.short}</span>{i>state.phase&&<span className="locked">·</span>}</div></div>)}</nav>
}
function ModelLab({config,onRefresh}){
  return <section className="model-lab"><div><h1>Seu modelo. Sua colheita.</h1><p>Teste seu detector nas {config.phases.length} fases — inclusive nas pegadinhas.</p></div><div className="lab-columns"><article><h2>Carregar modelo treinado</h2><ol><li>Coloque os pesos Ultralytics YOLO <code>.pt</code> na pasta <code>models/</code> do projeto.</li><li>Use as classes <code>apple</code> e <code>orange</code>. Para outros nomes, crie um arquivo de aliases junto dos pesos.</li><li>Atualize a lista, volte ao pomar e selecione seu modelo.</li></ol><pre>{'models/\n  yolov8n.pt       ← modelo incluído\n  best.pt         ← seu detector\n  best.json       ← aliases opcionais'}</pre><p>Exemplo de <code>best.json</code></p><pre>{'{ "ripe_apple": "apple", "laranja": "orange" }'}</pre><button className="secondary" onClick={onRefresh}>Atualizar lista de modelos</button></article><article><h2>Pesos disponíveis</h2>{config.models.map(m=><div className="model-row" key={m}><span>{m}</span><small>{m==='yolov8n.pt'?'Modelo COCO':'Personalizado'}</small></div>)}<h2 className="lab-note">Como funciona a pontuação</h2><p>Inferência local real, com frutas anotadas independentemente do modelo. Um acerto exige a classe correta e sobreposição IoU de pelo menos 0,40. Cada fruta rende pontos uma única vez.</p><p>Uma previsão de maçã ou laranja sem fruta real correspondente custa 40 pontos. Iscas não desaparecem. Outras classes, como sports ball, são ignoradas sem punição. Até cinco leituras por fase; a final sem frutas exige uma leitura.</p><p>A sequência de acertos não multiplica os pontos. O modo automático faz leituras em sequência e para ao concluir a fase. Desligue-o para ajustar o detector. Pressione Espaço para uma leitura manual.</p><p className="disclosure">Cenários fotográficos sintéticos, incluindo imitações deliberadas de frutas. Não são um teste de desempenho em uma fazenda real. Carregue apenas pesos de fontes confiáveis.</p></article></div></section>
}
function Summary({state,onRestart,session}){
  return <section className="summary"><Leaf/><h1>Fim de expediente!</h1><p>{state.phase_count} fases. {state.fooled} pegadinhas. Um robô cheio de histórias.</p><strong className="final-score">{state.score.toLocaleString('pt-BR')}<small>pontos no total</small></strong><div className="summary-metrics"><span><b>{state.correct}</b> frutas colhidas</span><span><b>{state.wrong}</b> falsos positivos</span><span><b>{(state.precision??0).toLocaleString('pt-BR')}%</b> de precisão</span></div><div className="report-table">{state.reports.map(r=><div key={r.phase}><span>{String(r.phase).padStart(2,'0')} / {r.name}</span><b>{r.total===0?(r.wrong===0?"Pegadinha evitada!":"Caiu na pegadinha!"):`${r.harvested} / ${r.total} colhidas`}</b><span>{r.scans} {r.scans===1?'leitura':'leituras'}</span></div>)}</div><div className="summary-actions"><button className="primary" onClick={onRestart}>Começar nova colheita</button><a className="secondary" href={`/api/report?session=${session}`} download="orchard-report.json">Baixar relatório</a></div></section>
}
function App(){
  const [config,setConfig]=useState(null),[state,setState]=useState(null),[session,setSession]=useState('');
  const [auto,setAuto]=useState(false),[sound,setSound]=useState(false),[message,setMessage]=useState('');
  const playSound=useHarvestSound();
  const [view,setView]=useState('field'),[model,setModel]=useState('yolov8n.pt'),[confidence,setConfidence]=useState(.5);
  const [busy,setBusy]=useState(false),[error,setError]=useState(''),[feedback,setFeedback]=useState(''),[events,setEvents]=useState([]);
  async function start(){setAuto(false);setMessage('');setBusy(true);setError('');try{const data=await api('start',{session});setSession(data.session);setState(data);setEvents([]);setFeedback('');setView('field');}catch(e){setError(e.message)}finally{setBusy(false)}}
  useEffect(()=>{let active=true;Promise.all([api('config'),api('start',{})]).then(([c,s])=>{if(active){setConfig(c);setState(s);setSession(s.session);setModel(c.default_model)}}).catch(e=>active&&setError(e.message));return()=>{active=false}},[]);
  useEffect(()=>{if(!events.length)return;const id=setTimeout(()=>setEvents([]),2200);return()=>clearTimeout(id)},[events]);
  useEffect(()=>{if(state?.done || view!=='field')setAuto(false)},[state?.done,view]);
  useEffect(()=>{if(!auto||busy||!state||state.done||view!=='field')return;const timer=setTimeout(scan,2300);return()=>clearTimeout(timer)},[auto,busy,state?.revision,view,model,confidence,sound]);
  useEffect(()=>{const key=e=>{if(e.code==='Space'&&!e.repeat&&!['INPUT','SELECT','TEXTAREA','BUTTON','A'].includes(e.target.tagName)&&view==='field'&&state&&!state.done&&!state.finished&&!busy){e.preventDefault();scan()}};window.addEventListener('keydown',key);return()=>window.removeEventListener('keydown',key)},[busy,state,view,model,confidence,sound]);
  async function scan(){if(busy)return;setBusy(true);setError('');setEvents([]);try{const result=await api('scan',{session,model,confidence,revision:state.revision});setState(result);setEvents(result.events);const n=result.events.filter(e=>e.correct).length;const bad=result.events.filter(e=>e.scored&&!e.correct).length;setMessage(quip(result));if(sound)playSound(bad>0);setFeedback(`${n} colhidas · ${bad} erros · ${(result.latency_ms/1000).toFixed(2)}s${!result.events.length?' — Experimente baixar a confiança.':''}`)}catch(e){setAuto(false);setError(e.message)}finally{setBusy(false)}}
  async function next(){setAuto(false);setMessage('');setBusy(true);setError('');try{setState(await api('next',{session}));setEvents([]);setFeedback('')}catch(e){setError(e.message)}finally{setBusy(false)}}
  async function refresh(){try{const c=await api('config');setConfig(c);setError('')}catch(e){setError(e.message)}}
  if(!config||!state)return <main className="loading"><Leaf/><h1>Abrindo o pomar…</h1>{error&&<p role="alert">{error}</p>}<p>Preparando o turno do robô Zé.</p>{error&&<button onClick={()=>location.reload()}>Tentar novamente</button>}</main>;
  return <><header><a className="brand" href="#" onClick={e=>{e.preventDefault();setView('field')}}><Leaf/>ORCHARD</a><nav><button className={view==='field'?'selected':''} onClick={()=>setView('field')}>Pomar</button><button className={view==='models'?'selected':''} onClick={()=>setView('models')}>Laboratório</button></nav><button className="reset" disabled={busy} onClick={start}>Novo jogo</button></header>
  {error&&<div className="error" role="alert">{error}<button onClick={()=>setError('')} aria-label="Fechar erro">×</button></div>}
  <main>{view==='models'?<ModelLab config={config} onRefresh={refresh}/>:state.finished?<Summary state={state} session={session} onRestart={start}/>:<><ArcadeBar state={state} auto={auto} setAuto={setAuto} sound={sound} setSound={v=>{setSound(v);if(v)playSound()}} message={message} busy={busy}/><div className="workspace"><Scene state={state} session={session} busy={busy} config={config} events={events}/><Controls state={state} config={config} model={model} setModel={setModel} confidence={confidence} setConfidence={setConfidence} busy={busy} onScan={scan} onNext={next} feedback={feedback}/></div><PhaseRail state={state} phases={config.phases}/></>}</main>
  <footer><span>Pontuação</span><div><b>+100</b> colheita correta</div><div><b className="negative">−40</b> erro de detecção</div><small>YOLO local · Pomar sintético</small></footer></>
}
createRoot(document.getElementById('root')).render(<App/>);
