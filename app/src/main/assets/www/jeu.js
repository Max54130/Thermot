/* Thermot : jeu de proximité de sens. Interface, logique de partie, langues. */

const VERSION = "4.3.0";
const CLE = "thermot:v2:";
const ORIGINE = Date.UTC(2026, 0, 1);   // jour n° 1

const $ = (s) => document.querySelector(s);
const millier = (n) => String(n).replace(/\B(?=(\d{3})+(?!\d))/g, "\u00A0");

const el = {
  splash: $("#splash"), jauge: $("#splash-jauge"), etat: $("#splash-etat"),
  splashSous: $("#splash-sous"),
  appli: $("#appli"), mode: $("#entete-mode"), marques: $("#bande-marques"),
  aiguille: $("#aiguille"),
  essais: $("#resume-essais"), record: $("#resume-record"),
  liste: $("#liste"), vide: $("#vide"), champ: $("#champ"), saisie: $("#saisie"),
  message: $("#message"), voile: $("#voile"), panneau: $("#panneau-contenu")
};

let partie = null;
let langue = "fr";
let T = LANGUES.fr;          // textes de la langue courante
let timerMsg = null;

/* ------------------------------------------------------------------ stockage */

const lire = (cle, defaut) => {
  try { const v = localStorage.getItem(CLE + cle); return v ? JSON.parse(v) : defaut; }
  catch (e) { return defaut; }
};
const ecrire = (cle, val) => {
  try { localStorage.setItem(CLE + cle, JSON.stringify(val)); } catch (e) {}
};
const oublier = (cle) => {
  try { localStorage.removeItem(CLE + cle); } catch (e) {}
};

/* ------------------------------------------------------------------ langue */

/* Une variante monolingue n'embarque qu'un lexique : la langue y est imposée. */
const langueImposee = () =>
  (typeof window !== "undefined" && window.LANGUE_UNIQUE) || null;

function langueDuSysteme() {
  if (langueImposee()) return langueImposee();
  const dispo = CODES_LANGUE;
  for (const balise of navigator.languages || [navigator.language || "fr"]) {
    const code = String(balise).slice(0, 2).toLowerCase();
    if (dispo.includes(code)) return code;
  }
  return "fr";
}

function appliquerTextes() {
  T = LANGUES[langue] || LANGUES.fr;
  document.documentElement.lang = langue;
  $("#splash-sous").textContent = T.baseline;
  $("#legende-froid").textContent = T.glacial;
  $("#legende-tiede").textContent = T.tiede;
  $("#legende-chaud").textContent = T.brulant;
  el.champ.placeholder = T.placeholder;
  el.champ.setAttribute("aria-label", T.labelProposer);
  el.vide.textContent = T.consigne;
  $("#btn-menu").setAttribute("aria-label", T.labelMenu);
  $("#btn-stats").setAttribute("aria-label", T.labelStats);
  $("#btn-fermer").setAttribute("aria-label", T.labelFermer);
  $("#btn-langue").textContent = T.drapeau;
  $("#btn-langue").setAttribute("aria-label", T.aLangue);
}

/* ------------------------------------------------------------------ thème */

const THEMES = ["auto", "clair", "sombre"];

const ICONES = {
  auto: `<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="8"/>
         <path d="M12 4a8 8 0 010 16z" fill="currentColor" stroke="none"/></svg>`,
  clair: `<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="4.2"/>
          <path d="M12 2.5v2.2M12 19.3v2.2M4.2 4.2l1.6 1.6M18.2 18.2l1.6 1.6M2.5 12h2.2M19.3 12h2.2M4.2 19.8l1.6-1.6M18.2 5.8l1.6-1.6"/></svg>`,
  sombre: `<svg viewBox="0 0 24 24" aria-hidden="true">
           <path d="M20 14.5A8.5 8.5 0 019.5 4a8.5 8.5 0 1010.5 10.5z"/></svg>`
};

const systemeEstClair = () =>
  window.matchMedia && window.matchMedia("(prefers-color-scheme: light)").matches;

function appliquerTheme(choix) {
  const effectif = choix === "auto" ? (systemeEstClair() ? "clair" : "sombre") : choix;
  document.documentElement.dataset.theme = effectif;
  const bouton = $("#btn-theme");
  if (bouton) {
    bouton.innerHTML = ICONES[choix];
    bouton.setAttribute("aria-label", T.labelTheme[choix]);
  }
  if (window.Pont && Pont.theme) {
    try { Pont.theme(effectif === "clair"); } catch (e) {}
  }
}

