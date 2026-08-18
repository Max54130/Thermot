#!/usr/bin/env python3
"""
Construit un lexique par langue à partir des vecteurs fastText.

Source : https://dl.fbaipublicfiles.com/fasttext/vectors-crawl/cc.XX.300.vec.gz
Licence des vecteurs : CC BY-SA 3.0 (Facebook AI Research, Grave et al. 2018)

Les 300 dimensions sont conservées : une analyse en composantes principales à
160 dimensions ne retrouvait que 84 % des 50 plus proches voisins, contre 98 %
avec la quantification seule. La taille se règle donc sur le nombre de mots.

Sortie par langue, dans app/src/main/assets/www/lexiques/ :
  lexique-XX.bin   en-tête, mots, vecteurs int8, normes float32
  alias-XX.txt     formes tolérées à la saisie -> forme du lexique
  cibles-XX.txt    mots pouvant tomber comme mot du jour
"""
import os, re, struct, sys, unicodedata
import numpy as np

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SORTIE = os.path.join(RACINE, "app/src/main/assets/www/lexiques")
# dossier contenant les fichiers cc.XX.300.vec tronqués
VECTEURS = os.environ.get("VECTEURS", os.path.join(RACINE, "..", "data"))
DIM = 300
# plafond de vocabulaire, surchargeable pour produire des variantes plus profondes
PLAFOND = int(os.environ.get("PLAFOND", "0"))

# Une langue = un alphabet, une taille, et ses règles de tolérance.
LANGUES = {
    "fr": dict(motif=r"^[a-zàâäçéèêëîïôöùûüÿœæ]{3,18}$"
                     r"|^[a-zàâäçéèêëîïôöùûüÿœæ]{2,14}(?:[-'][a-zàâäçéèêëîïôöùûüÿœæ]{1,14}){1,3}$",
               garde=78000,
               pluriels=["s", "x"], majuscules=False,
               irreguliers={"aux": ["al", "ail"], "eux": ["eu"], "oux": ["ou"]}),
    "en": dict(motif=r"^[a-z]{3,18}$", garde=48000,
               pluriels=["s", "es"], majuscules=False),
    "es": dict(motif=r"^[a-záéíóúüñ]{3,18}$", garde=48000,
               pluriels=["s", "es"], majuscules=False),
    # l'italien change la voyelle finale au pluriel : libro/libri, casa/case
    "it": dict(motif=r"^[a-zàèéìòóù]{3,18}$", garde=48000,
               pluriels=["i>o", "i>io", "i>e", "e>a", "i>a"], majuscules=False, garde_maj=50000),
    # l'allemand écrit ses noms communs avec une majuscule : les exclure
    # viderait le jeu de sa substance
    # l'allemand décline et infléchit : Berg/Berges/Berge/Bergen, Buch/Bücher
    "de": dict(motif=r"^[A-ZÄÖÜa-zäöüß][a-zäöüß]{2,17}$", garde=48000,
               # le suffixe « e » a été retiré : il fusionnait Kirsche, le fruit, avec Kirsch, l'alcool
               pluriels=["s", "es", "en", "n", "er", "ern"],
               demutation=True, majuscules=True),
}

TRANSLIT = {"ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss",
            "Ä": "Ae", "Ö": "Oe", "Ü": "Ue"}
DEMUTATION = str.maketrans({"ä": "a", "ö": "o", "ü": "u",
                            "Ä": "A", "Ö": "O", "Ü": "U"})


