import{r as e,t}from"./voxel-BfSZQAZg.js";import{c as n,f as r,i,r as ee,s as a,t as o}from"./logic-rqKjkrBE.js";import{d as s,f as c,h as l,i as te,l as u,m as d,n as f,o as p,r as ne,s as m,t as h,u as g}from"./ui-B6vaxqwQ.js";var _=[[`props`,`cloud`],[`mosquito`,`fly1`],[`props`,`residents`],[`props`,`hospital`]];async function v(r,v){let{t:w,labels:T,lang:E,i18n:D,fc:re,fcH:O,horizon:k,mode:A,panel:j}=v,M=Math.max(...O.map(e=>e.week)),N=Math.max(...O.map(e=>e.target_week)),P=e=>O.filter(t=>t.level===e).length,F=P(o[3]),I=P(o[2]),L=P(o[1]),R=i(re,O),z=R.filter(e=>e.level===o[2]||e.level===o[3]).slice(0,4),B=z.length?z:R.filter(e=>e.level===o[1]).slice(0,3),V=[...R].sort((e,t)=>t.q50_per100k-e.q50_per100k).slice(0,6),H=A===`replay`?b(w,k,O):F+I===0?x(w):``,U=()=>u(`epilag_action_brief.md`,ee(B,{t:w,lang:E,i18n:D,panelLabel:v.panelLabel,horizon:k,asOf:M}),`text/markdown`);r.innerHTML=`
    ${c(w.hello,`${k} ${w.weeks_ahead}`,`${w.as_of} ${n(M)} · ${w.for_week} ${n(N)} · ${v.panelLabel}`)}

    <section class="card status-strip" aria-labelledby="home-act-title">
      <div class="status-strip__lead"><span class="home-eyebrow" id="home-act-title">${s(w.act_now)}</span><div class="status-strip__total">${m(F+I)}<span>${s(T.top_areas)}</span></div></div>
      <div class="status-strip__levels" aria-label="${s(w.act_now)}">
        ${y(o[3],`warning`,F,w)}${y(o[2],`watch`,I,w)}${y(o[1],`above`,L,w)}
      </div>
      <div class="status-strip__message">${H}</div>
      <a class="btn btn--primary btn--sm status-strip__action" href="?page=map" data-go="map">${s(w.open_map)} <i data-icon="arrowRight" data-size="18"></i></a>
    </section>

    <div class="overview-grid" aria-label="${s(w.nav_map)}">
      <section class="card overview-map">
        ${p(`forecastMap`,w.nav_map,`${w.for_week} ${n(N)}`)}
        <div class="home-map" id="home-map" role="img" aria-label="${s(`${w.nav_map}, ${w.for_week} ${n(N)}`)}"><div class="home-map__tip" id="home-map-tip" hidden></div></div>
        <div class="map-footer"><ul class="home-legend">${o.map(e=>`<li data-lv="${h[e]}"><span class="sq sq--round"></span>${s(v.levelName(e))}</li>`).join(``)}</ul>
          <a class="inline-link" href="?page=map" data-go="map">${s(w.open_map)} <i data-icon="arrowRight" data-size="18"></i></a></div>
      </section>

      <aside class="card overview-priority">
        ${p(`alert`,w.rank,w.rank_sub)}
        ${V.length?`<ol class="priority-list" id="home-priority">${V.map((e,t)=>S(e,t,v)).join(``)}</ol>`:`<div class="empty-state"><span class="empty-state__icon"><i data-icon="check" data-size="20"></i></span><div>${s(w.brief_empty)}</div></div>`}
        <div class="priority-list__footer"><a class="inline-link" href="?page=map" data-go="map">${s(T.all_areas)} <i data-icon="arrowRight" data-size="18"></i></a></div>
      </aside>
    </div>

    <section class="card brief-card">
      ${p(`actionPlan`,w.brief_head,w.brief_sub)}
      ${z.length?``:`<div class="callout">${s(w.brief_empty)}</div>`}
      <div class="brief-list">${B.map(e=>C(e,v)).join(``)}</div>
      ${B.length?`<div class="brief-footer">${g(`dl-brief`,w.download_brief)}</div>`:``}
    </section>

    <section class="card weeks-card">
      ${p(`alert`,w.story_head)}
      <ol class="weeks-rail">${w.story.map(([e,t],n)=>`<li class="weeks-step${n===0?` weeks-step--on`:``}"><span class="weeks-step__art"><pixel-sprite sprite="${_[n][0]}" pose="${_[n][1]}" scale="${_[n][0]===`props`?1:2}"></pixel-sprite></span><span class="weeks-step__copy"><b>${s(e)}</b><span>${s(t)}</span></span></li>`).join(``)}</ol>
      ${d(T.about_this,`<p>${s(w.story_note)}</p>`)}
    </section>

    <section class="card drill-card">
      <div><div class="kicker">${s(T.drill)}</div><h2>${s(w.drill_head)}</h2><p>${s(w.drill_sub)}</p></div>
      <a class="btn btn--light btn--sm" href="../drill/"><i data-icon="play" data-size="18"></i>${s(w.drill_btn)}</a>
    </section>`,r.querySelectorAll(`[data-go]`).forEach(e=>e.addEventListener(`click`,t=>{t.ctrlKey||t.metaKey||t.shiftKey||t.altKey||(t.preventDefault(),v.go(e.dataset.go,e.dataset.u?{area:e.dataset.u}:{}))})),r.querySelector(`#story-btn`)?.addEventListener(`click`,()=>v.set({panel:`province`,mode:`replay`})),r.querySelector(`#dl-brief`)?.addEventListener(`click`,U),v.topDownload(w.download_brief,U);let W=r.querySelector(`#home-map`),G=r.querySelector(`#home-map-tip`),K=await e(`voxel_ph`),q=j===`province`?K.province:K.region,J=new Map(O.map(e=>[e.unit_id,e])),Y=await t(W,{grid:q,pixel:matchMedia(`(max-width: 680px)`).matches?2:3,markers:j!==`province`,onHover(e,t){let n=e&&J.get(e);if(Y.highlight(e),!n){G.hidden=!0;return}let r=W.getBoundingClientRect();G.innerHTML=`<b>${s(n.unit_name)}</b>${l(v,n.level)}<span>${a(n.q50)} (${a(n.q10)}–${a(n.q90)})</span>`,G.hidden=!1,G.style.left=`${Math.max(8,Math.min(t.clientX-r.left+14,r.width-190))}px`,G.style.top=`${Math.max(8,Math.min(t.clientY-r.top+14,r.height-88))}px`},onPick(e){e&&J.has(e)&&v.go(`unit`,{area:e})}});Y.setValues(Object.fromEntries(Y.units.map(e=>{let t=J.get(e);return[e,t?{color:f[t.level],height:ne[t.level]}:{color:te,height:1}]})),{duration:520});let X=()=>{G.hidden=!0,Y.highlight(null)};W.addEventListener(`pointerleave`,X);let Z=r.querySelector(`#home-priority`),Q=e=>Y.highlight(e.target.closest(`[data-u]`)?.dataset.u??null),$=()=>Y.highlight(null);return Z?.addEventListener(`pointerover`,Q),Z?.addEventListener(`pointerleave`,$),Z?.addEventListener(`focusin`,Q),Z?.addEventListener(`focusout`,$),()=>{W.removeEventListener(`pointerleave`,X),Z?.removeEventListener(`pointerover`,Q),Z?.removeEventListener(`pointerleave`,$),Z?.removeEventListener(`focusin`,Q),Z?.removeEventListener(`focusout`,$),Y.dispose()}}function y(e,t,n,r){return`<div class="status-level" data-lv="${h[e]}"><span class="sq sq--round"></span><span class="status-level__copy"><b class="nums">${m(n)}</b><span>${s(r[`${t}_n`])}</span></span></div>`}function b(e,t,n){let i=r(n);return`<div class="status-message__title">${s(e.then)}</div><p><b>${i.flagged} ${s(e.of)} ${i.crossed}</b> ${s(e.then_line.replace(`{h}`,t))}</p>`}function x(e){return`<div class="status-message__title">${s(e.quiet)}</div><p>${s(e.brief_empty)}</p><button type="button" class="btn btn--ghost btn--sm" id="story-btn">${s(e.replay_story)}</button>`}function S(e,t,r){return`<li><a class="priority-row" href="?page=unit&area=${encodeURIComponent(e.unit_id)}" data-u="${s(e.unit_id)}" data-go="unit" aria-label="${s(`${e.unit_name}, ${r.levelName(e.level)}`)}">
    <span class="priority-row__rank">${t+1}</span><span class="priority-row__copy"><b>${s(e.unit_name)}</b><small>${s(r.t.cases)}: ${a(e.q50)} (${a(e.q10)}–${a(e.q90)})</small><small>${s(r.t.peak)} ${n(e.peak_week,!1)}</small></span>
    <span class="priority-row__level">${l(r,e.level)}<small>${e.q50_per100k.toFixed(1)} ${s(r.t.per100k)}</small></span></a></li>`}function C(e,t){let[r,i]=t.i18n.PLAYBOOK[t.lang][e.level][0];return`<div class="brief-row" data-lv="${h[e.level]}"><div><div class="brief-row__name">${s(e.unit_name)} ${l(t,e.level)}</div>
    <div class="brief-row__meta">${s(t.t.cases)}: <b>${a(e.q50)}</b> (${a(e.q10)}–${a(e.q90)}) · ${s(t.t.peak)} ${n(e.peak_week,!1)}</div></div>
    <div class="brief-row__next"><b>${s(r)}:</b> ${s(i)}<div class="brief-row__meta">${s(t.t.prepare.replace(`{n}`,a(e.cases_high)))}</div></div></div>`}export{v as render};