/* Mode adulte : masque ou non les mots crus. Désactivé par défaut, pour que
   l'appli reste utilisable par des enfants sans réglage préalable. */
const adulteActif = () => lire("adulte", false) === true;

function appliquerFiltre() {
  Moteur.filtrer(!adulteActif());
}

function basculerAdulte() {
  const nouveau = !adulteActif();
  ecrire("adulte", nouveau);
  appliquerFiltre();
  /* le classement dépend du filtre : on le recalcule et on retire les essais
     qui viennent d'être masqués */
  partie.analyse = Moteur.analyser(partie.cible);
  partie.essais = partie.essais.filter(e => {
    const r = Moteur.resoudre(e.mot);
    return r && !r.bloque;
  });
  for (const e of partie.essais) {
    e.sim = partie.analyse.sims[e.i];
    e.rang = e.i === partie.cible ? 0 : (partie.analyse.rangs.get(e.i) || null);
  }
  sauver();
  fermerPanneau();
  dessinerTout();
  message(nouveau ? T.adulteOui : T.adulteNon);
}

const themeChoisi = () => {
  const v = lire("theme", "auto");
  return THEMES.includes(v) ? v : "auto";
};

function basculerTheme() {
  const suivant = THEMES[(THEMES.indexOf(themeChoisi()) + 1) % THEMES.length];
  ecrire("theme", suivant);
  appliquerTheme(suivant);
  message(suivant === "auto" ? T.themeAuto : suivant === "clair" ? T.themeClair : T.themeSombre, 1600);
}

if (window.matchMedia) {
  window.matchMedia("(prefers-color-scheme: light)")
    .addEventListener("change", () => { if (themeChoisi() === "auto") appliquerTheme("auto"); });
}

/* ------------------------------------------------------------------ outils */

