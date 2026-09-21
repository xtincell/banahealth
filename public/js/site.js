/**
 * banahealth.care — comportements de la page
 *
 * Servi comme fichier externe, et non integre au HTML : la politique
 * de securite du site refuse les scripts en ligne, et c'est voulu.
 *
 * Tout ce qui est ici est une amelioration progressive. Si ce fichier
 * ne se charge pas, le site reste entierement lisible : le contenu est
 * visible par defaut et le carrousel affiche sa premiere diapositive.
 */
(function () {
  'use strict';

  var reduit = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  // Signale que le script tourne : le CSS peut alors masquer le contenu
  // avant de le reveler. Sans cette classe, tout reste visible.
  if (!reduit) document.documentElement.classList.add('js-anim');

  // ---------- Revelation au defilement ----------
  function revelations() {
    var cibles = document.querySelectorAll('.reveler');
    if (reduit || !('IntersectionObserver' in window)) {
      for (var i = 0; i < cibles.length; i++) cibles[i].classList.add('vu');
      return;
    }
    var obs = new IntersectionObserver(
      function (entrees) {
        entrees.forEach(function (e) {
          if (e.isIntersecting) {
            e.target.classList.add('vu');
            obs.unobserve(e.target);
          }
        });
      },
      { rootMargin: '0px 0px -10% 0px', threshold: 0.05 }
    );
    for (var j = 0; j < cibles.length; j++) obs.observe(cibles[j]);
  }

  // ---------- Carrousel d'accueil ----------
  function carrousel() {
    var racine = document.querySelector('[data-diaporama]');
    if (!racine) return;

    var diapos = Array.prototype.slice.call(racine.querySelectorAll('[data-diapo]'));
    var puces = Array.prototype.slice.call(racine.querySelectorAll('[data-puce]'));
    if (diapos.length < 2) return;

    racine.classList.add('diaporama--actif');
    var index = 0;
    var minuteur = null;

    function afficher(n) {
      index = (n + diapos.length) % diapos.length;
      diapos.forEach(function (d, i) {
        var actif = i === index;
        d.classList.toggle('est-active', actif);
        if (actif) d.removeAttribute('aria-hidden');
        else d.setAttribute('aria-hidden', 'true');
      });
      puces.forEach(function (p, i) {
        p.classList.toggle('est-active', i === index);
        if (i === index) p.setAttribute('aria-current', 'true');
        else p.removeAttribute('aria-current');
      });
    }

    function demarrer() {
      if (reduit || minuteur) return;
      minuteur = setInterval(function () { afficher(index + 1); }, 6500);
    }
    function arreter() {
      if (minuteur) { clearInterval(minuteur); minuteur = null; }
    }
    function relancer() { arreter(); demarrer(); }

    var prec = racine.querySelector('[data-precedent]');
    var suiv = racine.querySelector('[data-suivant]');
    if (prec) prec.addEventListener('click', function () { afficher(index - 1); relancer(); });
    if (suiv) suiv.addEventListener('click', function () { afficher(index + 1); relancer(); });
    puces.forEach(function (p, i) {
      p.addEventListener('click', function () { afficher(i); relancer(); });
    });

    // On suspend pendant la lecture et quand l'onglet passe en arriere-plan
    racine.addEventListener('mouseenter', arreter);
    racine.addEventListener('mouseleave', demarrer);
    racine.addEventListener('focusin', arreter);
    racine.addEventListener('focusout', demarrer);
    document.addEventListener('visibilitychange', function () {
      if (document.hidden) arreter(); else demarrer();
    });

    afficher(0);
    demarrer();
  }

  function demarrage() {
    revelations();
    carrousel();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', demarrage);
  } else {
    demarrage();
  }
})();
