import{_ as e,c as t,f as n,s as r,t as i}from"./logic-B3QEs7v5.js";import{n as a,t as o}from"./voxel-Ct3on7rc.js";import{c as s,d as c,f as l,g as u,i as d,l as f,m as p,n as m,o as h,r as g,s as _,t as v,u as y}from"./ui-Bz91oxhK.js";async function b(b,x){let{t:S,fc:C,fcH:w,horizon:T,mode:E,panel:D}=x,O=Math.max(...w.map(e=>e.target_week)),k=Math.max(...w.map(e=>e.week)),A=[...w].sort((e,t)=>t.q50_per100k-e.q50_per100k),j=A.slice(0,12),M=Math.max(A[0]?.q50_per100k??0,1e-9),N=e=>w.filter(t=>t.level===e).length,P=E===`replay`?n(w):null;b.innerHTML=`
    ${l(S.nav_map,`${T} ${S.weeks_ahead}`,`${S.as_of} ${t(k)} · ${S.for_week} ${t(O)}`)}
    ${P?`<section class="hero-card hero-card--wide surface tone-night tx-rain">
      <div class="kicker">${c(S.replay_banner)} · ${c(S.result)}</div>
      <div class="replay-result hero-card__mid" data-crossed="${P.crossed}" data-flagged="${P.flagged}">${_(P.flagged)}&nbsp;${c(S.of)} ${P.crossed}</div>
      <p>${c(S.hits)}: ${P.crossed} · ${P.flagged} ${c(S.caught)}.</p><p class="small">${c(S.replay_note)}</p>
      <pixel-sprite class="hero-card__sprite" sprite="mosquito" pose="check" scale="4"></pixel-sprite></section>`:``}
    <div class="grid grid--4 kpis">${[[`outbreak warning`,`warning`],[`watch`,`watch`],[`above usual`,`above`],[`normal`,`normal`]].map(([e,t])=>`
      <div class="card kpi" data-lv="${v[e]}"><div class="kpi__lab"><span class="sq sq--round${e===i[3]&&N(e)?` lv--pulse`:``}"></span>${c(S[`${t}_n`])}</div>
        <div class="kpi__val">${_(N(e))}</div><div class="kpi__desc">${c(S[`${t}_d`])}</div></div>`).join(``)}</div>
    <div class="grid grid--map">
      <section class="card">
        ${h(`forecastMap`,S.nav_map,`${S.for_week} ${t(O)}`)}
        <div class="vmap" id="vmap" role="img" aria-label="${c(`${S.nav_map}: 3D map, column height and colour show the alert level`)}">
          <div class="vmap__tip" id="vmap-tip" hidden></div></div>
        <ul class="legend legend--row">${i.map(e=>`<li data-lv="${v[e]}"><span class="sq sq--round"></span>${c(x.levelName(e))}</li>`).join(``)}</ul>
      </section>
      <section class="card">
        ${h(`alert`,S.rank,S.rank_sub)}
        <ol class="rank" id="rank">${j.map((e,t)=>{let n=`${r(e.q50)} (${r(e.q10)}–${r(e.q90)})`;return E===`replay`&&e.actual!=null&&(n+=` → ${r(e.actual)}`),`<li><a class="rank__row" href="?page=unit&area=${encodeURIComponent(e.unit_id)}" data-u="${c(e.unit_id)}">
            <span class="rank__rk">${t+1}</span><span class="rank__nm">${c(e.unit_name)}<small>${n}</small></span>${p(x,e.level)}
            <span class="rank__bar" data-lv="${v[e.level]}"><i style="width:${(e.q50_per100k/M*100).toFixed(0)}%"></i></span>
            <span class="rank__num nums">${e.q50_per100k.toFixed(1)}</span></a></li>`}).join(``)}</ol>
      </section>
    </div>
    ${s(S.all_areas,`${u(A,[[S.area,e=>c(e.unit_name)],[S.level,e=>p(x,e.level)],[S.cases,e=>r(e.q50),`num`],[S.range,e=>`${r(e.q10)}–${r(e.q90)}`,`num`],[S.per100k,e=>e.q50_per100k.toFixed(1),`num`],...E===`replay`?[[S.actual_col,e=>`${r(e.actual)} · ${c(x.levelName(e.actual_level))}`]]:[]])}
      <div class="btn-row">${y(`dl-all`,S.download_all)}</div><p class="small muted">${c(S.open_data)}</p>`)}`,b.querySelectorAll(`a[data-u]`).forEach(e=>e.addEventListener(`click`,t=>{t.ctrlKey||t.metaKey||(t.preventDefault(),x.go(`unit`,{area:e.dataset.u}))})),b.querySelector(`#dl-all`).addEventListener(`click`,()=>{let t=Object.keys(C[0]).filter(e=>![`test_year`].includes(e));f(`epilag_forecast_${D}_${E}.csv`,e(C,t.map(e=>[e,t=>e.includes(`week`)?new Date(t[e]*864e5).toISOString().slice(0,10):t[e]])),`text/csv`)});let F=b.querySelector(`#vmap`),I=b.querySelector(`#vmap-tip`),L=await a(`voxel_ph`),R=D===`province`?L.province:L.region,z=new Map(w.map(e=>[e.unit_id,e])),B=await o(F,{grid:R,pixel:matchMedia(`(max-width: 680px)`).matches?2:3,markers:D!==`province`,onHover(e,t){let n=e&&z.get(e);if(B?.highlight(e),!n){I.hidden=!0;return}let i=F.getBoundingClientRect();I.innerHTML=`<b>${c(n.unit_name)}</b>${p(x,n.level)}<span>${r(n.q50)} (${r(n.q10)}–${r(n.q90)})</span>`,I.hidden=!1,I.style.left=`${Math.min(t.clientX-i.left+14,i.width-200)}px`,I.style.top=`${t.clientY-i.top+14}px`},onPick(e){e&&z.has(e)&&x.go(`unit`,{area:e})}});return B.setValues(Object.fromEntries(B.units.map(e=>{let t=z.get(e);return[e,t?{color:m[t.level],height:g[t.level]}:{color:d,height:1}]})),{duration:800}),F.addEventListener(`pointerleave`,()=>{I.hidden=!0,B.highlight(null)}),b.querySelector(`#rank`).addEventListener(`pointerover`,e=>B.highlight(e.target.closest(`[data-u]`)?.dataset.u??null)),b.querySelector(`#rank`).addEventListener(`pointerleave`,()=>B.highlight(null)),()=>B.dispose()}export{b as render};