def formes_de_base(mot, cfg, irregulieres_seulement=False):
    """
    Formes fléchies possibles d'un mot, selon les règles de la langue.

    Les formes issues des règles irrégulières sont demandées à part, car elles
    doivent primer : « travaux » vient de « travail », même si le corpus
    contient la coquille « travau » que le simple retrait du « x » produirait.
    """
    bases = set()
    for fin, remplacements in cfg.get("irreguliers", {}).items():
        if mot.endswith(fin) and len(mot) > len(fin) + 1:
            for r in remplacements:
                bases.add(mot[:-len(fin)] + r)
    if irregulieres_seulement:
        bases.discard(mot)
        return bases

    for regle in cfg.get("pluriels", []):
        if ">" in regle:                      # changement de voyelle finale
            fin, remplacement = regle.split(">")
            if mot.endswith(fin) and len(mot) > len(fin) + 2:
                bases.add(mot[:-len(fin)] + remplacement)
        elif mot.endswith(regle) and len(mot) > len(regle) + 3:
            bases.add(mot[:-len(regle)])
    if cfg.get("demutation"):                 # Bücher -> Buch
        for b in list(bases) + [mot]:
            d = b.translate(DEMUTATION)
            if d != b:
                bases.add(d)
        # Le pluriel en « e » n'est admis que s'il s'accompagne d'une inflexion :
        # Stühle vient bien de Stuhl, mais Kirsche ne vient pas de Kirsch.
        if mot.endswith("e") and len(mot) > 4:
            tronque = mot[:-1]
            sans_inflexion = tronque.translate(DEMUTATION)
            if sans_inflexion != tronque:
                bases.add(sans_inflexion)
    bases.discard(mot)
    return bases


def sans_accent(m):
    return "".join(c for c in unicodedata.normalize("NFD", m)
                   if unicodedata.category(c) != "Mn")


def translitere(m):
    return "".join(TRANSLIT.get(c, c) for c in m)


def lire_tranche(chemin, motif, mots, vecs, entete):
    """
    Lit une tranche du fichier de vecteurs et empile ce qui passe le filtre.

    La découpe se fait en une seule coupure au premier espace, et les 300
    flottants sont lus d'un bloc : cinq fois plus rapide que de découper toute
    la ligne, ce qui compte quand on parcourt deux millions d'entrées.
    """
    with open(chemin, encoding="utf-8", errors="replace") as f:
        if entete:
            f.readline()          # « 2000000 300 » en première ligne du fichier d'origine
        for ligne in f:
            mot, _, reste = ligne.partition(" ")
            if not motif.match(mot):
                continue
            v = np.fromstring(reste, dtype=np.float32, sep=" ")
            if v.size != DIM:
                continue
            n = np.linalg.norm(v)
            if n < 1e-6:
                continue
            mots.append(mot)
            vecs.append(v / n)


def lire_vecteurs(chemins, motif):
    """
    Lit plusieurs tranches, dans l'ordre de fréquence décroissante. La tête
    couvre le vocabulaire courant, la suite ramène les mots rares mais connus,
    du genre « esperluette » ou « bigorneau », qui ont leur place dans un jeu
    de mots même s'ils sortent peu dans un corpus web.
    """
    mots, vecs = [], []
    for rang, chemin in enumerate(chemins):
        if os.path.exists(chemin):
            lire_tranche(chemin, motif, mots, vecs, entete=(rang == 0))
    return mots, np.vstack(vecs)


def normalise(m):
    return sans_accent(m.lower())


def lire_cibles(code):
    chemin = os.path.join(RACINE, "outils/cibles", f"{code}.txt")
    if not os.path.exists(chemin):
        return []
    return [l.strip() for l in open(chemin, encoding="utf-8") if l.strip()]


# Pluriels français que la morphologie régulière ne rattrape pas.
IRREGULIERS_FR = {
    "yeux": "œil", "cieux": "ciel", "aïeux": "aïeul", "messieurs": "monsieur",
    "mesdames": "madame", "mesdemoiselles": "mademoiselle", "œufs": "œuf",
    "oeufs": "oeuf", "bœufs": "bœuf", "boeufs": "boeuf",
}

# Au-delà de ce rang de fréquence, un mot n'est plus un mot courant : c'est
# une coquille, un mot étranger ou un nom propre déguisé. Sert de garde-fou aux
# règles de pluriel irrégulier.
COURANT = 60000

# Mots français terminés par -x ou -eux qui ne sont pas des pluriels. Les règles
# de flexion doivent les laisser tranquilles, sans quoi « creux » se retrouve
# rattaché à la coquille « creu ».
INVARIABLES_FR = set("""creux époux faux prix voix noix toux choix roux doux jaloux houx flux
crucifix perdrix index silex thorax larynx pharynx lynx sphinx onyx phénix taux flux courroux
époux joyeux affreux heureux nerveux nombreux fameux fabuleux""".split())

PLAFOND = int(os.environ.get("PLAFOND", "0"))   # 0 = pas de plafond


