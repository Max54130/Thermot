#!/usr/bin/env python3
"""
Trie les nouvelles cibles proposées : ne garde que les noms communs.

Un mot du jour doit être un nom commun au singulier. Les listes reçues sont
construites par fréquence brute et contiennent donc des verbes, des adjectifs
et des mots outils, qui feraient de très mauvais mots cachés.

Plutôt que des règles de suffixes, peu fiables en français comme en italien
(« plaisir » et « souvenir » sont des noms, « finir » non), on entraîne une
régression logistique sur les vecteurs eux-mêmes :

- exemples positifs : les mots cibles déjà curés à la main, tous des noms ;
- exemples négatifs : verbes, adjectifs, adverbes et mots outils listés ci-dessous.

La justesse est mesurée par validation croisée avant d'accepter quoi que ce soit.
"""
import json, os, sys
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import cross_val_score

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEX = os.path.join(RACINE, "app/src/main/assets/www/lexiques")
VECTEURS = os.environ.get("VECTEURS", os.path.join(RACINE, "..", "data"))
RECU = os.environ.get("RECU", os.path.join(RACINE, "..", "recu"))

# Contre-exemples : ce qu'un mot du jour ne doit jamais être.
NEGATIFS = {
"fr": """prendre donner faire aller venir voir savoir pouvoir vouloir devoir mettre dire
partir sortir entrer monter descendre courir marcher parler écouter regarder manger boire
dormir vivre mourir aimer détester chercher trouver perdre gagner ouvrir fermer commencer
finir continuer arrêter penser croire comprendre apprendre oublier rappeler porter tenir
belle beau joli laid grand petit gros mince long court haut bas jeune vieux nouveau ancien
bon mauvais meilleur pire fort faible chaud froid propre sale facile difficile important
possible impossible certain probable vrai faux plein rapide lent premier dernier seul même
autre chose truc machin gens quelqu'un personne rien tout beaucoup peu très trop assez
toujours jamais souvent parfois ici maintenant hier demain alors donc ainsi cependant
plutôt vraiment surtout encore déjà bientôt aussi moins plus contre entre pendant selon""",
"en": """take give make going coming trying doing saying getting having being seeing knowing
looking working playing living dying loving finding losing winning opening closing starting
finishing keeping holding putting running walking talking listening eating drinking sleeping
beautiful ugly big small large tiny long short high low young old new ancient good bad better
worse strong weak hot cold clean dirty easy hard important possible impossible certain likely
true false full fast slow first last only same other thing stuff someone anyone nothing
everything really quite rather very much many few always never often sometimes here there
now then today tomorrow yesterday however therefore although because during against between""",
"es": """tomar dar hacer ir venir ver saber poder querer deber poner decir salir entrar subir
bajar correr andar hablar escuchar mirar comer beber dormir vivir morir amar buscar encontrar
perder ganar abrir cerrar empezar terminar seguir parar pensar creer entender aprender olvidar
bello hermoso feo grande pequeño gordo delgado largo corto alto bajo joven viejo nuevo antiguo
bueno malo mejor peor fuerte débil caliente frío limpio sucio fácil difícil importante posible
imposible cierto probable verdadero falso lleno rápido lento primero último solo mismo otro
cosa algo alguien nadie nada todo mucho poco muy demasiado bastante siempre nunca a menudo
aquí ahora hoy mañana ayer entonces sin embargo aunque porque durante contra entre según""",
"it": """prendere dare fare andare venire vedere sapere potere volere dovere mettere dire
uscire entrare salire scendere correre camminare parlare ascoltare guardare mangiare bere
dormire vivere morire amare cercare trovare perdere vincere aprire chiudere cominciare finire
continuare fermare pensare credere capire imparare dimenticare portare tenere nuova nuovo
seconda secondo particolare bello brutto grande piccolo grosso magro lungo corto alto basso
giovane vecchio antico buono cattivo migliore peggiore forte debole caldo freddo pulito sporco
facile difficile importante possibile impossibile certo probabile vero falso pieno veloce
lento primo ultimo solo stesso altro cosa roba qualcuno nessuno niente tutto molto poco
troppo abbastanza sempre mai spesso qui ora oggi domani ieri allora quindi tuttavia benché""",
"de": """nehmen geben machen gehen kommen sehen wissen können wollen sollen setzen sagen
gehend kommend laufen sprechen hören schauen essen trinken schlafen leben sterben lieben
suchen finden verlieren gewinnen öffnen schließen anfangen aufhören denken glauben verstehen
lernen vergessen tragen halten schön hässlich groß klein dick dünn lang kurz hoch niedrig
jung alt neu gut schlecht besser schlimmer stark schwach heiß kalt sauber schmutzig leicht
schwer wichtig möglich unmöglich sicher wahr falsch voll schnell langsam erste letzte einzige
gleiche andere Ding Sachen jemand niemand nichts alles sehr viel wenig zu genug immer nie
oft manchmal hier jetzt heute morgen gestern damals jedoch obwohl weil während gegen zwischen""",
}

