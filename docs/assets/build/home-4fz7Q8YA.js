import{c as e,f as t,i as n,r,s as i,t as a}from"./logic-B3QEs7v5.js";import{d as o,f as s,l as c,m as l,o as u,s as d,t as f,u as p}from"./ui-Bz91oxhK.js";var m={map:`forecastMap`,unit:`areaDetail`,budget:`actionPlan`,public:`residents`,qc:`barangay`,proof:`didItWork`},h=[[`props`,`cloud`],[`mosquito`,`fly1`],[`props`,`residents`],[`props`,`hospital`]];function g(g,v){let{t:y,lang:b,i18n:x,fc:S,fcH:C,horizon:w,mode:T}=v,E=Math.max(...C.map(e=>e.week)),D=Math.max(...C.map(e=>e.target_week)),O=e=>C.filter(t=>t.level===e).length,k=O(a[3]),A=O(a[2]),j=O(a[1]),M;if(T===`replay`){let e=t(C);M=`<div class="hero-card__then">${o(y.then)}</div>
      <div class="hero-card__claim"><b>${e.flagged} ${o(y.of)} ${e.crossed}</b> ${o(y.then_line.replace(`{h}`,w))}</div>`}else M=k+A===0?`<p class="hero-card__quiet">${o(y.quiet)}</p>
      <button type="button" class="btn btn--light btn--sm" id="story-btn">${o(y.replay_story)}</button>`:``;let N=n(S,C),P=N.filter(e=>e.level===a[2]||e.level===a[3]).slice(0,6),F=P.length?P:N.filter(e=>e.level===a[1]).slice(0,3);g.innerHTML=`
    ${s(y.hello,`${w} ${y.weeks_ahead}`,`${y.as_of} ${e(E)} · ${y.for_week} ${e(D)} · ${v.panelLabel}`)}
    <div class="grid grid--home">
      <section class="hero-card surface tone-night tx-rain">
        <div class="kicker">${o(y.act_now)}</div>
        <div class="hero-card__big">${d(k+A)}</div>
        <div class="chips">
          <span class="chip chip--night">${_(`outbreak warning`)}${k} ${o(y.warning_n)}</span>
          <span class="chip chip--night">${_(`watch`)}${A} ${o(y.watch_n)}</span>
          <span class="chip chip--night">${_(`above usual`)}${j} ${o(y.above_n)}</span>
        </div>
        ${M}
        <a class="btn btn--light btn--sm hero-card__go" href="?page=map" data-go="map">${o(y.open_map)} <i data-icon="arrowRight" data-size="24"></i></a>
        <pixel-sprite class="hero-card__sprite" sprite="mosquito" pose="${k?`alert`:A?`search`:`sleepy`}" scale="4"></pixel-sprite>
      </section>
      <section class="card">
        ${u(`alert`,y.story_head)}
        <ol class="story">${y.story.map(([e,t],n)=>`<li class="story__step${n===0?` story__step--on`:``}">
          <span class="story__art"><pixel-sprite sprite="${h[n][0]}" pose="${h[n][1]}" scale="${h[n][0]===`props`?1:2}"></pixel-sprite></span>
          <b>${o(e)}</b><span>${o(t)}</span></li>`).join(``)}</ol>
        <div class="callout story__note"><i data-icon="alert" data-size="24"></i>${o(y.story_note)}</div>
      </section>
    </div>

    <h2 class="vsub">${o(y.features_head)} <span>${o(y.features_sub)}</span></h2>
    <div class="grid grid--3 feats">${Object.keys(m).map(e=>{let[t,n,r]=x.FEATURES[b][e];return`<a class="card feat" href="?page=${e}" data-go="${e}">
        <span class="feat__ic"><i data-icon="${m[e]}" data-size="48"></i></span>
        <h3>${o(y[`nav_${e}`])}</h3>
        <dl><dt>${o(y.does)}</dt><dd>${o(t)}</dd><dt>${o(y.why_h)}</dt><dd>${o(n)}</dd><dt>${o(y.you)}</dt><dd class="feat__you">${o(r)}</dd></dl>
        <span class="feat__open">${o(y.open)} <i data-icon="arrowRight" data-size="24"></i></span></a>`}).join(``)}</div>

    <section class="drill-banner console">
      <div><div class="kicker">Dengue Drill</div><h2>${o(y.drill_head)}</h2><p>${o(y.drill_sub)}</p>
        <a class="btn btn--light btn--sm" href="../drill/"><i data-icon="play" data-size="24"></i>${o(y.drill_btn)}</a></div>
      <pixel-sprite sprite="frog" pose="watch" scale="4"></pixel-sprite>
    </section>

    <section class="card">
      ${u(`actionPlan`,y.brief_head,y.brief_sub)}
      ${P.length?``:`<div class="callout"><i data-icon="check" data-size="24"></i>${o(y.brief_empty)}</div>`}
      <div class="briefs">${F.map(t=>{let[n,r]=x.PLAYBOOK[b][t.level][0];return`<div class="brief-row" data-lv="${f[t.level]}"><div><div class="brief-row__nm">${o(t.unit_name)} ${l(v,t.level)}</div>
          <div class="brief-row__meta">${o(y.cases)}: <b>${i(t.q50)}</b> (${i(t.q10)}–${i(t.q90)}) · ${o(y.peak)} ${e(t.peak_week,!1)}</div></div>
          <div class="brief-row__next"><b>${o(n)}:</b> ${o(r)}<div class="brief-row__meta">${o(y.prepare.replace(`{n}`,i(t.cases_high)))}</div></div></div>`}).join(``)}</div>
      ${F.length?p(`dl-brief`,y.download_brief):``}
    </section>`,g.querySelectorAll(`[data-go]`).forEach(e=>e.addEventListener(`click`,t=>{t.ctrlKey||t.metaKey||(t.preventDefault(),v.go(e.dataset.go))})),g.querySelector(`#story-btn`)?.addEventListener(`click`,()=>v.set({panel:`province`,mode:`replay`})),g.querySelector(`#dl-brief`)?.addEventListener(`click`,()=>c(`epilag_action_brief.md`,r(F,{t:y,lang:b,i18n:x,panelLabel:v.panelLabel,horizon:w,asOf:E}),`text/markdown`))}var _=e=>`<span class="sq sq--round" data-lv="${f[e]}"></span>`;export{g as render};