def construire(code):
    cfg = dict(LANGUES[code])
    if PLAFOND:
        cfg["garde"] = PLAFOND
    sources = [f"{VECTEURS}/{code}_head.vec", f"{VECTEURS}/{code}_tail.vec",
               f"{VECTEURS}/{code}_full.vec"]
    if os.path.exists(f"{VECTEURS}/{code}_full.vec"):
        sources = [f"{VECTEURS}/{code}_full.vec"]     # le corpus entier remplace les tranches
    mots, M = lire_vecteurs(sources, re.compile(cfg["motif"]))
    rang = {m: i for i, m in enumerate(mots)}
    print(f"[{code}] candidats bruts : {len(mots)}")

    garde = [True] * len(mots)
    alias = {}

    # 1) formes fléchies ramenées à la forme de base, seulement si celle-ci est
    #    plus fréquente : la fréquence tranche mieux qu'une règle absolue.
    #    Exception pour les pluriels irréguliers, où la forme plurielle est
    #    souvent la plus courante : « yeux » l'emporte sur « œil », « chevaux »
    #    sur « cheval ». La règle y est appliquée sans condition de fréquence.
    irreg = cfg.get("irreguliers", {})
    for i, m in enumerate(mots):
        if not garde[i]:
            continue
        if code == "fr" and m in INVARIABLES_FR:
            continue
        sans_frequence = any(m.endswith(f) for f in irreg)

        def meilleure(candidates, ignorer_frequence, seuil=0.55, par_frequence=False):
            """
            Choisit la forme de base. Par défaut on prend la plus proche au sens
            des vecteurs. Pour les pluriels irréguliers on prend la plus
            fréquente au-dessus d'un seuil abaissé : « travaux » et « travail »
            ne sont qu'à 0,45 l'un de l'autre, l'usage ayant éloigné les deux
            sens, alors que la coquille « travau » est contextuellement plus
            proche. La fréquence tranche mieux que la similarité dans ce cas.
            """
            retenu, score, meilleur_rang = None, seuil, None
            for base in candidates:
                j = rang.get(base)
                if j is None or not garde[j] or (j >= i and not ignorer_frequence):
                    continue
                # Un pluriel irrégulier renvoie forcément à un mot courant.
                # Sans ce garde-fou, « creux » finissait sur la coquille
                # « creu » et « époux » sur « épou », toutes deux présentes
                # dans le corpus mais enfouies très loin dans les fréquences.
                if par_frequence and j >= COURANT and j >= i:
                    continue
                s = float(M[i] @ M[j])
                if s <= seuil:
                    continue
                if par_frequence:
                    if meilleur_rang is None or j < meilleur_rang:
                        retenu, meilleur_rang = base, j
                elif s > score:
                    retenu, score = base, s
            return retenu

        # la règle irrégulière passe avant le simple retrait d'une lettre
        meilleur = meilleure(formes_de_base(m, cfg, irregulieres_seulement=True),
                             True, seuil=0.30, par_frequence=True)
        if meilleur is None:
            meilleur = meilleure(formes_de_base(m, cfg), sans_frequence)
        if meilleur:
            garde[i] = False
            alias[m] = meilleur

    # 2) pluriels irréguliers listés : quand les deux formes existent, on garde
    #    le singulier et l'on rattache le pluriel. Sans cela « yeux » restait un
    #    mot à part entière, avec son propre score, au lieu de renvoyer à « œil ».
    if code == "fr":
        for pluriel, singulier in IRREGULIERS_FR.items():
            ip, isg = rang.get(pluriel), rang.get(singulier)
            if ip is not None and isg is not None and garde[isg]:
                garde[ip] = False
                alias[pluriel] = singulier

    # 3) doublons d'accentuation : on garde la forme la plus fréquente
    for i, m in enumerate(mots):
        if not garde[i]:
            continue
        d = sans_accent(m)
        if d == m:
            continue
        j = rang.get(d)
        if j is None or not garde[j]:
            continue
        if float(M[i] @ M[j]) > 0.60:
            if i < j:
                garde[j] = False
                alias[d] = m
            else:
                garde[i] = False
                alias[m] = d

    # 3) doublons de casse, utile là où les noms prennent une majuscule
    if cfg["majuscules"]:
        for i, m in enumerate(mots):
            if not garde[i] or m == m.lower():
                continue
            j = rang.get(m.lower())
            if j is not None and garde[j] and float(M[i] @ M[j]) > 0.52:
                if i < j:
                    garde[j] = False
                else:
                    garde[i] = False

    # Les mots cibles sont ajoutés même s'ils tombent au-delà du plafond de
    # vocabulaire : un mot du jour absent du lexique n'aurait aucun sens.
    vises = {normalise(m) for m in lire_cibles(code)}
    retenus = [i for i in range(len(mots)) if garde[i]]
    plafond = PLAFOND or cfg["garde"]
    gardes = retenus[:plafond]
    deja = set(gardes)
    for i in retenus[plafond:]:
        if normalise(mots[i]) in vises and i not in deja:
            gardes.append(i)
            deja.add(i)
    gardes.sort()
    final = [mots[i] for i in gardes]
    Mf = M[gardes]
    ens = set(final)
    alias = {k: v for k, v in alias.items() if v in ens and k not in ens}

    # 4) tolérances de saisie : minuscules, accents omis, translittération, et
    #    pour les composés, les formes sans séparateur ou avec un espace
    for m in final:
        variantes = {m.lower(), sans_accent(m).lower(), translitere(m).lower()}
        if "-" in m or "'" in m:
            colle = m.replace("-", "").replace("'", "")
            espace = m.replace("-", " ").replace("'", " ")
            variantes |= {colle, colle.lower(), sans_accent(colle).lower(),
                          espace, espace.lower(), sans_accent(espace).lower()}
        for variante in variantes:
            if variante != m and variante not in ens and variante not in alias:
                alias[variante] = m

    if code == "fr":
        for pluriel, singulier in IRREGULIERS_FR.items():
            if singulier in ens and pluriel not in ens:
                alias[pluriel] = singulier

    composes = sum(1 for m in final if "-" in m or "'" in m)
    print(f"[{code}] mots conservés : {len(final)}   alias : {len(alias)}"
          + (f"   dont composés : {composes}" if composes else ""))

    Q = np.clip(np.rint(Mf * 127.0), -127, 127).astype(np.int8)
    normes = np.linalg.norm(Q.astype(np.float32), axis=1).astype(np.float32)

    os.makedirs(SORTIE, exist_ok=True)
    bloc = "\n".join(final).encode("utf-8")
    with open(f"{SORTIE}/lexique-{code}.bin", "wb") as f:
        f.write(b"MOTX")
        f.write(struct.pack("<IHI", len(final), DIM, len(bloc)))
        f.write(bloc)
        f.write(Q.tobytes())
        f.write(normes.tobytes())
    with open(f"{SORTIE}/alias-{code}.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(f"{k}\t{v}" for k, v in sorted(alias.items())))

    # les mots cibles proposés sont filtrés sur leur présence réelle
    propose = lire_cibles(code)
    if propose:
        # rattrapage insensible à la casse et aux accents, indispensable en
        # allemand où la forme minuscule d'un nom peut être la plus fréquente
        par_norme = {}
        for m in final:
            par_norme.setdefault(normalise(m), m)
        for k, v in alias.items():
            par_norme.setdefault(normalise(k), v)

        retenu, absents = [], []
        for m in propose:
            if m in ens:
                retenu.append(m)
            elif m in alias:
                retenu.append(alias[m])
            elif normalise(m) in par_norme:
                retenu.append(par_norme[normalise(m)])
            else:
                absents.append(m)
        vus, cibles = set(), []
        for m in retenu:
            if m not in vus:
                vus.add(m); cibles.append(m)
        with open(f"{SORTIE}/cibles-{code}.txt", "w", encoding="utf-8") as f:
            f.write("\n".join(cibles))
        print(f"[{code}] cibles : {len(cibles)} retenues, {len(absents)} absentes")
        if absents:
            print(f"[{code}] absentes : {' '.join(absents[:25])}")

    taille = os.path.getsize(f"{SORTIE}/lexique-{code}.bin") / 1e6
    print(f"[{code}] lexique-{code}.bin : {taille:.1f} Mo")
    np.save(f"{VECTEURS}/{code}_mat.npy", Q)
    with open(f"{VECTEURS}/{code}_mots.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(final))


if __name__ == "__main__":
    for code in (sys.argv[1:] or LANGUES.keys()):
        construire(code)
