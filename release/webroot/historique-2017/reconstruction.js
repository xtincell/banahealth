/* Autonomous interactions. No WordPress, legacy plugin code, analytics or storage. */
(() => {
  'use strict';
  const language = document.documentElement.lang;
  const siteBase = document.documentElement.dataset.siteBase || '/';
  const localPath = '/' + location.pathname.slice(siteBase.length);
  const oldLanguage = new URLSearchParams(location.search).get('lang');
  if (oldLanguage === 'fr' && !localPath.startsWith('/fr/')) {
    location.replace(siteBase + 'fr' + localPath + location.hash); return;
  }
  if (oldLanguage === 'en' && localPath.startsWith('/fr/')) {
    location.replace(siteBase + localPath.slice(4) + location.hash); return;
  }
  document.documentElement.classList.add('reconstruction-js');
  const menu = document.querySelector('#site-navigation');
  const menuButton = document.querySelector('.menu-toggle');
  const closeMenu = () => { menu?.classList.remove('is-open'); menuButton?.setAttribute('aria-expanded', 'false'); };
  menuButton?.addEventListener('click', () => {
    const opened = menu.classList.toggle('is-open'); menuButton.setAttribute('aria-expanded', String(opened));
  });
  document.querySelectorAll('.submenu-trigger').forEach(button => {
    button.addEventListener('click', () => {
      const opened = button.parentElement.classList.toggle('submenu-open'); button.setAttribute('aria-expanded', String(opened));
    });
    button.parentElement.addEventListener('mouseenter',()=>{
      if(matchMedia('(min-width:1001px) and (hover:hover)').matches){button.parentElement.classList.add('submenu-open');button.setAttribute('aria-expanded','true');}
    });
    button.parentElement.addEventListener('mouseleave',()=>{
      if(matchMedia('(min-width:1001px) and (hover:hover)').matches&&!button.parentElement.contains(document.activeElement)){button.parentElement.classList.remove('submenu-open');button.setAttribute('aria-expanded','false');}
    });
  });
  document.addEventListener('keydown', e => {
    if (e.key === 'Escape') {
      closeMenu();
      document.querySelectorAll('.submenu-open').forEach(li => { li.classList.remove('submenu-open'); li.querySelector('button')?.setAttribute('aria-expanded', 'false'); });
      if (document.activeElement?.closest('#site-navigation')) menuButton?.focus();
    }
  });
  const reduced = matchMedia('(prefers-reduced-motion: reduce)');
  document.querySelectorAll('[data-rebuilt-slider]').forEach(slider => {
    const slides = [...slider.querySelectorAll(':scope > .slidedItem')];
    if (slides.length < 2) return;
    let index = 0, paused = reduced.matches, timer, pointerInside = false;
    const controls = document.createElement('div'); controls.className = 'slider-controls';
    const button = (label, text, action) => {
      const b = document.createElement('button'); b.type='button';b.setAttribute('aria-label',label);b.textContent=text;b.addEventListener('click',action);controls.append(b);return b;
    };
    const show = n => {
      index = (n + slides.length) % slides.length;
      slides.forEach((s,i) => { const active=i===index;s.classList.toggle('is-active',active);s.inert=!active;s.setAttribute('aria-hidden',String(!active)); });
      dots.forEach((b,i) => b.setAttribute('aria-current',String(i===index)));
    };
    button(language==='fr'?'Précédent':'Previous', '‹', () => show(index-1));
    const dots=slides.map((s,i) => button((language==='fr'?'Diapositive ':'Slide ')+(i+1),String(i+1),()=>show(i)));
    button(language==='fr'?'Suivant':'Next','›',()=>show(index+1));
    const pause=button('Pause','Ⅱ',()=>{paused=!paused;pause.textContent=paused?'▶':'Ⅱ';pause.setAttribute('aria-label',paused?(language==='fr'?'Reprendre':'Resume'):'Pause');pause.setAttribute('aria-pressed',String(paused));schedule();});
    const schedule=()=>{clearInterval(timer);if(!paused&&!reduced.matches&&!document.hidden&&!pointerInside&&!slider.contains(document.activeElement)) timer=setInterval(()=>show(index+1),5000);};
    slider.addEventListener('mouseenter',()=>{pointerInside=true;schedule();});
    slider.addEventListener('mouseleave',()=>{pointerInside=false;schedule();});
    slider.addEventListener('focusin',schedule);slider.addEventListener('focusout',()=>setTimeout(schedule,0));
    document.addEventListener('visibilitychange',schedule);reduced.addEventListener('change',schedule);
    slider.append(controls);show(0);schedule();
  });
  document.querySelectorAll('[data-contact-form]').forEach(form => {
    form.addEventListener('submit',event=>{
      event.preventDefault();if(!form.reportValidity())return;
      const values=[...new FormData(form)].filter(([key,value])=>!key.startsWith('_')&&typeof value==='string'&&value.trim());
      const body=values.map(([key,value])=>key+': '+value).join('\n\n');
      const subject=language==='fr'?'Demande de contact BanaHealth':'BanaHealth contact enquiry';
      location.href='mailto:hello@banahealth.care?subject='+encodeURIComponent(subject)+'&body='+encodeURIComponent(body);
    });
  });
  const dialog=document.createElement('dialog');dialog.className='gallery-dialog';dialog.setAttribute('aria-label',language==='fr'?'Photographie agrandie':'Enlarged photograph');
  const picture=document.createElement('img');const close=document.createElement('button');close.type='button';close.textContent='×';close.setAttribute('aria-label',language==='fr'?'Fermer':'Close');
  dialog.append(picture,close);document.body.append(dialog);close.addEventListener('click',()=>dialog.close());
  dialog.addEventListener('click',e=>{if(e.target===dialog)dialog.close();});
  document.querySelectorAll('a[data-gallery]').forEach(a=>a.addEventListener('click',e=>{e.preventDefault();picture.src=a.href;picture.alt=a.querySelector('img')?.alt||'';dialog.showModal();}));
})();
