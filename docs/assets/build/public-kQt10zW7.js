import{c as e}from"./logic-B3QEs7v5.js";import{a as t,d as n,f as r,m as i,o as a,t as o}from"./ui-Bz91oxhK.js";var s={drop:[`props`,`container`],shirt:[`props`,`people`],hospital:[`props`,`clinicBag`],bug:[`mosquito`,`sleepy`]},c={"outbreak warning":[`mosquito`,`alert`],watch:[`mosquito`,`search`],"above usual":[`frog`,`watch`],normal:[`frog`,`happy`]};function l(l,u){let{t:d,lang:f,i18n:p,fcH:m,horizon:h}=u,g=p.PUBLIC[f],_=[...m].sort((e,t)=>e.unit_name.localeCompare(t.unit_name)),v=_.some(e=>e.unit_id===u.area)?u.area:_[0].unit_id,y=m.find(e=>e.unit_id===v),b=g.status[y.level].replace(`{area}`,y.unit_name).replace(`{h}`,h),x=g.msg.replace(`{area}`,y.unit_name).replace(`{week}`,e(y.target_week)).replace(`{status}`,b),[S,C]=c[y.level];l.innerHTML=`
    ${r(g.head,g.muted,g.sub)}
    <div class="unit-pick">${t(`area`,g.pick,_,v)}</div>
    <div class="grid grid--public">
      <section class="hero-card hero-card--public surface tone-night tx-rain" data-lv="${o[y.level]}">
        <div class="kicker">${n(y.unit_name)} · ${n(d.for_week)} ${e(y.target_week)}</div>
        <div>${i(u,y.level)}</div>
        <p class="hero-card__status">${n(b)}</p>
        <pixel-sprite class="hero-card__sprite hero-card__sprite--big" sprite="${S}" pose="${C}" scale="${S===`frog`?4:5}"></pixel-sprite>
      </section>
      <section class="card">${a(`alert`,g.signs_head)}
        <ul class="signs">${g.signs.map(e=>`<li><span class="sq sq--round" data-lv="warning"></span>${n(e)}</li>`).join(``)}</ul></section>
    </div>
    <h2 class="vsub">${n(g.do_head)}</h2>
    <div class="grid grid--4">${g.do.map(([e,t,r])=>`<section class="card feat feat--plain">
      <span class="feat__ic"><pixel-sprite sprite="${s[e][0]}" pose="${s[e][1]}" scale="${s[e][0]===`props`?1:2}"></pixel-sprite></span>
      <h3>${n(t)}</h3><p>${n(r)}</p></section>`).join(``)}</div>
    <section class="card">${a(`residents`,g.share_head,g.note)}
      <div class="share"><p id="msg">${n(x)}</p><button type="button" class="btn btn--primary btn--sm" id="copy">${f===`fil`?`Kopyahin`:`Copy message`}</button></div></section>`,l.querySelector(`#area`).addEventListener(`change`,e=>u.set({area:e.target.value},{push:!1})),l.querySelector(`#copy`).addEventListener(`click`,async e=>{let t=e.currentTarget;try{await navigator.clipboard.writeText(x),t.textContent=f===`fil`?`Nakopya`:`Copied`}catch{getSelection().selectAllChildren(l.querySelector(`#msg`))}})}export{l as render};