# Repérés en relisant la première passe : le modèle les prenait pour des noms.
RENFORT = {
"fr": """télévisuelle professionnelle britannique poétique didactique journalistique graphique
universitaire ecclésiastique israélite supérieure sanglant acquitté choisie résulte solidaire
censurée centriste rival compatriote responsable""",
"en": """gaseous societal criminal fascist floral algal biblical deciduous academic federal
municipal digital global annual initial marine tribal viral vocal legal""",
"es": """francesa parroquial petrolera agrícola jurisdiccional inmediata extranjera nacional
regional cultural mundial digital global anual inicial marina tribal viral vocal legal""",
"it": """maledetta pubblicitaria infernale cinematografico straniera agricola elettrica celeste
cranica nazionale regionale culturale mondiale digitale globale annuale iniziale marina legale""",
"de": """kulturell national regional global digital jährlich anfänglich rechtlich örtlich
wirtschaftlich technisch politisch sozial medizinisch sportlich künstlerisch""",
}

# Un mot du jour ne doit pas mettre mal à l'aise : ces champs sont exclus d'office.
EXCLUS = set("""fellation cocaïne cocaine cocaína héroïne pénis penis vagin vagina érection
sperme prostituée prostitute viol rape suicide cannabis heroína marihuana Penis Cannabis
Kokain Heroin stupro suicidio suicidio prostituta prostituée droga drogue""".split())

SEUIL = float(os.environ.get("SEUIL", "0.86"))


def charger(code):
    Q = np.load(f"{VECTEURS}/{code}_mat.npy").astype(np.float32)
    Q /= np.linalg.norm(Q, axis=1, keepdims=True)
    mots = open(f"{VECTEURS}/{code}_mots.txt", encoding="utf-8").read().split("\n")
    idx = {m: i for i, m in enumerate(mots)}
    alias = {}
    for ligne in open(f"{LEX}/alias-{code}.txt", encoding="utf-8"):
        if "\t" in ligne:
            a, b = ligne.rstrip("\n").split("\t")
            alias[a] = b
    return Q, mots, idx, alias


def trier(code):
    Q, mots, idx, alias = charger(code)
    curees = [l.strip() for l in open(f"{LEX}/cibles-{code}.txt", encoding="utf-8") if l.strip()]

    pos = [idx[m] for m in curees if m in idx]
    neg = []
    for m in (NEGATIFS[code] + " " + RENFORT[code]).split():
        j = idx.get(m) or idx.get(m.lower()) or idx.get(m.capitalize())
        if j is not None:
            neg.append(j)
    neg = sorted(set(neg))

    X = np.vstack([Q[pos], Q[neg]])
    y = np.r_[np.ones(len(pos)), np.zeros(len(neg))]
    modele = LogisticRegression(max_iter=2000, C=1.0, class_weight="balanced")
    justesse = cross_val_score(modele, X, y, cv=5).mean()
    modele.fit(X, y)

    nouveaux = [l.strip() for l in open(f"{RECU}/new-targets-{code}.txt", encoding="utf-8") if l.strip()]
    deja = set(curees)

    retenus, rejetes, absents = [], [], []
    for m in nouveaux:
        if m in deja:
            continue
        cible = m if m in idx else alias.get(m)
        if cible is None or cible not in idx:
            absents.append(m)
            continue
        if m in EXCLUS:
            rejetes.append((m, 0.0))
            continue
        if cible != m or cible in deja:
            # forme fléchie ou doublon d'une cible existante
            rejetes.append((m, 0.0))
            continue
        p = float(modele.predict_proba(Q[idx[m]].reshape(1, -1))[0, 1])
        (retenus if p >= SEUIL else rejetes).append((m, p))

    retenus.sort(key=lambda t: -t[1])
    rejetes.sort(key=lambda t: -t[1])
    print(f"[{code}] justesse du tri : {justesse*100:.1f} %  "
          f"({len(pos)} noms, {len(neg)} contre-exemples)")
    print(f"[{code}] {len(retenus)} retenus, {len(rejetes)} écartés, "
          f"{len(absents)} absents du lexique, sur {len(nouveaux)} proposés")
    print(f"[{code}] retenus, les plus sûrs : {' '.join(m for m, _ in retenus[:12])}")
    print(f"[{code}] retenus, les plus limites : {' '.join(m for m, _ in retenus[-12:])}")
    print(f"[{code}] écartés, les plus limites : {' '.join(m for m, _ in rejetes[:12] if _)}")
    return [m for m, _ in retenus]


if __name__ == "__main__":
    sortie = {}
    for code in (sys.argv[1:] or ["fr", "en", "es", "it", "de"]):
        sortie[code] = trier(code)
        print()
    os.makedirs(os.path.join(RACINE, "outils/cibles"), exist_ok=True)
    json.dump(sortie, open(os.path.join(RACINE, "outils/nouvelles_cibles.json"), "w",
                           encoding="utf-8"), ensure_ascii=False, indent=0)
    print("total retenu :", sum(len(v) for v in sortie.values()))
