import{r as e,t}from"./voxel-CGR-sNJU.js";import{f as n,i as r,r as i,s as a,t as o}from"./logic-rqKjkrBE.js";import{s as ee}from"./data-DbYTdCf-.js";import{d as s,i as c,l,m as u,n as d,o as f,r as p,s as m,t as h,u as te}from"./ui-CnGjrbFj.js";import{t as ne}from"./chart-C5l-ZFvK.js";async function g(n,l){let{t:g,labels:b,lang:oe,i18n:se,fc:x,fcH:S,horizon:C,mode:w,panel:T,area:E,regionMeta:D}=l,O=Math.max(...S.map(e=>e.week)),k=e=>S.filter(t=>t.level===e).length,A=k(o[3]),j=k(o[2]),M=k(o[1]),N=r(x,S),P=N.filter(e=>e.level===o[2]||e.level===o[3]).slice(0,4),F=P.length?P:N.filter(e=>e.level===o[1]).slice(0,3),I=[...N].sort((e,t)=>t.q50_per100k-e.q50_per100k).slice(0,6),L=w===`replay`?re(b,C,S):A+j===0?ie(g,b):``,R=new Set(S.map(e=>e.unit_id)),z=new Map((await ee(T,`history`)).filter(e=>e.week===O&&R.has(e.unit_id)&&e.cases!=null).map(e=>[e.unit_id,e.cases])),B=[...new Set(x.map(e=>e.horizon))].sort((e,t)=>e-t),V=e=>x.filter(t=>t.horizon===e).reduce((e,t)=>e+t.q50,0),H=[...z.values()].reduce((e,t)=>e+t,0),U=z.size?V(C)/Math.max(H,1)-1:null,W=S.filter(e=>(z.get(e.unit_id)??0)>=5).map(e=>({...e,now:z.get(e.unit_id),pct:e.q50/z.get(e.unit_id)-1})).filter(e=>e.pct>0).sort((e,t)=>t.pct-e.pct).slice(0,5);n.innerHTML=`
    <section class="card status-strip" aria-labelledby="home-act-title">
      <div class="status-strip__lead"><span class="home-eyebrow" id="home-act-title">${s(b.act_now)}</span><div class="status-strip__total">${m(A+j)}<span>${s(b.on_alert)}</span></div></div>
      <div class="status-strip__levels" aria-label="${s(b.act_now)}">
        ${_(o[3],`warning`,A,g)}${_(o[2],`watch`,j,g)}${_(o[1],`above`,M,g)}
      </div>
      <div class="status-strip__message">${L}</div>
    </section>

    <div class="overview-insights">
      <section class="card">
        ${f(`areaDetail`,b.trend,b.trend_sub)}
        ${U==null?``:`<div class="trend-head" data-dir="${U>0?`up`:`down`}"><b class="nums">${U>0?`▲`:`▼`} ${Math.abs(Math.round(U*100))}%</b><span>${s(b.vs_now.replace(`{h}`,C))}</span></div>`}
        <div id="home-trend" class="chart-box"></div>
      </section>
      <section class="card">
        ${f(`alert`,b.rising,b.rising_sub)}
        ${W.length?`<ol class="priority-list">${W.map((e,t)=>y(e,t,l)).join(``)}</ol>`:`<div class="empty-state"><span class="empty-state__icon"><i data-icon="check" data-size="20"></i></span><div>${s(b.no_rising)}</div></div>`}
      </section>
      <section class="card">
        ${f(`check`,b.do_week)}
        ${F.length?`<div class="do-list">${F.slice(0,3).map(e=>ae(e,l)).join(``)}</div>`:`<div class="empty-state"><span class="empty-state__icon"><i data-icon="check" data-size="20"></i></span><div>${s(b.quiet)}</div></div>`}
      </section>
    </div>

    <div class="overview-grid" aria-label="${s(g.nav_map)}">
      <section class="card overview-map">
        ${f(`forecastMap`,g.nav_map)}
        <div class="home-map" id="home-map" role="img" aria-label="${s(g.nav_map)}"><div class="home-map__tip" id="home-map-tip" hidden></div></div>
        <div class="map-footer"><ul class="home-legend">${o.map(e=>`<li data-lv="${h[e]}"><span class="sq sq--round"></span>${s(l.levelName(e))}</li>`).join(``)}</ul>
          <a class="inline-link" href="?page=map" data-go="map">${s(g.open_map)} <i data-icon="arrowRight" data-size="18"></i></a></div>
      </section>

      <aside class="card overview-priority">
        ${f(`alert`,g.rank)}
        ${I.length?`<ol class="priority-list" id="home-priority">${I.map((e,t)=>v(e,t,l)).join(``)}</ol>`:`<div class="empty-state"><span class="empty-state__icon"><i data-icon="check" data-size="20"></i></span><div>${s(b.quiet)}</div></div>`}
        <div class="priority-list__footer"><a class="inline-link" href="?page=map" data-go="map">${s(b.all_areas)} <i data-icon="arrowRight" data-size="18"></i></a></div>
      </aside>
    </div>`,n.querySelectorAll(`[data-go]`).forEach(e=>e.addEventListener(`click`,t=>{t.ctrlKey||t.metaKey||t.shiftKey||t.altKey||(t.preventDefault(),l.go(e.dataset.go,e.dataset.u?{area:e.dataset.u}:{}))})),n.querySelector(`#story-btn`)?.addEventListener(`click`,()=>l.set({panel:`province`,mode:`replay`,region:null,area:null})),l.topDownload(g.download_brief,()=>te(`epilag_action_brief.md`,i(F,{t:g,lang:oe,i18n:se,panelLabel:l.panelLabel,horizon:C,asOf:O}),`text/markdown`));let ce=ne(n.querySelector(`#home-trend`),{height:170,text:!0,categories:[b.now,...B.map(e=>b.wk_ahead.replace(`{h}`,e))],groups:[{values:[H,...B.map(V)],colors:[`#8A9891`,...B.map(e=>e===C?`#08754F`:`#9FCBA6`)]}]}),G=n.querySelector(`#home-map`),K=n.querySelector(`#home-map-tip`),q=T===`province`&&D?await e(`voxel_regions`):await e(`voxel_ph`),le=T===`province`&&D?q[D.psgc]:T===`province`?q.province:q.region,J=new Map(S.map(e=>[e.unit_id,e])),Y=await t(G,{grid:le,pixel:matchMedia(`(max-width: 680px)`).matches?2:3,markers:T!==`province`,framing:`land`,onHover(e,t){let n=e&&J.get(e);if(Y.highlight(e),!n){K.hidden=!0;return}let r=G.getBoundingClientRect();K.innerHTML=`<b>${s(n.unit_name)}</b>${u(l,n.level)}<span>${a(n.q50)} (${a(n.q10)}–${a(n.q90)})</span>`,K.hidden=!1,K.style.left=`${Math.max(8,Math.min(t.clientX-r.left+14,r.width-190))}px`,K.style.top=`${Math.max(8,Math.min(t.clientY-r.top+14,r.height-88))}px`},onPick(e){e&&J.has(e)&&l.go(`unit`,{area:e})}});Y.setValues(Object.fromEntries(Y.units.map(e=>{let t=J.get(e);return[e,t?{color:d[t.level],height:p[t.level]}:{color:c,height:1}]})),{duration:520}),Y.highlight(E);let X=()=>{K.hidden=!0,Y.highlight(E)};G.addEventListener(`pointerleave`,X);let Z=n.querySelector(`#home-priority`),Q=e=>Y.highlight(e.target.closest(`[data-u]`)?.dataset.u??null),$=()=>Y.highlight(E);return Z?.addEventListener(`pointerover`,Q),Z?.addEventListener(`pointerleave`,$),Z?.addEventListener(`focusin`,Q),Z?.addEventListener(`focusout`,$),()=>{ce(),G.removeEventListener(`pointerleave`,X),Z?.removeEventListener(`pointerover`,Q),Z?.removeEventListener(`pointerleave`,$),Z?.removeEventListener(`focusin`,Q),Z?.removeEventListener(`focusout`,$),Y.dispose()}}function _(e,t,n,r){return`<div class="status-level" data-lv="${h[e]}"><span class="sq sq--round"></span><span class="status-level__copy"><b class="nums">${m(n)}</b><span>${s(r[`${t}_n`])}</span></span></div>`}function re(e,t,r){let i=n(r);return`<p><b>${i.flagged} / ${i.crossed}</b> ${s(e.flagged_early.replace(`{h}`,t))}</p>`}function ie(e,t){return`<div class="status-message__title">${s(t.quiet)}</div><button type="button" class="btn btn--ghost btn--sm" id="story-btn">${s(e.replay_story)}</button>`}function v(e,t,n){return`<li><a class="priority-row" href="?page=unit&area=${encodeURIComponent(e.unit_id)}" data-u="${s(e.unit_id)}" data-go="unit" aria-label="${s(`${e.unit_name}, ${n.levelName(e.level)}`)}" title="${s(`${n.t.range}: ${a(e.q10)}–${a(e.q90)}`)}">
    <span class="priority-row__rank">${t+1}</span><span class="priority-row__copy"><b>${s(e.unit_name)}</b><small>${a(e.q50)} ${s(n.labels.cases_n)}</small></span>
    <span class="priority-row__level">${u(n,e.level)}<small>${e.q50_per100k.toFixed(1)} ${s(n.labels.per100k_short)}</small></span></a></li>`}function y(e,t,n){return`<li><a class="priority-row" href="?page=unit&area=${encodeURIComponent(e.unit_id)}" data-u="${s(e.unit_id)}" data-go="unit" aria-label="${s(`${e.unit_name}, +${Math.round(e.pct*100)}%, ${n.levelName(e.level)}`)}" title="${s(n.levelName(e.level))}">
    <span class="priority-row__rank">${t+1}</span><span class="priority-row__copy"><b>${s(e.unit_name)}</b><small>${a(e.now)} → ${a(e.q50)} ${s(n.labels.cases_n)}</small></span>
    <span class="rise-pct nums">${l(e.level)}+${Math.round(e.pct*100)}%</span></a></li>`}function ae(e,t){return`<a class="do-row" data-lv="${h[e.level]}" href="?page=unit&area=${encodeURIComponent(e.unit_id)}" data-u="${s(e.unit_id)}" data-go="unit">
    <span class="do-row__name">${s(e.unit_name)} ${u(t,e.level)}</span><small>${s(t.labels.level_action[e.level])}</small></a>`}export{g as render};