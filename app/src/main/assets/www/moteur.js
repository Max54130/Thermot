/* Moteur sémantique de Thermot.
   Un lexique par langue : vecteurs fastText filtrés puis quantifiés en int8.
   Tout le calcul se fait sur l'appareil, hors ligne. */

const Moteur = (() => {
  let langue = null;
  let mots = [];
  let index = new Map();      // mot -> position
  let alias = new Map();      // forme tolérée -> mot du lexique
  let vecteurs = null;        // Int8Array (n * dim)
  let normes = null;          // Float32Array (n)
  let dim = 0, n = 0;
  let cibles = [];
  let indices = {};           // mot cible -> liste d'indices rédigés
  let bloques = new Set();    // positions des mots crus, masqués par défaut
  let filtre = true;          // mode tout public actif

  const sansAccent = (m) => m.normalize("NFD").replace(/[\u0300-\u036f]/g, "");

  /** Charge le lexique d'une langue et remplace celui qui était en mémoire. */
  async function charger(code, surProgres) {
    const etapes = (LANGUES[code] || LANGUES.fr).chargement;
    surProgres(4, etapes[0]);
    const buf = await (await fetch(`lexiques/lexique-${code}.bin`)).arrayBuffer();
    surProgres(45, etapes[1]);

    const vue = new DataView(buf);
    const magie = String.fromCharCode(vue.getUint8(0), vue.getUint8(1), vue.getUint8(2), vue.getUint8(3));
    if (magie !== "MOTX") throw new Error("format inattendu");
    n = vue.getUint32(4, true);
    dim = vue.getUint16(8, true);
    const tailleMots = vue.getUint32(10, true);

    let p = 14;
    mots = new TextDecoder("utf-8").decode(new Uint8Array(buf, p, tailleMots)).split("\n");
    p += tailleMots;
    vecteurs = new Int8Array(buf, p, n * dim);
    p += n * dim;
    normes = new Float32Array(buf.slice(p, p + n * 4));

    index = new Map();
    for (let i = 0; i < n; i++) index.set(mots[i], i);
    surProgres(72, etapes[2]);

    alias = new Map();
    const brut = await (await fetch(`lexiques/alias-${code}.txt`)).text();
    for (const ligne of brut.split("\n")) {
      if (!ligne) continue;
      const [de, vers] = ligne.split("\t");
      if (index.has(vers)) alias.set(de, vers);
    }
    surProgres(88, etapes[3]);

    cibles = (await (await fetch(`lexiques/cibles-${code}.txt`)).text())
      .split("\n").map(m => m.trim()).filter(m => m && (index.has(m) || alias.has(m)));

    try { indices = await (await fetch(`lexiques/indices-${code}.json`)).json(); }
    catch (e) { indices = {}; }

    bloques = new Set();
    try {
      const brut = await (await fetch(`lexiques/sensibles-${code}.txt`)).text();
      for (const mot of brut.split("\n")) {
        const i = index.get(mot.trim());
        if (i !== undefined) bloques.add(i);
      }
    } catch (e) { /* liste absente : rien n'est masqué */ }

    langue = code;
    surProgres(100, etapes[4]);
    return { mots: n, cibles: cibles.length };
  }

  /* Ce que le joueur a tapé : casse, accents et flexions sont tolérés.
     Un mot cru renvoie { bloque: true } quand le mode tout public est actif :
     mieux vaut le dire que de prétendre que le mot n'existe pas. */
  function resoudre(saisie) {
    let m = String(saisie).trim().replace(/[^\p{L}'-]/gu, "");
    if (!m) return null;
    const essais = [m, m.toLowerCase(), sansAccent(m), sansAccent(m).toLowerCase()];
    for (const e of essais) {
      const trouve = chercher(e);
      if (trouve === undefined) continue;
      if (filtre && bloques.has(trouve)) return { bloque: true };
      return { i: trouve, mot: mots[trouve], corrige: mots[trouve] === m ? null : m };
    }

    /* Rattrapage morphologique : le joueur écrit souvent une forme voisine de
       celle que porte le lexique, « cucurbitacé » pour « cucurbitacée » par
       exemple. On essaie quelques variantes, puis on cherche un mot du lexique
       dont la saisie est le début, en prenant le plus fréquent. */
    const base = sansAccent(m).toLowerCase();

    /* on essaie d'abord d'allonger, puis de compléter par le début, et enfin
       de raccourcir : « abricotie » doit donner « abricotier », pas « abricot » */
    const rallonge = (v) => {
      if (v.length < 3) return undefined;
      const t = chercher(v) ?? chercher(v.toLowerCase());
      return t;
    };
    for (const variante of [m + "e", m + "s", m + "es", m + "a", m + "o"]) {
      const t = rallonge(variante);
      if (t !== undefined) {
        if (filtre && bloques.has(t)) return { bloque: true };
        return { i: t, mot: mots[t], corrige: m };
      }
    }
    if (m.length >= 5) {
      for (let i = 0; i < n; i++) {
        const cand = mots[i];
        if (cand.length > m.length && cand.length <= m.length + 3 &&
            sansAccent(cand).toLowerCase().startsWith(base)) {
          if (filtre && bloques.has(i)) return { bloque: true };
          return { i, mot: cand, corrige: m };
        }
      }
    }
    for (const variante of [m.slice(0, -1), m.slice(0, -2)]) {
      if (variante.length < 3) continue;
      if (variante.length < 3) continue;
      const t = chercher(variante) ?? chercher(variante.toLowerCase());
      if (t !== undefined) {
        if (filtre && bloques.has(t)) return { bloque: true };
        return { i: t, mot: mots[t], corrige: m };
      }
    }
    return null;
  }

  /** Position d'un mot dans le lexique, alias compris. */
  function chercher(mot) {
    if (index.has(mot)) return index.get(mot);
    if (alias.has(mot)) return index.get(alias.get(mot));
    return undefined;
  }

  /* Cosinus entre deux entrées du lexique. */
  function similarite(a, b) {
    let s = 0;
    const da = a * dim, db = b * dim;
    for (let k = 0; k < dim; k++) s += vecteurs[da + k] * vecteurs[db + k];
    return s / (normes[a] * normes[b]);
  }

  /* Similarités de la cible avec tout le lexique, rang des 1000 plus proches,
     et similarité médiane qui sert de zéro à l'échelle de température. */
  function analyser(cible) {
    const sims = new Float32Array(n);
    const dc = cible * dim, nc = normes[cible];
    for (let i = 0; i < n; i++) {
      let s = 0;
      const di = i * dim;
      for (let k = 0; k < dim; k++) s += vecteurs[di + k] * vecteurs[dc + k];
      sims[i] = s / (normes[i] * nc);
    }
    let candidats = Array.from({ length: n }, (_, i) => i);
    if (filtre) candidats = candidats.filter(i => !bloques.has(i));
    const ordre = candidats.sort((a, b) => sims[b] - sims[a]);
    const base = sims[ordre[Math.floor(n / 2)]];
    const rangs = new Map();
    let r = 0;
    for (const i of ordre) {
      if (i === cible) continue;
      r++;
      rangs.set(i, r);
      if (r >= 1000) break;
    }
    const meilleur = ordre.find(i => i !== cible);
    return { sims, rangs, base, simMax: sims[meilleur] };
  }

  return {
    charger, resoudre, similarite, analyser,
    filtrer: (actif) => { filtre = actif; },
    filtreActif: () => filtre,
    nbBloques: () => bloques.size,
    mot: (i) => mots[i],
    cibles: () => cibles,
    indices: (mot) => indices[mot] || [],
    taille: () => n,
    langue: () => langue
  };
})();
