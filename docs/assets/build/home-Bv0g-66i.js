import{f as e,i as t,r as n,s as r,t as i}from"./logic-B3QEs7v5.js";import{r as a,t as o}from"./voxel-CGR-sNJU.js";import{s}from"./data-BEtu4ex9.js";import{d as c,i as ee,l,m as u,n as te,o as d,r as f,s as p,t as m,u as ne}from"./ui-DnmqvsTN.js";import{t as re}from"./chart-B41LSN13.js";async function h(e,l){let{t:h,labels:b,lang:oe,i18n:x,fc:S,fcH:C,horizon:w,mode:se,panel:T,area:E,regionMeta:D}=l,O=Math.max(...C.map(e=>e.week)),k=e=>C.filter(t=>t.level===e).length,A=k(i[3]),j=k(i[2]),ce=k(i[1]),M=t(S,C),N=M.filter(e=>e.level===i[2]||e.level===i[3]).slice(0,4),P=N.length?N:M.filter(e=>e.level===i[1]).slice(0,3),F=[...M].sort((e,t)=>t.q50_per100k-e.q50_per100k).slice(0,6),le=se===`replay`?ie(b,w,C):A+j===0?ae(h,b):``,I=new Set(C.map(e=>e.unit_id)),L=new Map((await s(T,`history`)).filter(e=>e.week===O&&I.has(e.unit_id)&&e.cases!=null).map(e=>[e.unit_id,e.cases])),R=[...new Set(S.map(e=>e.horizon))].sort((e,t)=>e-t),z=e=>S.filter(t=>t.horizon===e).reduce((e,t)=>e+t.q50,0),B=[...L.values()].reduce((e,t)=>e+t,0),V=L.size?z(w)/Math.max(B,1)-1:null,H=C.filter(e=>(L.get(e.unit_id)??0)>=5).map(e=>({...e,now:L.get(e.unit_id),pct:e.q50/L.get(e.unit_id)-1})).filter(e=>e.pct>0).sort((e,t)=>t.pct-e.pct).slice(0,5);e.innerHTML=`
    <section class="card status-strip" aria-labelledby="home-act-title">
      <div class="status-strip__lead"><span class="home-eyebrow" id="home-act-title">${c(b.act_now)}</span><div class="status-strip__total">${p(A+j)}<span>${c(b.on_alert)}</span></div></div>
      <div class="status-strip__levels" aria-label="${c(b.act_now)}">
        ${g(i[3],`warning`,A,h)}${g(i[2],`watch`,j,h)}${g(i[1],`above`,ce,h)}
      </div>
      <div class="status-strip__message">${le}</div>
    </section>

    <div class="overview-insights">
      <section class="card">
        ${d(`areaDetail`,b.trend,b.trend_sub)}
        ${V==null?``:`<div class="trend-head" data-dir="${V>0?`up`:`down`}"><b class="nums">${V>0?`▲`:`▼`} ${Math.abs(Math.round(V*100))}%</b><span>${c(b.vs_now.replace(`{h}`,w))}</span></div>`}
        <div id="home-trend" class="chart-box"></div>
      </section>
      <section class="card">
        ${d(`alert`,b.rising,b.rising_sub)}
        ${H.length?`<ol class="priority-list">${H.map((e,t)=>v(e,t,l)).join(``)}</ol>`:`<div class="empty-state"><span class="empty-state__icon"><i data-icon="check" data-size="20"></i></span><div>${c(b.no_rising)}</div></div>`}
      </section>
      <section class="card">
        ${d(`check`,b.do_week)}
        ${P.length?`<div class="do-list">${P.slice(0,3).map(e=>y(e,l)).join(``)}</div>`:`<div class="empty-state"><span class="empty-state__icon"><i data-icon="check" data-size="20"></i></span><div>${c(b.quiet)}</div></div>`}
      </section>
    </div>

    <div class="overview-grid" aria-label="${c(h.nav_map)}">
      <section class="card overview-map">
        ${d(`forecastMap`,h.nav_map)}
        <div class="home-map" id="home-map" role="img" aria-label="${c(h.nav_map)}"><div class="home-map__tip" id="home-map-tip" hidden></div></div>
        <div class="map-footer"><ul class="home-legend">${i.map(e=>`<li data-lv="${m[e]}"><span class="sq sq--round"></span>${c(l.levelName(e))}</li>`).join(``)}</ul>
          <a class="inline-link" href="?page=map" data-go="map">${c(h.open_map)} <i data-icon="arrowRight" data-size="18"></i></a></div>
      </section>

      <aside class="card overview-priority">
        ${d(`alert`,h.rank)}
        ${F.length?`<ol class="priority-list" id="home-priority">${F.map((e,t)=>_(e,t,l)).join(``)}</ol>`:`<div class="empty-state"><span class="empty-state__icon"><i data-icon="check" data-size="20"></i></span><div>${c(b.quiet)}</div></div>`}
        <div class="priority-list__footer"><a class="inline-link" href="?page=map" data-go="map">${c(b.all_areas)} <i data-icon="arrowRight" data-size="18"></i></a></div>
      </aside>
    </div>`,e.querySelectorAll(`[data-go]`).forEach(e=>e.addEventListener(`click`,t=>{t.ctrlKey||t.metaKey||t.shiftKey||t.altKey||(t.preventDefault(),l.go(e.dataset.go,e.dataset.u?{area:e.dataset.u}:{}))})),e.querySelector(`#story-btn`)?.addEventListener(`click`,()=>l.set({panel:`province`,mode:`replay`,region:null,area:null})),l.topDownload(h.download_brief,()=>ne(`epilag_action_brief.md`,n(P,{t:h,lang:oe,i18n:x,panelLabel:l.panelLabel,horizon:w,asOf:O}),`text/markdown`));let U=re(e.querySelector(`#home-trend`),{height:170,text:!0,categories:[b.now,...R.map(e=>b.wk_ahead.replace(`{h}`,e))],groups:[{values:[B,...R.map(z)],colors:[`#8A9891`,...R.map(e=>e===w?`#08754F`:`#9FCBA6`)]}]}),W=e.querySelector(`#home-map`),G=e.querySelector(`#home-map-tip`),K=T===`province`&&D?await a(`voxel_regions`):await a(`voxel_ph`),q=T===`province`&&D?K[D.psgc]:T===`province`?K.province:K.region,J=new Map(C.map(e=>[e.unit_id,e])),Y=await o(W,{grid:q,pixel:matchMedia(`(max-width: 680px)`).matches?2:3,markers:T!==`province`,framing:`land`,onHover(e,t){let n=e&&J.get(e);if(Y.highlight(e),!n){G.hidden=!0;return}let i=W.getBoundingClientRect();G.innerHTML=`<b>${c(n.unit_name)}</b>${u(l,n.level)}<span>${r(n.q50)} (${r(n.q10)}–${r(n.q90)})</span>`,G.hidden=!1,G.style.left=`${Math.max(8,Math.min(t.clientX-i.left+14,i.width-190))}px`,G.style.top=`${Math.max(8,Math.min(t.clientY-i.top+14,i.height-88))}px`},onPick(e){e&&J.has(e)&&l.go(`unit`,{area:e})}});Y.setValues(Object.fromEntries(Y.units.map(e=>{let t=J.get(e);return[e,t?{color:te[t.level],height:f[t.level]}:{color:ee,height:1}]})),{duration:520}),Y.highlight(E);let X=()=>{G.hidden=!0,Y.highlight(E)};W.addEventListener(`pointerleave`,X);let Z=e.querySelector(`#home-priority`),Q=e=>Y.highlight(e.target.closest(`[data-u]`)?.dataset.u??null),$=()=>Y.highlight(E);return Z?.addEventListener(`pointerover`,Q),Z?.addEventListener(`pointerleave`,$),Z?.addEventListener(`focusin`,Q),Z?.addEventListener(`focusout`,$),()=>{U(),W.removeEventListener(`pointerleave`,X),Z?.removeEventListener(`pointerover`,Q),Z?.removeEventListener(`pointerleave`,$),Z?.removeEventListener(`focusin`,Q),Z?.removeEventListener(`focusout`,$),Y.dispose()}}function g(e,t,n,r){return`<div class="status-level" data-lv="${m[e]}"><span class="sq sq--round"></span><span class="status-level__copy"><b class="nums">${p(n)}</b><span>${c(r[`${t}_n`])}</span></span></div>`}function ie(t,n,r){let i=e(r);return`<p><b>${i.flagged} / ${i.crossed}</b> ${c(t.flagged_early.replace(`{h}`,n))}</p>`}function ae(e,t){return`<div class="status-message__title">${c(t.quiet)}</div><button type="button" class="btn btn--ghost btn--sm" id="story-btn">${c(e.replay_story)}</button>`}function _(e,t,n){return`<li><a class="priority-row" href="?page=unit&area=${encodeURIComponent(e.unit_id)}" data-u="${c(e.unit_id)}" data-go="unit" aria-label="${c(`${e.unit_name}, ${n.levelName(e.level)}`)}" title="${c(`${n.t.range}: ${r(e.q10)}–${r(e.q90)}`)}">
    <span class="priority-row__rank">${t+1}</span><span class="priority-row__copy"><b>${c(e.unit_name)}</b><small>${r(e.q50)} ${c(n.labels.cases_n)}</small></span>
    <span class="priority-row__level">${u(n,e.level)}<small>${e.q50_per100k.toFixed(1)} ${c(n.labels.per100k_short)}</small></span></a></li>`}function v(e,t,n){return`<li><a class="priority-row" href="?page=unit&area=${encodeURIComponent(e.unit_id)}" data-u="${c(e.unit_id)}" data-go="unit" aria-label="${c(`${e.unit_name}, +${Math.round(e.pct*100)}%, ${n.levelName(e.level)}`)}" title="${c(n.levelName(e.level))}">
    <span class="priority-row__rank">${t+1}</span><span class="priority-row__copy"><b>${c(e.unit_name)}</b><small>${r(e.now)} → ${r(e.q50)} ${c(n.labels.cases_n)}</small></span>
    <span class="rise-pct nums">${l(e.level)}+${Math.round(e.pct*100)}%</span></a></li>`}function y(e,t){return`<a class="do-row" data-lv="${m[e.level]}" href="?page=unit&area=${encodeURIComponent(e.unit_id)}" data-u="${c(e.unit_id)}" data-go="unit">
    <span class="do-row__name">${c(e.unit_name)} ${u(t,e.level)}</span><small>${c(t.labels.level_action[e.level])}</small></a>`}export{h as render};