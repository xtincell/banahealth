# Maintenance du site classique — 28 octobre 2026

## Perimetre

La presentation classique reste la version publique. Le lien de decouverte
a ete retire des deux accueils. L'apercu `/nouveau/` est conserve sans modification,
avec sa directive noindex ; il n'a pas ete inverse avec le site principal.

Les contenus editoriaux, photos, logo et six fichiers de signature email sont
conserves. Aucune reecriture, traduction, mise a jour des affirmations medicales
ou migration de framework ne fait partie de cette intervention.

## Corrections publiees

- Recuperation des anciennes entrees `/index.php`, `/wordpress/index.php` et
  des selecteurs `?lang=en` / `?lang=fr` avec leur destination bilingue.
- Canonicalisation HTTPS et www ; les images de signature restent accessibles
  directement sur les deux domaines, sans redirection supplementaire en HTTPS.
- Scripts executables et fichiers sensibles toujours interdits, y compris
  leurs extensions en majuscules. Les seules exceptions index.php sont des
  redirections : aucun fichier PHP n'est execute.
- Mise en cache OVH retablie par le passage de development a production.
  Pare-feu conserve. HTML revalide, scripts non empreintes a cache court,
  fichiers empreintes et polices a cache long.
- Mulish hebergee localement avec sa licence, sans requete Google Fonts.
- Menu mobile ferme exclu de la navigation clavier ; focus visible et fermeture
  avec Echap ; defilement possible sur les ecrans de faible hauteur.
- Pause du diaporama, cibles tactiles de 44 px, un seul H1, diapositives
  inactives inaccessibles au focus et suspension pendant l'interaction.
  Les trois messages restent lisibles sans JavaScript ; mouvement reduit respecte.
- Dependances corrigees sans changement d'Astro : notamment Vite 8.3.5,
  undici 8.12.3 et Zod 4.6.7.

## Preuves obtenues

| Controle | Resultat |
| --- | --- |
| Compilation et verification Legacy | Reussite ; 69 routes locales dont 34 Legacy non publiees |
| Site principal | 35 pages, dont 404, verifiees |
| References internes locales | 1 244 references presentes |
| Fidelite du contenu principal | Comparaison du texte editorial normalise : identique sur 35 pages |
| Signatures email | Six fichiers identiques octet pour octet, localement et sur le site public |
| Redirections Apache | 49 cas passes localement puis sur le domaine public |
| Fichiers interdits | Six cas 403 passes ; page inconnue en 404 |
| Publication | 45 fichiers remplaces/ajoutes, sans supprimer les anciens assets |
| Controle public des fichiers | 44 fichiers de publication et six signatures verifies par SHA-256 ; configuration relue par SFTP |
| Audit npm de production | Aucune vulnerabilite signalee apres correction |
| Navigateur Chromium | Sept pages a 390, 768 et 1440 px : aucun debordement horizontal ni image cassee detectee |
| Interactions | Menu clavier/Echap, pause, hauteur stable entre diapositives et acces sans JavaScript testes |
| Console | Aucune erreur ou alerte relevee sur les parcours testes |

Ces controles ne constituent pas un audit exhaustif WCAG, un test sur tous les
appareils physiques, une mesure Lighthouse ni une validation editoriale medicale.

## Acces regional : point restant

Les certificats TLS des deux domaines sont valides lors du controle. Le DNS
resout en IPv4 et IPv6. Des requetes HTTPS reussissent depuis Johannesburg,
Durban, Le Cap et la France.

Toutefois, une sonde du reseau Internet Magnate a Pretoria echoue a etablir la
connexion TCP vers l'IPv4 OVH, sur deux series. Depuis cette meme sonde, le site
temoin globalping.io repond. Un premier echec a Johannesburg n'a pas ete
reproduit lors des deux series suivantes. La sonde du Cap devient ensuite hors
ligne, y compris pour le temoin : ce cas ne doit pas etre attribue a BanaHealth.

Cela montre une anomalie d'acces dependante du reseau, sans identifier a elle
seule sa cause ni etablir qu'il s'agit du probleme de la cliente. Une erreur
avant HTTP ne se corrige pas dans les styles ou les redirections du site.
Les journaux et le diagnostic reseau OVH restent necessaires pour conclure.

Contre-verification apres publication, mesure `2CQasveAAeD2z3YxT00021OqW` :
quatre reponses HTTP 200 (trois reseaux de Johannesburg et un de Durban),
nouvel echec TCP a Pretoria et sonde du Cap hors ligne. Le point reseau reste
donc ouvert apres les corrections du site ; aucune resolution universelle
ni validation sur l'appareil de la cliente n'est revendiquee.

Le 403 obtenu avec certaines signatures de robots (curl/Wget) est distinct :
les navigateurs usuels, Office et Googlebot ont repondu 200 dans les tests.
Le pare-feu n'a pas ete desactive sur la seule base de ce resultat.

Mesures ponctuelles Globalping utilisees : `2y0gwGiNlDw0QVwjp00021Oq1`,
`2L4uJBDYfOwZStoB300021Oq3`, `23HJ1jvekkcttOWYC00021OqD`,
`2R41yjfjvMGhkAndS00021OqJ`. Temoin : `2AR8cOSA9t7NVOem900021OqD`
et `2G7fo1RvsJPKVdzJc00021OqJ`.

La [page de statut OVH](https://web-cloud.status-ovhcloud.com/) indique aussi
des incidents sur certains serveurs du cluster120 le 26 octobre, declares
resolus le meme jour. Cela ne prouve ni que BanaHealth etait sur ces serveurs
precis, ni que ces incidents expliquent les echecs observes le 28 octobre.

## Sauvegarde et restauration

Sauvegarde complete du site public et des configurations avant intervention,
conservee hors depot. Les fichiers ont ete envoyes vers un nom temporaire puis
renommes ; assets avant pages, configuration en dernier. Les signatures et
`/nouveau/` ont ete exclus de l'envoi.

Le dossier prive de maintenance contient le manifeste SHA-256 et le lot
`rollback-classic.sftp`. Celui-ci restaure les fichiers anterieurs modifies ;
les nouveaux assets non references peuvent rester en place sans incidence.
Restaurer aussi `.ovhconfig` depuis `ovhconfig-before` pour annuler le changement
de cache OVH. Ne jamais publier ce dossier prive sur GitHub.
