import{r as e,t}from"./voxel-BfSZQAZg.js";import{c as n,f as r,i,r as a,s as o,t as s}from"./logic-rqKjkrBE.js";import{d as c,f as ee,i as l,l as u,m as d,n as f,o as p,r as te,s as m,t as h,u as g}from"./ui-CB-7FfJ_.js";var _={map:`forecastMap`,unit:`areaDetail`,budget:`actionPlan`,public:`residents`,qc:`barangay`,proof:`didItWork`},v=[[`props`,`cloud`],[`mosquito`,`fly1`],[`props`,`residents`],[`props`,`hospital`]];async function y(r,y){let{t:T,lang:E,i18n:D,fc:O,fcH:k,horizon:A,mode:j,panel:M}=y,N=Math.max(...k.map(e=>e.week)),P=Math.max(...k.map(e=>e.target_week)),F=e=>k.filter(t=>t.level===e).length,I=F(s[3]),L=F(s[2]),R=F(s[1]),z=i(O,k),B=z.filter(e=>e.level===s[2]||e.level===s[3]).slice(0,6),V=B.length?B:z.filter(e=>e.level===s[1]).slice(0,3),H=[...z].sort((e,t)=>t.q50_per100k-e.q50_per100k).slice(0,6),U=j===`replay`?x(T,A,k):I+L===0?S(T):``;r.innerHTML=`
    ${ee(T.hello,`${A} ${T.weeks_ahead}`,`${T.as_of} ${n(N)} · ${T.for_week} ${n(P)} · ${y.panelLabel}`)}

    <section class="card home-counts" aria-labelledby="home-act-title">
      <div class="home-counts__lead">
        <span class="home-eyebrow" id="home-act-title">${c(T.act_now)}</span>
        <div class="home-counts__total">${m(I+L)}</div>
      </div>
      <div class="home-counts__levels" aria-label="${c(T.act_now)}">
        ${b(s[3],`warning`,I,T)}
        ${b(s[2],`watch`,L,T)}
        ${b(s[1],`above`,R,T)}
      </div>
      <div class="home-counts__state">${U}</div>
      <a class="btn btn--primary btn--sm home-counts__map" href="?page=map" data-go="map">${c(T.open_map)} <i data-icon="arrowRight" data-size="24"></i></a>
    </section>

    <section class="home-forecast" aria-label="${c(T.nav_map)}">
      <section class="card home-map-card">
        ${p(`forecastMap`,T.nav_map,`${T.for_week} ${n(P)}`)}
        <div class="home-map" id="home-map" role="img" aria-label="${c(`${T.nav_map}, ${T.for_week} ${n(P)}`)}">
          <div class="home-map__tip" id="home-map-tip" hidden></div>
        </div>
        <div class="home-map__footer">
          <ul class="home-legend">${s.map(e=>`<li data-lv="${h[e]}"><span class="sq sq--round"></span>${c(y.levelName(e))}</li>`).join(``)}</ul>
        </div>
      </section>

      <aside class="card home-priority">
        ${p(`alert`,T.rank,T.rank_sub)}
        ${H.length?`<ol class="home-priority__list" id="home-priority">${H.map((e,t)=>C(e,t,y)).join(``)}</ol>`:`<div class="callout home-priority__empty"><i data-icon="check" data-size="24"></i>${c(T.brief_empty)}</div>`}
        <a class="home-priority__all" href="?page=map" data-go="map">${c(T.open_map)} <i data-icon="arrowRight" data-size="24"></i></a>
      </aside>
    </section>

    <section class="card home-brief">
      ${p(`actionPlan`,T.brief_head,T.brief_sub)}
      ${B.length?``:`<div class="callout home-brief__empty"><i data-icon="check" data-size="24"></i>${c(T.brief_empty)}</div>`}
      <div class="briefs">${V.map(e=>w(e,y)).join(``)}</div>
      ${V.length?`<div class="home-brief__footer">${g(`dl-brief`,T.download_brief)}</div>`:``}
    </section>

    <section class="card home-story">
      ${p(`alert`,T.story_head)}
      <ol class="home-story__rail">${T.story.map(([e,t],n)=>`<li class="home-story__step${n===0?` home-story__step--on`:``}">
        <span class="home-story__art"><pixel-sprite sprite="${v[n][0]}" pose="${v[n][1]}" scale="${v[n][0]===`props`?1:2}"></pixel-sprite></span>
        <span class="home-story__copy"><b>${c(e)}</b><span>${c(t)}</span></span></li>`).join(``)}</ol>
      <div class="callout home-story__note"><i data-icon="alert" data-size="24"></i>${c(T.story_note)}</div>
    </section>

    <section class="home-tools" aria-labelledby="home-tools-title">
      <div class="home-section-heading"><h2 id="home-tools-title">${c(T.features_head)}</h2><p>${c(T.features_sub)}</p></div>
      <div class="home-tools__grid">${Object.keys(_).map(e=>{let[t,n,r]=D.FEATURES[E][e];return`<a class="card home-tool" href="?page=${e}" data-go="${e}">
          <span class="home-tool__ic"><i data-icon="${_[e]}" data-size="32"></i></span>
          <div class="home-tool__body"><h3>${c(T[`nav_${e}`])}</h3>
            <dl><div><dt>${c(T.does)}</dt><dd>${c(t)}</dd></div><div><dt>${c(T.why_h)}</dt><dd>${c(n)}</dd></div><div><dt>${c(T.you)}</dt><dd class="home-tool__you">${c(r)}</dd></div></dl>
            <span class="home-tool__open">${c(T.open)} <i data-icon="arrowRight" data-size="24"></i></span>
          </div>
        </a>`}).join(``)}</div>
    </section>

    <section class="drill-banner console home-drill">
      <div><div class="kicker">Dengue Drill</div><h2>${c(T.drill_head)}</h2><p>${c(T.drill_sub)}</p>
        <a class="btn btn--light btn--sm" href="../drill/"><i data-icon="play" data-size="24"></i>${c(T.drill_btn)}</a></div>
      <pixel-sprite sprite="frog" pose="watch" scale="3"></pixel-sprite>
    </section>`,r.querySelectorAll(`[data-go]`).forEach(e=>e.addEventListener(`click`,t=>{t.ctrlKey||t.metaKey||(t.preventDefault(),y.go(e.dataset.go,e.dataset.u?{area:e.dataset.u}:{}))})),r.querySelector(`#story-btn`)?.addEventListener(`click`,()=>y.set({panel:`province`,mode:`replay`})),r.querySelector(`#dl-brief`)?.addEventListener(`click`,()=>u(`epilag_action_brief.md`,a(V,{t:T,lang:E,i18n:D,panelLabel:y.panelLabel,horizon:A,asOf:N}),`text/markdown`));let W=r.querySelector(`#home-map`),G=r.querySelector(`#home-map-tip`),K=await e(`voxel_ph`),q=M===`province`?K.province:K.region,J=new Map(k.map(e=>[e.unit_id,e])),Y=await t(W,{grid:q,pixel:matchMedia(`(max-width: 680px)`).matches?2:3,markers:M!==`province`,onHover(e,t){let n=e&&J.get(e);if(Y.highlight(e),!n){G.hidden=!0;return}let r=W.getBoundingClientRect();G.innerHTML=`<b>${c(n.unit_name)}</b>${d(y,n.level)}<span>${o(n.q50)} (${o(n.q10)}–${o(n.q90)})</span>`,G.hidden=!1,G.style.left=`${Math.max(8,Math.min(t.clientX-r.left+14,r.width-190))}px`,G.style.top=`${Math.max(8,Math.min(t.clientY-r.top+14,r.height-88))}px`},onPick(e){e&&J.has(e)&&y.go(`unit`,{area:e})}});Y.setValues(Object.fromEntries(Y.units.map(e=>{let t=J.get(e);return[e,t?{color:f[t.level],height:te[t.level]}:{color:l,height:1}]})),{duration:600});let X=()=>{G.hidden=!0,Y.highlight(null)};W.addEventListener(`pointerleave`,X);let Z=r.querySelector(`#home-priority`),Q=e=>Y.highlight(e.target.closest(`[data-u]`)?.dataset.u??null),$=()=>Y.highlight(null);return Z?.addEventListener(`pointerover`,Q),Z?.addEventListener(`pointerleave`,$),()=>{W.removeEventListener(`pointerleave`,X),Z?.removeEventListener(`pointerover`,Q),Z?.removeEventListener(`pointerleave`,$),Y.dispose()}}function b(e,t,n,r){return`<div class="home-counts__level" data-lv="${h[e]}"><span class="sq sq--round"></span><div><b>${m(n)}</b><span>${c(r[`${t}_n`])}</span></div></div>`}function x(e,t,n){let i=r(n);return`<div class="home-state__eyebrow">${c(e.then)}</div><p><b>${i.flagged} ${c(e.of)} ${i.crossed}</b> ${c(e.then_line.replace(`{h}`,t))}</p>`}function S(e){return`<div class="home-state__eyebrow">${c(e.quiet)}</div><button type="button" class="btn btn--ghost btn--sm" id="story-btn">${c(e.replay_story)}</button>`}function C(e,t,r){return`<li><a class="home-priority__row" href="?page=unit&area=${encodeURIComponent(e.unit_id)}" data-u="${c(e.unit_id)}" data-go="unit">
    <span class="home-priority__rank">${t+1}</span><span class="home-priority__copy"><b>${c(e.unit_name)}</b><small>${c(r.t.cases)}: ${o(e.q50)} (${o(e.q10)}–${o(e.q90)})</small><small>${c(r.t.peak)} ${n(e.peak_week,!1)}</small></span>
    <span class="home-priority__level">${d(r,e.level)}<small>${e.q50_per100k.toFixed(1)} ${c(r.t.per100k)}</small></span>
  </a></li>`}function w(e,t){let[r,i]=t.i18n.PLAYBOOK[t.lang][e.level][0];return`<div class="brief-row home-brief-row" data-lv="${h[e.level]}"><div class="home-brief-row__area"><div class="brief-row__nm">${c(e.unit_name)} ${d(t,e.level)}</div>
    <div class="brief-row__meta">${c(t.t.cases)}: <b>${o(e.q50)}</b> (${o(e.q10)}–${o(e.q90)}) · ${c(t.t.peak)} ${n(e.peak_week,!1)}</div></div>
    <div class="brief-row__next"><b>${c(r)}:</b> ${c(i)}<div class="brief-row__meta">${c(t.t.prepare.replace(`{n}`,o(e.cases_high)))}</div></div></div>`}export{y as render};