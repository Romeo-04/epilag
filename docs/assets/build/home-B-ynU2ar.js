import{r as e,t}from"./voxel-BfSZQAZg.js";import{c as n,f as r,i,r as a,s as o,t as s}from"./logic-rqKjkrBE.js";import{d as c,f as ee,h as l,i as u,l as te,m as ne,n as d,o as f,r as re,s as p,t as m,u as h}from"./ui-B6vaxqwQ.js";var g=[[`props`,`cloud`],[`mosquito`,`fly1`],[`props`,`residents`],[`props`,`hospital`]];async function _(r,_){let{t:S,labels:C,lang:ae,i18n:w,fc:T,fcH:E,horizon:D,mode:O,panel:k,area:A,regionMeta:j}=_,M=Math.max(...E.map(e=>e.week)),N=Math.max(...E.map(e=>e.target_week)),P=e=>E.filter(t=>t.level===e).length,F=P(s[3]),I=P(s[2]),L=P(s[1]),R=i(T,E),z=R.filter(e=>e.level===s[2]||e.level===s[3]).slice(0,4),B=z.length?z:R.filter(e=>e.level===s[1]).slice(0,3),V=[...R].sort((e,t)=>t.q50_per100k-e.q50_per100k).slice(0,6),H=O===`replay`?y(S,D,E):F+I===0?b(S):``,U=()=>te(`epilag_action_brief.md`,a(B,{t:S,lang:ae,i18n:w,panelLabel:_.panelLabel,horizon:D,asOf:M}),`text/markdown`);r.innerHTML=`
    ${ee(S.hello,`${D} ${S.weeks_ahead}`,`${S.as_of} ${n(M)} · ${S.for_week} ${n(N)} · ${_.panelLabel}`)}

    <section class="card status-strip" aria-labelledby="home-act-title">
      <div class="status-strip__lead"><span class="home-eyebrow" id="home-act-title">${c(S.act_now)}</span><div class="status-strip__total">${p(F+I)}<span>${c(C.top_areas)}</span></div></div>
      <div class="status-strip__levels" aria-label="${c(S.act_now)}">
        ${v(s[3],`warning`,F,S)}${v(s[2],`watch`,I,S)}${v(s[1],`above`,L,S)}
      </div>
      <div class="status-strip__message">${H}</div>
      <a class="btn btn--primary btn--sm status-strip__action" href="?page=map" data-go="map">${c(S.open_map)} <i data-icon="arrowRight" data-size="18"></i></a>
    </section>

    <div class="overview-grid" aria-label="${c(S.nav_map)}">
      <section class="card overview-map">
        ${f(`forecastMap`,S.nav_map,`${S.for_week} ${n(N)}`)}
        <div class="home-map" id="home-map" role="img" aria-label="${c(`${S.nav_map}, ${S.for_week} ${n(N)}`)}"><div class="home-map__tip" id="home-map-tip" hidden></div></div>
        <div class="map-footer"><ul class="home-legend">${s.map(e=>`<li data-lv="${m[e]}"><span class="sq sq--round"></span>${c(_.levelName(e))}</li>`).join(``)}</ul>
          <a class="inline-link" href="?page=map" data-go="map">${c(S.open_map)} <i data-icon="arrowRight" data-size="18"></i></a></div>
      </section>

      <aside class="card overview-priority">
        ${f(`alert`,S.rank,S.rank_sub)}
        ${V.length?`<ol class="priority-list" id="home-priority">${V.map((e,t)=>x(e,t,_)).join(``)}</ol>`:`<div class="empty-state"><span class="empty-state__icon"><i data-icon="check" data-size="20"></i></span><div>${c(S.brief_empty)}</div></div>`}
        <div class="priority-list__footer"><a class="inline-link" href="?page=map" data-go="map">${c(C.all_areas)} <i data-icon="arrowRight" data-size="18"></i></a></div>
      </aside>
    </div>

    <section class="card brief-card">
      ${f(`actionPlan`,S.brief_head,S.brief_sub)}
      ${z.length?``:`<div class="callout">${c(S.brief_empty)}</div>`}
      <div class="brief-list">${B.map(e=>ie(e,_)).join(``)}</div>
      ${B.length?`<div class="brief-footer">${h(`dl-brief`,S.download_brief)}</div>`:``}
    </section>

    <section class="card weeks-card">
      ${f(`alert`,S.story_head)}
      <ol class="weeks-rail">${S.story.map(([e,t],n)=>`<li class="weeks-step${n===0?` weeks-step--on`:``}"><span class="weeks-step__art"><pixel-sprite sprite="${g[n][0]}" pose="${g[n][1]}" scale="${g[n][0]===`props`?1:2}"></pixel-sprite></span><span class="weeks-step__copy"><b>${c(e)}</b><span>${c(t)}</span></span></li>`).join(``)}</ol>
      ${ne(C.about_this,`<p>${c(S.story_note)}</p>`)}
    </section>

    <section class="card drill-card">
      <div><div class="kicker">${c(C.drill)}</div><h2>${c(S.drill_head)}</h2><p>${c(S.drill_sub)}</p></div>
      <a class="btn btn--light btn--sm" href="../drill/"><i data-icon="play" data-size="18"></i>${c(S.drill_btn)}</a>
    </section>`,r.querySelectorAll(`[data-go]`).forEach(e=>e.addEventListener(`click`,t=>{t.ctrlKey||t.metaKey||t.shiftKey||t.altKey||(t.preventDefault(),_.go(e.dataset.go,e.dataset.u?{area:e.dataset.u}:{}))})),r.querySelector(`#story-btn`)?.addEventListener(`click`,()=>_.set({panel:`province`,mode:`replay`,region:null,area:null})),r.querySelector(`#dl-brief`)?.addEventListener(`click`,U),_.topDownload(S.download_brief,U);let W=r.querySelector(`#home-map`),G=r.querySelector(`#home-map-tip`),K=k===`province`&&j?await e(`voxel_regions`):await e(`voxel_ph`),q=k===`province`&&j?K[j.psgc]:k===`province`?K.province:K.region,J=new Map(E.map(e=>[e.unit_id,e])),Y=await t(W,{grid:q,pixel:matchMedia(`(max-width: 680px)`).matches?2:3,markers:k!==`province`,onHover(e,t){let n=e&&J.get(e);if(Y.highlight(e),!n){G.hidden=!0;return}let r=W.getBoundingClientRect();G.innerHTML=`<b>${c(n.unit_name)}</b>${l(_,n.level)}<span>${o(n.q50)} (${o(n.q10)}–${o(n.q90)})</span>`,G.hidden=!1,G.style.left=`${Math.max(8,Math.min(t.clientX-r.left+14,r.width-190))}px`,G.style.top=`${Math.max(8,Math.min(t.clientY-r.top+14,r.height-88))}px`},onPick(e){e&&J.has(e)&&_.go(`unit`,{area:e})}});Y.setValues(Object.fromEntries(Y.units.map(e=>{let t=J.get(e);return[e,t?{color:d[t.level],height:re[t.level]}:{color:u,height:1}]})),{duration:520}),Y.highlight(A);let X=()=>{G.hidden=!0,Y.highlight(A)};W.addEventListener(`pointerleave`,X);let Z=r.querySelector(`#home-priority`),Q=e=>Y.highlight(e.target.closest(`[data-u]`)?.dataset.u??null),$=()=>Y.highlight(A);return Z?.addEventListener(`pointerover`,Q),Z?.addEventListener(`pointerleave`,$),Z?.addEventListener(`focusin`,Q),Z?.addEventListener(`focusout`,$),()=>{W.removeEventListener(`pointerleave`,X),Z?.removeEventListener(`pointerover`,Q),Z?.removeEventListener(`pointerleave`,$),Z?.removeEventListener(`focusin`,Q),Z?.removeEventListener(`focusout`,$),Y.dispose()}}function v(e,t,n,r){return`<div class="status-level" data-lv="${m[e]}"><span class="sq sq--round"></span><span class="status-level__copy"><b class="nums">${p(n)}</b><span>${c(r[`${t}_n`])}</span></span></div>`}function y(e,t,n){let i=r(n);return`<div class="status-message__title">${c(e.then)}</div><p><b>${i.flagged} ${c(e.of)} ${i.crossed}</b> ${c(e.then_line.replace(`{h}`,t))}</p>`}function b(e){return`<div class="status-message__title">${c(e.quiet)}</div><p>${c(e.brief_empty)}</p><button type="button" class="btn btn--ghost btn--sm" id="story-btn">${c(e.replay_story)}</button>`}function x(e,t,r){return`<li><a class="priority-row" href="?page=unit&area=${encodeURIComponent(e.unit_id)}" data-u="${c(e.unit_id)}" data-go="unit" aria-label="${c(`${e.unit_name}, ${r.levelName(e.level)}`)}">
    <span class="priority-row__rank">${t+1}</span><span class="priority-row__copy"><b>${c(e.unit_name)}</b><small>${c(r.t.cases)}: ${o(e.q50)} (${o(e.q10)}–${o(e.q90)})</small><small>${c(r.t.peak)} ${n(e.peak_week,!1)}</small></span>
    <span class="priority-row__level">${l(r,e.level)}<small>${e.q50_per100k.toFixed(1)} ${c(r.t.per100k)}</small></span></a></li>`}function ie(e,t){let[r,i]=t.i18n.PLAYBOOK[t.lang][e.level][0];return`<div class="brief-row" data-lv="${m[e.level]}"><div><div class="brief-row__name">${c(e.unit_name)} ${l(t,e.level)}</div>
    <div class="brief-row__meta">${c(t.t.cases)}: <b>${o(e.q50)}</b> (${o(e.q10)}–${o(e.q90)}) · ${c(t.t.peak)} ${n(e.peak_week,!1)}</div></div>
    <div class="brief-row__next"><b>${c(r)}:</b> ${c(i)}<div class="brief-row__meta">${c(t.t.prepare.replace(`{n}`,o(e.cases_high)))}</div></div></div>`}export{_ as render};