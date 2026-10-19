import{t as e}from"./data-DbYTdCf-.js";import{c as t,d as n,f as r,g as i,o as a,s as o,t as s}from"./ui-Bz91oxhK.js";import{t as c}from"./chart-C5l-ZFvK.js";async function l(l,u){let{t:d,lang:f,i18n:p,fc:m,horizon:h,panel:g}=u;if(g!==`region_qc`){l.innerHTML=`${r(d.qc_head,d.qc_muted,d.qc_note)}
      <section class="card"><div class="callout"><i data-icon="info" data-size="24"></i>${n(d.switch_qc)}</div>
      <div class="btn-row"><button type="button" class="btn btn--primary btn--sm" id="switch">${n(d.switch_btn)}</button></div></section>`,l.querySelector(`#switch`).addEventListener(`click`,()=>u.set({panel:`region_qc`}));return}let _=m.filter(e=>e.unit_id===`QC`).sort((e,t)=>e.horizon-t.horizon),v=_.reduce((e,t)=>e+t.q50,0)/_.length*8,y=_.find(e=>e.horizon===h).level,b=(await e()).map(e=>({...e,expected_8wk:e.share*v})),x=b.slice(0,5);l.innerHTML=`
    ${r(d.qc_head,d.qc_muted,d.qc_note)}
    <div class="grid grid--qc">
      <div class="stack">
        <section class="hero-card surface tone-night tx-rain" data-lv="${s[y]}">
          <div class="kicker">${n(d.city_fc)}</div><div class="hero-card__big">${o(v)}</div>
          <div class="chips"><span class="chip chip--night"><span class="sq sq--round"></span>${n(u.levelName(y))}</span></div>
          <p>${n(p.ALERT_TEXT[f][y])}</p>
          <pixel-sprite class="hero-card__sprite" sprite="props" pose="school" scale="2"></pixel-sprite>
        </section>
        <section class="card">${a(`barangay`,`Top 5`)}
          <ol class="rank">${x.map((e,t)=>`<li><div class="rank__row rank__row--3"><span class="rank__rk">${t+1}</span>
            <span class="rank__nm">${n(e.Barangay)}<small>${(e.share*100).toFixed(1)}% · ${Math.round(e.cases_2025).toLocaleString(`en-US`)} (2025)</small></span>
            <span class="rank__num nums">${Math.round(e.expected_8wk)}</span></div></li>`).join(``)}</ol></section>
      </div>
      <section class="card">${a(`forecastMap`,d.brgy_chart)}<div id="bchart" class="chart-box"></div></section>
    </div>
    ${t(d.all_areas,i(b,[[`Barangay`,e=>n(e.Barangay)],[`Cases 2022-2025`,e=>Math.round(e.cases_2022_2025).toLocaleString(`en-US`),`num`],[`Cases 2025`,e=>Math.round(e.cases_2025).toLocaleString(`en-US`),`num`],[`Share of city`,e=>`${(e.share*100).toFixed(1)}%`,`num`],[`Expected, next 8 weeks`,e=>e.expected_8wk.toFixed(1),`num`]]))}`;let S=b.slice(0,20);return c(l.querySelector(`#bchart`),{categories:S.map(e=>e.Barangay),horizontal:!0,height:560,fmt:e=>Math.round(e),groups:[{values:S.map(e=>e.expected_8wk),colors:S.map((e,t)=>`rgba(8,117,79,${(1-.65*t/19).toFixed(2)})`)}]})}export{l as render};