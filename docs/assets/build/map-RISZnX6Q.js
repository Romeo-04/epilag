const __vite__mapDeps=(i,m=__vite__mapDeps,d=(m.f||(m.f=["assets/build/maplibre-map-BDoA_hjH.js","assets/build/rolldown-runtime-XKyaHtl9.js","assets/build/preload-helper-DgYTTzAH.js","assets/build/voxel-Cly2tmIt.js"])))=>i.map(i=>d[i]);
import{t as e}from"./preload-helper-DgYTTzAH.js";import{r as t,t as n}from"./voxel-Cly2tmIt.js";import{_ as r,c as i,f as a,s as o,t as s}from"./logic-rqKjkrBE.js";import{c,d as l,f as u,g as d,i as f,l as p,m,n as h,o as g,r as _,s as v,t as y,u as b}from"./ui-Bz91oxhK.js";async function x(x,S){let{t:C,fc:w,fcH:T,horizon:E,mode:D,panel:O}=S,k=Math.max(...T.map(e=>e.target_week)),A=Math.max(...T.map(e=>e.week)),j=[...T].sort((e,t)=>t.q50_per100k-e.q50_per100k),M=j.slice(0,12),N=Math.max(j[0]?.q50_per100k??0,1e-9),P=e=>T.filter(t=>t.level===e).length,F=D===`replay`?a(T):null;x.innerHTML=`
    ${u(C.nav_map,`${E} ${C.weeks_ahead}`,`${C.as_of} ${i(A)} · ${C.for_week} ${i(k)}`)}
    ${F?`<section class="hero-card hero-card--wide surface tone-night tx-rain">
      <div class="kicker">${l(C.replay_banner)} · ${l(C.result)}</div>
      <div class="replay-result hero-card__mid" data-crossed="${F.crossed}" data-flagged="${F.flagged}">${v(F.flagged)}&nbsp;${l(C.of)} ${F.crossed}</div>
      <p>${l(C.hits)}: ${F.crossed} · ${F.flagged} ${l(C.caught)}.</p><p class="small">${l(C.replay_note)}</p>
      <pixel-sprite class="hero-card__sprite" sprite="mosquito" pose="check" scale="4"></pixel-sprite></section>`:``}
    <div class="grid grid--4 kpis">${[[`outbreak warning`,`warning`],[`watch`,`watch`],[`above usual`,`above`],[`normal`,`normal`]].map(([e,t])=>`
      <div class="card kpi" data-lv="${y[e]}"><div class="kpi__lab"><span class="sq sq--round${e===s[3]&&P(e)?` lv--pulse`:``}"></span>${l(C[`${t}_n`])}</div>
        <div class="kpi__val">${v(P(e))}</div><div class="kpi__desc">${l(C[`${t}_d`])}</div></div>`).join(``)}</div>
    <div class="grid grid--map">
      <section class="card">
        ${g(`forecastMap`,C.nav_map,`${C.for_week} ${i(k)}`)}
        <div class="vmap" id="vmap" role="img" aria-label="${l(`${C.nav_map}: 3D map, column height and colour show the alert level`)}">
          <div class="vmap__tip" id="vmap-tip" hidden></div></div>
        <ul class="legend legend--row">${s.map(e=>`<li data-lv="${y[e]}"><span class="sq sq--round"></span>${l(S.levelName(e))}</li>`).join(``)}</ul>
      </section>
      <section class="card">
        ${g(`alert`,C.rank,C.rank_sub)}
        <ol class="rank" id="rank">${M.map((e,t)=>{let n=`${o(e.q50)} (${o(e.q10)}–${o(e.q90)})`;return D===`replay`&&e.actual!=null&&(n+=` → ${o(e.actual)}`),`<li><a class="rank__row" href="?page=unit&area=${encodeURIComponent(e.unit_id)}" data-u="${l(e.unit_id)}">
            <span class="rank__rk">${t+1}</span><span class="rank__nm">${l(e.unit_name)}<small>${n}</small></span>${m(S,e.level)}
            <span class="rank__bar" data-lv="${y[e.level]}"><i style="width:${(e.q50_per100k/N*100).toFixed(0)}%"></i></span>
            <span class="rank__num nums">${e.q50_per100k.toFixed(1)}</span></a></li>`}).join(``)}</ol>
      </section>
    </div>
    ${c(C.all_areas,`${d(j,[[C.area,e=>l(e.unit_name)],[C.level,e=>m(S,e.level)],[C.cases,e=>o(e.q50),`num`],[C.range,e=>`${o(e.q10)}–${o(e.q90)}`,`num`],[C.per100k,e=>e.q50_per100k.toFixed(1),`num`],...D===`replay`?[[C.actual_col,e=>`${o(e.actual)} · ${l(S.levelName(e.actual_level))}`]]:[]])}
      <div class="btn-row">${b(`dl-all`,C.download_all)}</div><p class="small muted">${l(C.open_data)}</p>`)}`,x.querySelectorAll(`a[data-u]`).forEach(e=>e.addEventListener(`click`,t=>{t.ctrlKey||t.metaKey||(t.preventDefault(),S.go(`unit`,{area:e.dataset.u}))})),x.querySelector(`#dl-all`).addEventListener(`click`,()=>{let e=Object.keys(w[0]).filter(e=>![`test_year`].includes(e));p(`epilag_forecast_${O}_${D}.csv`,r(w,e.map(e=>[e,t=>e.includes(`week`)?new Date(t[e]*864e5).toISOString().slice(0,10):t[e]])),`text/csv`)});let I=x.querySelector(`#vmap`),L=x.querySelector(`#vmap-tip`),R=await t(`voxel_ph`),z=O===`province`?R.province:R.region,B=new Map(T.map(e=>[e.unit_id,e])),V=await(S.map===`maplibre`?(await e(async()=>{let{createMaplibreMap:e}=await import(`./maplibre-map-BDoA_hjH.js`);return{createMaplibreMap:e}},__vite__mapDeps([0,1,2,3]))).createMaplibreMap:n)(I,{grid:z,pixel:matchMedia(`(max-width: 680px)`).matches?2:3,markers:O!==`province`,onHover(e,t){let n=e&&B.get(e);if(V?.highlight(e),!n){L.hidden=!0;return}let r=I.getBoundingClientRect();L.innerHTML=`<b>${l(n.unit_name)}</b>${m(S,n.level)}<span>${o(n.q50)} (${o(n.q10)}–${o(n.q90)})</span>`,L.hidden=!1,L.style.left=`${Math.min(t.clientX-r.left+14,r.width-200)}px`,L.style.top=`${t.clientY-r.top+14}px`},onPick(e){e&&B.has(e)&&S.go(`unit`,{area:e})}});return V.setValues(Object.fromEntries(V.units.map(e=>{let t=B.get(e);return[e,t?{color:h[t.level],height:_[t.level]}:{color:f,height:1}]})),{duration:800}),I.addEventListener(`pointerleave`,()=>{L.hidden=!0,V.highlight(null)}),x.querySelector(`#rank`).addEventListener(`pointerover`,e=>V.highlight(e.target.closest(`[data-u]`)?.dataset.u??null)),x.querySelector(`#rank`).addEventListener(`pointerleave`,()=>V.highlight(null)),()=>V.dispose()}export{x as render};