function melangeur(graine) {
  return function () {
    graine |= 0; graine = (graine + 0x6D2B79F5) | 0;
    let t = Math.imul(graine ^ (graine >>> 15), 1 | graine);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function ordreCibles() {
  const liste = Moteur.cibles().slice();
  const rnd = melangeur(0x7A1C05);
  for (let i = liste.length - 1; i > 0; i--) {
    const j = Math.floor(rnd() * (i + 1));
    [liste[i], liste[j]] = [liste[j], liste[i]];
  }
  return liste;
}

function numeroDuJour(d = new Date()) {
  const local = Date.UTC(d.getFullYear(), d.getMonth(), d.getDate());
  return Math.floor((local - ORIGINE) / 86400000) + 1;
}

function couleur(rang, sim) {
  if (rang === 0) return "var(--t6)";
  if (rang && rang <= 10) return "var(--t5)";
  if (rang && rang <= 100) return "var(--t4)";
  if (rang) return "var(--t3)";
  const t = temperature(sim);
  if (t >= 30) return "var(--t2)";
  if (t >= 8) return "var(--t1)";
  return "var(--t0)";
}

/* Température : 0 = un mot pris au hasard, 99 = le mot le plus proche de la
   cible, 100 = la cible elle-même. Les 100 degrés sont réservés au mot trouvé :
   sinon le voisin de rang 1 atteignait le plafond de l'échelle et affichait lui
   aussi 100,0°, ce qui laissait croire à une seconde bonne réponse. */
function temperature(sim) {
  const { base, simMax } = partie.analyse;
  if (sim >= 0.9999) return 100;
  return Math.min(99.9, 99 * (sim - base) / Math.max(simMax - base, 0.05));
}

const position = (sim) => Math.max(0, Math.min(1, (temperature(sim) + 22) / 122));

/* Placement sur la bande, marges comprises. */
const surLaBande = (sim) => 1.5 + position(sim) * 97;

const mouvementReduit = () =>
  window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

/**
 * Pose l'aiguille sur la température d'un essai. Quand le mot vient d'être
 * proposé, elle part du bord glacial, file jusqu'à sa valeur, la dépasse
 * légèrement puis revient s'y poser.
 */
function placerAiguille(essai, anime) {
  const a = el.aiguille;
  if (!essai) { a.hidden = true; return; }

  const cible = surLaBande(essai.sim);
  a.hidden = false;
  a.style.color = couleur(essai.rang, essai.sim);
  a.style.left = cible + "%";

  if (!anime || mouvementReduit() || typeof a.animate !== "function") return;

  const elan = Math.min(cible / 40, 1) * Math.min(5.5, Math.max(0, 98.5 - cible));
  const duree = Math.round(400 + cible * 7);

  a.animate([
    { left: "1.5%", opacity: 0.25, offset: 0 },
    { opacity: 1, offset: 0.14 },
    { left: (cible + elan) + "%", offset: 0.8, easing: "cubic-bezier(.15,.65,.3,1)" },
    { left: cible + "%", offset: 1, easing: "cubic-bezier(.45,0,.25,1)" }
  ], { duration: duree, fill: "none" });
}

function message(txt, duree = 2600) {
  el.message.textContent = txt;
  clearTimeout(timerMsg);
  if (txt) timerMsg = setTimeout(() => { el.message.textContent = ""; }, duree);
}

/* ------------------------------------------------------------------ parties */

const cleJour = (jour) => `${langue}:jour:${jour}`;
const cleStats = () => `${langue}:stats`;

function nouvellePartie(mode, cibleMot) {
  const jour = numeroDuJour();
  let mot = cibleMot;
  if (!mot) {
    const liste = ordreCibles();
    mot = mode === "jour" ? liste[(jour - 1) % liste.length]
                          : liste[Math.floor(Math.random() * liste.length)];
  }
  const trouve = Moteur.resoudre(mot);
  partie = {
    mode, jour, cible: trouve.i, mot: trouve.mot,
    essais: [], fini: false, abandon: false, indices: 0, indicesVus: [],
    analyse: Moteur.analyser(trouve.i)
  };
  if (mode === "jour") {
    const sauve = lire(cleJour(jour), null);
    if (sauve && sauve.mot === partie.mot) {
      partie.essais = sauve.essais;
      partie.fini = sauve.fini;
      partie.abandon = sauve.abandon;
      partie.indices = sauve.indices || 0;
      partie.indicesVus = sauve.indicesVus || [];
    }
  }
  dessinerTout();
}

function sauver() {
  if (partie.mode !== "jour") return;
  ecrire(cleJour(partie.jour), {
    mot: partie.mot, essais: partie.essais,
    fini: partie.fini, abandon: partie.abandon,
    indices: partie.indices, indicesVus: partie.indicesVus
  });
}

function proposer(saisie) {
  if (partie.fini) { message(T.finie); return; }
  const r = Moteur.resoudre(saisie);
  if (r && r.bloque) { message(T.motFiltre); return; }
  if (!r) { message(T.inconnu); return; }
  if (partie.essais.find(e => e.i === r.i)) { message(T.dejaPropose(r.mot)); return; }

  const sim = partie.analyse.sims[r.i];
  const rang = r.i === partie.cible ? 0 : (partie.analyse.rangs.get(r.i) || null);
  partie.essais.push({ i: r.i, mot: r.mot, sim, rang });

  if (r.i === partie.cible) {
    partie.fini = true;
    majStats(true, partie.essais.length);
  }
  sauver();
  dessinerTout(r.i);
  if (r.corrige) message(T.compteComme(r.corrige, r.mot));
  if (partie.fini) setTimeout(() => panneauFin(), 420);
}

function abandonner() {
  if (partie.fini) { fermerPanneau(); message(T.dejaFinie); return; }
  partie.fini = true; partie.abandon = true;
  partie.essais.push({ i: partie.cible, mot: partie.mot, sim: 1, rang: 0, revele: true });
  majStats(false, partie.essais.length);
  sauver();
  fermerPanneau();
  dessinerTout(partie.cible);
  setTimeout(() => panneauFin(), 320);
}

function reinitialiser() {
  partie.essais = [];
  partie.fini = false;
  partie.abandon = false;
  partie.indices = 0;
  partie.indicesVus = [];
  if (partie.mode === "jour") oublier(cleJour(partie.jour));
  fermerPanneau();
  dessinerTout();
  message(T.efface);
  el.champ.focus();
}

/**
 * Un indice oriente sans donner. On tire au hasard parmi ceux qui restent pour
 * ce mot : catégorie, phrase d'usage où le mot est masqué. En dernier recours
 * seulement, quand il n'y a plus de texte disponible, on ajoute un mot proche
 * à la liste, comme avant.
 */
function indice() {
  const tous = Moteur.indices(partie.mot);
  const restants = tous.filter((_, k) => !partie.indicesVus.includes(k));

  if (restants.length) {
    const k = tous.indexOf(restants[Math.floor(Math.random() * restants.length)]);
    partie.indicesVus.push(k);
    partie.indices++;
    sauver();
    panneauIndice(tous[k], tous.length - partie.indicesVus.length);
    return;
  }

  /* Plus rien d'écrit pour ce mot : on le dit, on ne joue pas un coup à sa place. */
  fermerPanneau();
  message(T.plusIndice);
}

function majStats(gagne, essais) {
  if (partie.mode !== "jour") return;
  const s = lire(cleStats(), { parties: 0, gagnees: 0, serie: 0, meilleureSerie: 0, dernierJour: 0, total: 0 });
  if (s.dernierJour === partie.jour) return;
  s.parties++;
  if (gagne) {
    s.gagnees++; s.total += essais;
    s.serie = s.dernierJour === partie.jour - 1 ? s.serie + 1 : 1;
    s.meilleureSerie = Math.max(s.meilleureSerie, s.serie);
  } else s.serie = 0;
  s.dernierJour = partie.jour;
  ecrire(cleStats(), s);
}

/* ------------------------------------------------------------------ affichage */

function dessinerTout(surligne) {
  el.mode.textContent = partie.mode === "jour" ? T.motDuJour(partie.jour) : T.partieLibre;

  const tries = partie.essais.slice().sort((a, b) => b.sim - a.sim);
  const meilleur = tries[0];

  el.essais.textContent = T.essais(partie.essais.length);
  el.record.textContent = meilleur
    ? T.meilleur(meilleur.mot, temperature(meilleur.sim).toFixed(1))
    : T.riensEncore;

  const nouveau = surligne !== undefined;
  const porte = nouveau ? partie.essais.find(e => e.i === surligne)
                        : partie.essais[partie.essais.length - 1];

  /* Le mot que porte l'aiguille n'a pas de marque : sinon son arrivée serait
     annoncée avant même que l'aiguille se mette en route. */
  el.marques.innerHTML = "";
  for (const e of partie.essais) {
    if (porte && e.i === porte.i) continue;
    const t = document.createElement("i");
    t.style.left = surLaBande(e.sim) + "%";
    if (meilleur && e.i === meilleur.i) {
      t.classList.add("pointe");
      t.style.color = couleur(e.rang, e.sim);
    }
    el.marques.appendChild(t);
  }

  placerAiguille(porte, nouveau);

  el.vide.hidden = partie.essais.length > 0;
  el.liste.querySelectorAll(".essai").forEach(n => n.remove());

  const ordre = nouveau
    ? [partie.essais.find(e => e.i === surligne), ...tries.filter(e => e.i !== surligne)]
    : tries;

  for (const e of ordre) {
    if (!e) continue;
    const rang = tries.indexOf(e) + 1;
    const d = document.createElement("div");
    d.className = "essai verre" + (e.i === surligne ? " recent anime" : "") + (e.rang === 0 ? " trouve" : "");
    d.style.color = couleur(e.rang, e.sim);
    d.innerHTML =
      `<span class="fond" style="width:${surLaBande(e.sim).toFixed(1)}%"></span>` +
      `<span class="rang">${rang}</span>` +
      `<span class="mot">${e.mot}</span>` +
      (e.rang === 0
        ? `<span class="badge">${e.revele ? "×" : "✓"}</span>`
        : e.rang ? `<span class="badge">#${e.rang}</span>` : "") +
      `<span class="valeur">${temperature(e.sim).toFixed(1)}°</span>`;
    el.liste.appendChild(d);
  }
  el.liste.scrollTop = 0;
}

/* ------------------------------------------------------------------ panneaux */

function ouvrirPanneau(html) {
  el.panneau.innerHTML = html;
  const dejaOuvert = !el.voile.hidden;
  el.voile.hidden = false;
  el.champ.blur();
  if (!dejaOuvert) history.pushState({ panneau: true }, "");
}

function fermerPanneau() {
  if (el.voile.hidden) return;
  if (history.state && history.state.panneau) history.back();
  else el.voile.hidden = true;
}

window.addEventListener("popstate", () => { el.voile.hidden = true; });

function panneauMenu() {
  ouvrirPanneau(`
    <h2>${T.titre}</h2>

    <h3>${T.actions}</h3>
    <button class="action" data-agir="reinit">${T.aEffacer}<small>${T.aEffacerSous}</small></button>
    ${partie.fini
      ? `<p class="note">${T.dejaRevele}</p>`
      : `<button class="action chaud" data-agir="abandon">${T.aReveler}<small>${T.aRevelerSous}</small></button>`}
    <button class="action" data-agir="indice">${T.aIndice}<small>${T.aIndiceSous}</small></button>
    <button class="action" data-agir="libre">${T.aLibre}<small>${T.aLibreSous}</small></button>
    <button class="action" data-agir="jour">${T.aJour}<small>${T.aJourSous}</small></button>
    ${langueImposee() ? "" : `<button class="action" data-agir="langue">${T.aLangue}<small>${T.aLangueSous}</small></button>`}
    <button class="action${adulteActif() ? " actif" : ""}" data-agir="adulte">
      ${T.aAdulte}<small>${adulteActif() ? T.aAdulteOn : T.aAdulteOff}</small></button>
    <button class="action" data-agir="theme">${T.aTheme}<small>${T.aThemeSous}</small></button>

    <h3>${T.commentTitre}</h3>
    <p>${T.commentTexte}</p>
    <ul><li>${T.regle1()}</li><li>${T.regle2}</li><li>${T.regle3}</li></ul>

    <p class="credit">${T.credit(VERSION)}</p>
  `);
}

function panneauLangue() {
  ouvrirPanneau(`
    <h2>${T.langueTitre}</h2>
    <p>${T.langueTexte}</p>
    ${CODES_LANGUE.map(code => `
      <button class="action${code === langue ? " actif" : ""}" data-agir="langue-${code}">
        ${LANGUES[code].nom}<small>${LANGUES[code].baseline}</small></button>`).join("")}
  `);
}

function panneauStats() {
  const s = lire(cleStats(), { parties: 0, gagnees: 0, serie: 0, meilleureSerie: 0, total: 0 });
  const moyenne = s.gagnees ? Math.round(s.total / s.gagnees) : null;
  ouvrirPanneau(`
    <h2>${T.statsTitre}</h2>
    <div class="chiffres deux">
      <div class="chiffre"><b>${s.parties}</b><span>${T.sJoues}</span></div>
      <div class="chiffre"><b>${s.gagnees}</b><span>${T.sTrouves}</span></div>
      <div class="chiffre"><b>${moyenne ?? "–"}</b><span>${T.sMoyenne}</span></div>
      <div class="chiffre"><b>${s.serie}</b><span>${T.sSerie}</span></div>
    </div>
    <p class="note">${T.sMeilleure(s.meilleureSerie)}
      ${partie.mode === "jour" ? T.sEnCours(partie.essais.length) : T.sLibre}</p>
    <p class="credit">${T.sNote(millier(Moteur.taille()))}</p>
  `);
}

function panneauConfirmerReinit() {
  if (!partie.essais.length) { reinitialiser(); return; }
  ouvrirPanneau(`
    <h2>${T.confEffacerTitre}</h2>
    <div class="avertissement doux"><b>↺</b>
      <span>${T.confEffacerTexte(partie.essais.length, partie.mode === "jour")}</span></div>
    <p style="margin-top:14px">${T.confEffacerNote}</p>
    <div class="paire">
      <button class="action" data-agir="retour">${T.annuler}</button>
      <button class="action ferme" data-agir="reinit-oui">${T.effacer}</button>
    </div>
  `);
}

function panneauConfirmer() {
  ouvrirPanneau(`
    <h2>${T.confRevelerTitre}</h2>
    <div class="avertissement"><b>!</b><span>${T.confRevelerTexte}</span></div>
    <p style="margin-top:14px">${T.confRevelerNote(partie.essais.length)}</p>
    <div class="paire">
      <button class="action" data-agir="retour">${T.annuler}</button>
      <button class="action danger" data-agir="abandon-oui">${T.reveler}</button>
    </div>
  `);
}

function panneauIndice(indice, reste) {
  const etiquette = indice.t === "def" ? T.indiceDef
                  : indice.t === "cat" ? T.indiceCat : T.indicePhrase;
  ouvrirPanneau(`
    <h2>${T.indiceTitre}</h2>
    <p class="etiquette">${etiquette}</p>
    <div class="indice">${indice.x}</div>
    <div class="paire">
      <button class="action" data-agir="retour">${T.annuler}</button>
      ${reste > 0
        ? `<button class="action" data-agir="indice">${T.indiceEncore}</button>`
        : `<button class="action" data-agir="fermer">${T.indiceCompris}</button>`}
    </div>
    <p class="credit">${T.indiceSource}</p>
  `);
}

function panneauFin() {
  const nb = partie.essais.length;
  const proches = [...partie.analyse.rangs.entries()]
    .filter(([, r]) => r <= 8).sort((a, b) => a[1] - b[1])
    .map(([i]) => `<span>${Moteur.mot(i)}</span>`).join("");
  ouvrirPanneau(`
    <h2>${partie.abandon ? T.finRevele(partie.mot) : T.finTrouve(partie.mot)}</h2>
    <p>${partie.abandon ? T.finTexteRevele(nb - 1) : T.finTexteTrouve(nb, partie.indices)}</p>
    <h3>${T.finProches}</h3>
    <div class="voisins">${proches}</div>
    <button class="action" data-agir="libre">${T.finEnchainer}<small>${T.finEnchainerSous}</small></button>
  `);
}

/* ------------------------------------------------------------------ liaisons */

el.saisie.addEventListener("submit", (ev) => {
  ev.preventDefault();
  const v = el.champ.value;
  if (!v.trim()) return;
  el.champ.value = "";
  proposer(v);
});

$("#btn-menu").addEventListener("click", panneauMenu);
$("#btn-stats").addEventListener("click", panneauStats);
$("#btn-theme").addEventListener("click", basculerTheme);
$("#btn-langue").addEventListener("click", panneauLangue);
$("#btn-fermer").addEventListener("click", fermerPanneau);
el.voile.addEventListener("click", (ev) => { if (ev.target === el.voile) fermerPanneau(); });

async function changerLangue(code) {
  if (code === langue) { fermerPanneau(); return; }
  fermerPanneau();
  el.splash.hidden = false;
  el.splash.classList.remove("sortie");
  el.jauge.style.width = "0%";
  langue = code;
  ecrire("langue", code);
  appliquerTextes();
  appliquerTheme(themeChoisi());
  await Moteur.charger(code, (pct, texte) => {
    el.jauge.style.width = pct + "%";
    el.etat.textContent = texte;
  });
  appliquerFiltre();
  nouvellePartie("jour");
  setTimeout(() => {
    el.splash.classList.add("sortie");
    setTimeout(() => { el.splash.hidden = true; }, 480);
    message(T.langueChangee(T.nom));
  }, 420);
}

el.panneau.addEventListener("click", (ev) => {
  const b = ev.target.closest("[data-agir]");
  if (!b) return;
  const quoi = b.dataset.agir;
  if (quoi === "libre") { fermerPanneau(); nouvellePartie("libre"); message(T.nouveauHasard); }
  if (quoi === "jour") { fermerPanneau(); nouvellePartie("jour"); }
  if (quoi === "indice") indice();
  if (quoi === "fermer") fermerPanneau();
  if (quoi === "reinit") panneauConfirmerReinit();
  if (quoi === "reinit-oui") reinitialiser();
  if (quoi === "abandon") panneauConfirmer();
  if (quoi === "abandon-oui") abandonner();
  if (quoi === "retour") panneauMenu();
  if (quoi === "langue") panneauLangue();
  if (quoi === "theme") basculerTheme();
  if (quoi === "adulte") basculerAdulte();
  if (quoi.startsWith("langue-")) changerLangue(quoi.slice(7));
});

(async function demarrer() {
  const debut = Date.now();
  langue = langueImposee() || lire("langue", null) || langueDuSysteme();
  if (!CODES_LANGUE.includes(langue)) langue = "fr";
  if (langueImposee()) $("#btn-langue").hidden = true;
  appliquerTextes();
  appliquerTheme(themeChoisi());
  try {
    await Moteur.charger(langue, (pct, texte) => {
      el.jauge.style.width = pct + "%";
      el.etat.textContent = texte;
    });
    appliquerFiltre();
    nouvellePartie("jour");
    appliquerTheme(themeChoisi());

    const reste = Math.max(0, 900 - (Date.now() - debut));
    setTimeout(() => {
      el.appli.hidden = false;
      el.splash.classList.add("sortie");
      setTimeout(() => { el.splash.hidden = true; }, 480);
      if (!partie.fini) el.champ.focus();
    }, reste);
  } catch (e) {
    el.etat.textContent = T.erreurLexique(e.message);
  }
})();
