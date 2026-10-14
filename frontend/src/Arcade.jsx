import React, {useRef, useEffect} from 'react';

export function useHarvestSound() {
  const audio = useRef(null);
  useEffect(() => () => { audio.current?.close().catch(() => {}); }, []);
  return async (error = false) => {
    try {
      const Audio = window.AudioContext || window.webkitAudioContext;
      if (!Audio) return;
      audio.current ||= new Audio();
      const ctx = audio.current;
      await ctx.resume();
      [0, 1, 2].forEach((step) => {
        const oscillator = ctx.createOscillator(), gain = ctx.createGain();
        oscillator.connect(gain); gain.connect(ctx.destination);
        oscillator.type = error ? 'triangle' : 'sine';
        oscillator.frequency.value = error ? 260 - step * 65 : 440 * [1, 1.25, 1.5][step];
        const t = ctx.currentTime + step * .09;
        gain.gain.setValueAtTime(.045, t); gain.gain.exponentialRampToValueAtTime(.001, t + .15);
        oscillator.start(t); oscillator.stop(t + .16);
      });
    } catch { /* Sound is optional; browser audio policies never interrupt a harvest. */ }
  };
}
export function quip(result) {
  const trap = result.events.find(e => e.reason === 'decoy');
  if (trap) return ({'maçã de plástico':'Colhi uma maçã com garantia de fábrica. Não recomendo a torta.', 'vela de laranja':'Essa laranja tem pavio. O suco vai sair… quente.', 'bolinha de Natal':'Ho ho… ops. Acabei de colher o Natal.', 'bola de basquete':'Três pontos na cesta! Menos quarenta no placar.'})[trap.decoy];
  if (result.events.some(e => e.scored && !e.correct)) return 'Minha confiança estava alta. Minha precisão pediu demissão.';
  if (result.total === 0) return 'Nada de fruta. Nada de golpe. Hoje eu venci o departamento de decoração.';
  if (!result.events.some(e => e.correct)) return 'Estou contemplando a natureza. Talvez baixar a confiança ajude.';
  return ['Mais uma colheita sem morder o cabo USB!', 'Fruta no cesto, autoestima no processador.', 'Minha avó dizia: quem vê pixels, não vê coração.', 'Hoje a salada de frutas vem com inteligência artificial.'][result.scans % 4];
}
export function ArcadeBar({state, auto, setAuto, sound, setSound, message, busy}) {
  return <section className="arcade-bar" aria-label="Modo de jogo"><div className="robot-speech"><span className="robot-name">ROBÔ ZÉ</span><p aria-live="polite">{message || 'Pronto para colher. Meu diploma em frutologia chegou por e-mail.'}</p></div><div className="arcade-switches"><button className={auto?'secondary enabled':'secondary'} aria-pressed={auto} disabled={state.done || state.finished} onClick={()=>setAuto(!auto)}>{auto?'Pausar automático':'Colheita automática'}</button><button className="secondary" aria-pressed={sound} onClick={()=>setSound(!sound)}>Som: {sound?'ligado':'desligado'}</button></div><div className="combo" key={state.combo}><strong>{state.combo}×</strong><span>acertos seguidos<br/><small>recorde: {state.best_combo}</small></span></div><small className="space-tip">{busy?'Zé está pensando…':'Espaço para analisar'}</small></section>;
}
export function HarvestEffects({events, revision}) {
  const correct = events.filter(e=>e.correct);
  const failed = events.some(e=>e.scored&&!e.correct);
  return <div key={revision} className={'harvest-effects '+(failed?'ouch':'')} aria-hidden="true">{correct.map((e,i)=><span className="floating-points" key={i} style={{left:(e.box[0]+e.box[2])/24+'%',top:(e.box[1]+e.box[3])/16+'%',animationDelay:i*.04+'s'}}>+100</span>)}{correct.length>=3&&Array.from({length:18},(_,i)=><i className="confetti" key={'c'+i} style={{left:(i*37%100)+'%',background:['#b9f477','#ffbd67','#f8e79c'][i%3],animationDelay:i*.025+'s',rotate:i*31+'deg'}}/>)}{failed&&<span className="oops">EITA! PEGADINHA?</span>}</div>;
}
