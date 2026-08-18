#!/usr/bin/env python3
"""
Construit les indices de chaque mot cible, dans chaque langue.

Deux sources, toutes deux vérifiables :

1. La catégorie, déduite du lexique lui-même. Chaque catégorie est définie par
   quelques mots d'ancrage ; la cible reçoit la catégorie dont le centre est le
   plus proche, à condition de dépasser un seuil. Aucune donnée extérieure.

2. Une phrase d'usage où le mot est masqué, tirée du corpus Tatoeba
   (https://tatoeba.org, phrases sous licence CC BY 2.0 FR).

Sortie : app/src/main/assets/www/lexiques/indices-XX.json
  { "mot": [ {"t": "cat", "x": "..."}, {"t": "phrase", "x": "..."} ], ... }
"""
import json, os, re, sys, unicodedata
import numpy as np

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEX = os.path.join(RACINE, "app/src/main/assets/www/lexiques")
VECTEURS = os.environ.get("VECTEURS", os.path.join(RACINE, "..", "data"))
PHRASES = os.path.join(VECTEURS, "phrases")

CORPUS = {"fr": "fra", "en": "eng", "es": "spa", "it": "ita", "de": "deu"}

# Catégories : libellé affiché, puis mots d'ancrage cherchés dans le lexique.
CATEGORIES = {
 "fr": [
  ("C'est un animal.", ["chien", "oiseau", "poisson", "cheval", "insecte"]),
  ("Ça pousse, c'est végétal.", ["arbre", "fleur", "plante", "feuille", "racine"]),
  ("Ça se mange ou ça se boit.", ["pain", "fromage", "soupe", "fruit", "boisson"]),
  ("Ça se porte sur soi.", ["chemise", "pantalon", "chaussure", "manteau", "chapeau"]),
  ("C'est un outil ou un objet qu'on manipule.", ["marteau", "outil", "clé", "couteau", "machine"]),
  ("Ça meuble une pièce.", ["chaise", "table", "armoire", "lit", "meuble"]),
  ("Ça roule, vole ou navigue.", ["voiture", "train", "bateau", "avion", "camion"]),
  ("C'est un bâtiment ou un lieu construit.", ["maison", "église", "usine", "gare", "immeuble"]),
  ("C'est un élément du paysage.", ["montagne", "rivière", "forêt", "plaine", "vallée"]),
  ("Ça a rapport au temps qu'il fait.", ["pluie", "vent", "neige", "orage", "nuage"]),
  ("C'est une partie du corps.", ["main", "jambe", "épaule", "genou", "oreille", "dent", "doigt", "cou", "peau"]),
  ("Ça désigne une personne ou un métier.", ["médecin", "boulanger", "soldat", "ouvrier", "marchand"]),
  ("C'est une idée, pas un objet.", ["liberté", "courage", "peur", "espoir", "justice"]),
  ("Ça touche à la musique ou à l'art.", ["guitare", "chanson", "tableau", "orchestre", "danse"]),
  ("Ça se joue ou ça se pratique.", ["match", "jeu", "sport", "course", "équipe"]),
  ("C'est une matière ou une substance.", ["bois", "métal", "pierre", "tissu", "verre"]),
 ],
 "en": [
  ("It is an animal.", ["dog", "bird", "fish", "horse", "insect"]),
  ("It grows, it is a plant.", ["tree", "flower", "plant", "leaf", "root"]),
  ("You eat it or drink it.", ["bread", "cheese", "soup", "fruit", "drink"]),
  ("You wear it.", ["shirt", "trousers", "shoe", "coat", "hat"]),
  ("It is a tool or a handheld object.", ["hammer", "tool", "key", "knife", "machine"]),
  ("It furnishes a room.", ["chair", "table", "cupboard", "bed", "furniture"]),
  ("It rolls, flies or sails.", ["car", "train", "boat", "plane", "truck"]),
  ("It is a building or a built place.", ["house", "church", "factory", "station", "building"]),
  ("It belongs to the landscape.", ["mountain", "river", "forest", "plain", "valley"]),
  ("It has to do with the weather.", ["rain", "wind", "snow", "storm", "cloud"]),
  ("It is a part of the body.", ["hand", "leg", "shoulder", "knee", "ear", "tooth", "finger", "neck", "skin"]),
  ("It names a person or a trade.", ["doctor", "baker", "soldier", "worker", "merchant"]),
  ("It is an idea, not an object.", ["freedom", "courage", "fear", "hope", "justice"]),
  ("It has to do with music or art.", ["guitar", "song", "painting", "orchestra", "dance"]),
  ("It is played or practised.", ["match", "game", "sport", "race", "team"]),
  ("It is a material or a substance.", ["wood", "metal", "stone", "cloth", "glass"]),
 ],
 "es": [
  ("Es un animal.", ["perro", "pájaro", "pez", "caballo", "insecto"]),
  ("Crece, es vegetal.", ["árbol", "flor", "planta", "hoja", "raíz"]),
  ("Se come o se bebe.", ["pan", "queso", "sopa", "fruta", "bebida"]),
  ("Se lleva puesto.", ["camisa", "pantalón", "zapato", "abrigo", "sombrero"]),
  ("Es una herramienta o un objeto de mano.", ["martillo", "herramienta", "llave", "cuchillo", "máquina"]),
  ("Amuebla una habitación.", ["silla", "mesa", "armario", "cama", "mueble"]),
  ("Rueda, vuela o navega.", ["coche", "tren", "barco", "avión", "camión"]),
  ("Es un edificio o un lugar construido.", ["casa", "iglesia", "fábrica", "estación", "edificio"]),
  ("Forma parte del paisaje.", ["montaña", "río", "bosque", "llanura", "valle"]),
  ("Tiene que ver con el tiempo que hace.", ["lluvia", "viento", "nieve", "tormenta", "nube"]),
  ("Es una parte del cuerpo.", ["mano", "pierna", "hombro", "rodilla", "oreja", "diente", "dedo", "cuello", "piel"]),
  ("Designa a una persona o un oficio.", ["médico", "panadero", "soldado", "obrero", "comerciante"]),
  ("Es una idea, no un objeto.", ["libertad", "valor", "miedo", "esperanza", "justicia"]),
  ("Tiene que ver con la música o el arte.", ["guitarra", "canción", "cuadro", "orquesta", "danza"]),
  ("Se juega o se practica.", ["partido", "juego", "deporte", "carrera", "equipo"]),
  ("Es un material o una sustancia.", ["madera", "metal", "piedra", "tela", "vidrio"]),
 ],
 "it": [
  ("È un animale.", ["cane", "uccello", "pesce", "cavallo", "insetto"]),
  ("Cresce, è vegetale.", ["albero", "fiore", "pianta", "foglia", "radice"]),
  ("Si mangia o si beve.", ["pane", "formaggio", "zuppa", "frutta", "bevanda"]),
  ("Si indossa.", ["camicia", "pantalone", "scarpa", "cappotto", "cappello"]),
  ("È un attrezzo o un oggetto da tenere in mano.", ["martello", "attrezzo", "chiave", "coltello", "macchina"]),
  ("Arreda una stanza.", ["sedia", "tavolo", "armadio", "letto", "mobile"]),
  ("Rotola, vola o naviga.", ["automobile", "treno", "barca", "aereo", "camion"]),
  ("È un edificio o un luogo costruito.", ["casa", "chiesa", "fabbrica", "stazione", "palazzo"]),
  ("Fa parte del paesaggio.", ["montagna", "fiume", "bosco", "pianura", "valle"]),
  ("Riguarda il tempo che fa.", ["pioggia", "vento", "neve", "tempesta", "nuvola"]),
  ("È una parte del corpo.", ["mano", "gamba", "spalla", "ginocchio", "orecchio", "dente", "dito", "collo", "pelle"]),
  ("Indica una persona o un mestiere.", ["medico", "panettiere", "soldato", "operaio", "mercante"]),
  ("È un'idea, non un oggetto.", ["libertà", "coraggio", "paura", "speranza", "giustizia"]),
  ("Riguarda la musica o l'arte.", ["chitarra", "canzone", "quadro", "orchestra", "danza"]),
  ("Si gioca o si pratica.", ["partita", "gioco", "sport", "corsa", "squadra"]),
  ("È un materiale o una sostanza.", ["legno", "metallo", "pietra", "tessuto", "vetro"]),
 ],
 "de": [
  ("Es ist ein Tier.", ["Hund", "Vogel", "Fisch", "Pferd", "Insekt"]),
  ("Es wächst, es ist eine Pflanze.", ["Baum", "Blume", "Pflanze", "Blatt", "Wurzel"]),
  ("Man isst oder trinkt es.", ["Brot", "Käse", "Suppe", "Obst", "Getränk"]),
  ("Man trägt es am Körper.", ["Hemd", "Hose", "Schuh", "Mantel", "Hut"]),
  ("Es ist ein Werkzeug oder ein Gegenstand für die Hand.", ["Hammer", "Werkzeug", "Schlüssel", "Messer", "Maschine"]),
  ("Es steht als Möbel im Raum.", ["Stuhl", "Tisch", "Schrank", "Bett", "Möbel"]),
  ("Es rollt, fliegt oder fährt zur See.", ["Auto", "Zug", "Schiff", "Flugzeug", "Lastwagen"]),
  ("Es ist ein Gebäude oder ein gebauter Ort.", ["Haus", "Kirche", "Fabrik", "Bahnhof", "Gebäude"]),
  ("Es gehört zur Landschaft.", ["Berg", "Fluss", "Wald", "Ebene", "Tal"]),
  ("Es hat mit dem Wetter zu tun.", ["Regen", "Wind", "Schnee", "Gewitter", "Wolke"]),
  ("Es ist ein Körperteil.", ["Hand", "Bein", "Schulter", "Knie", "Ohr", "Zahn", "Finger", "Hals", "Haut"]),
  ("Es benennt einen Menschen oder einen Beruf.", ["Arzt", "Bäcker", "Soldat", "Arbeiter", "Kaufmann"]),
  ("Es ist ein Gedanke, kein Gegenstand.", ["Freiheit", "Mut", "Angst", "Hoffnung", "Gerechtigkeit"]),
  ("Es hat mit Musik oder Kunst zu tun.", ["Gitarre", "Lied", "Gemälde", "Orchester", "Tanz"]),
  ("Man spielt es oder man übt es aus.", ["Spiel", "Sport", "Rennen", "Mannschaft", "Wettkampf"]),
  ("Es ist ein Stoff oder ein Material.", ["Holz", "Metall", "Stein", "Gewebe", "Glas"]),
 ],
}

MASQUE = "\u2026\u2026\u2026"


def charger_lexique(code):
    Q = np.load(f"{VECTEURS}/{code}_mat.npy").astype(np.float32)
    Q /= np.linalg.norm(Q, axis=1, keepdims=True)
    mots = open(f"{VECTEURS}/{code}_mots.txt", encoding="utf-8").read().split("\n")
    return mots, {m: i for i, m in enumerate(mots)}, Q


def indices_categorie(code, cibles, idx, Q, seuil=0.28, marge=0.035):
    """
    Catégorie la plus proche, à deux conditions : dépasser un seuil, et devancer
    nettement la suivante. Sans cette marge, un mot sans catégorie évidente
    récoltait une étiquette au hasard, ce qui égare le joueur au lieu de l'aider.
    """
    sorties = {}
    centres, libelles = [], []
    for libelle, ancres in CATEGORIES[code]:
        vus = [idx[a] for a in ancres if a in idx]
        if len(vus) < 3:
            print(f"  [{code}] ancres insuffisantes pour : {libelle}")
            continue
        c = Q[vus].mean(axis=0)
        centres.append(c / np.linalg.norm(c))
        libelles.append(libelle)
    C = np.vstack(centres)
    for m in cibles:
        if m not in idx:
            continue
        s = C @ Q[idx[m]]
        o = np.argsort(-s)
        if s[o[0]] < seuil or s[o[0]] - s[o[1]] < marge:
            continue
        sorties[m] = [libelles[o[0]]]
    return sorties


def indices_phrases(code, cibles, maxi=2):
    """Phrases d'usage où le mot est remplacé par des points de suspension."""
    fichier = f"{PHRASES}/{CORPUS[code]}.tsv"
    if not os.path.exists(fichier):
        return {}
    besoin = {m.lower(): m for m in cibles}
    trouve = {m: [] for m in cibles}
    motif = re.compile(r"[^\W\d_]+", re.UNICODE)
    for ligne in open(fichier, encoding="utf-8", errors="replace"):
        parts = ligne.rstrip("\n").split("\t")
        if len(parts) < 3:
            continue
        phrase = parts[2]
        if not (35 <= len(phrase) <= 110):
            continue
        jetons = {j.lower() for j in motif.findall(phrase)}
        communs = jetons & besoin.keys()
        if len(communs) != 1:
            continue
        bas = next(iter(communs))
        mot = besoin[bas]
        if len(trouve[mot]) >= maxi:
            continue
        masquee = re.sub(rf"(?<![^\W\d_]){re.escape(bas)}(?![^\W\d_])", MASQUE,
                         phrase, flags=re.IGNORECASE)
        if MASQUE not in masquee or bas in masquee.lower():
            continue
        trouve[mot].append(masquee)
    return {m: v for m, v in trouve.items() if v}


def indices_definition(code, cibles):
    """
    Définitions rédigées à la main, dans outils/definitions/XX.json.
    Un contrôle refuse celles qui laissent filtrer le mot ou un dérivé évident :
    une définition qui contient sa propre entrée ne serait plus un indice.
    """
    chemin = os.path.join(RACINE, "outils/definitions", f"{code}.json")
    if not os.path.exists(chemin):
        return {}
    brut = json.load(open(chemin, encoding="utf-8"))
    motif = re.compile(r"[^\W\d_]+", re.UNICODE)

    def sans_accent(m):
        return "".join(c for c in unicodedata.normalize("NFD", m.lower())
                       if unicodedata.category(c) != "Mn")

    retenues, rejets = {}, []
    for mot, texte in brut.items():
        if mot not in cibles:
            rejets.append((mot, "hors liste de cibles"))
            continue
        racine = sans_accent(mot)[:max(4, len(mot) - 2)]
        fuite = next((j for j in motif.findall(texte)
                      if sans_accent(j).startswith(racine)), None)
        if fuite:
            rejets.append((mot, f"laisse filtrer « {fuite} »"))
            continue
        retenues[mot] = texte
    for mot, raison in rejets:
        print(f"  [{code}] définition écartée, {mot} : {raison}")
    return retenues


def construire(code):
    cibles = [l.strip() for l in
              open(f"{LEX}/cibles-{code}.txt", encoding="utf-8") if l.strip()]
    mots, idx, Q = charger_lexique(code)

    defs = indices_definition(code, set(cibles))
    cats = indices_categorie(code, cibles, idx, Q)
    phrases = indices_phrases(code, cibles)

    sortie = {}
    for m in cibles:
        liste = [{"t": "def", "x": defs[m]}] if m in defs else []
        liste += [{"t": "cat", "x": t} for t in cats.get(m, [])]
        liste += [{"t": "phrase", "x": p} for p in phrases.get(m, [])]
        if liste:
            sortie[m] = liste

    chemin = f"{LEX}/indices-{code}.json"
    json.dump(sortie, open(chemin, "w", encoding="utf-8"), ensure_ascii=False)
    couvert = sum(1 for m in cibles if m in sortie)
    print(f"[{code}] {couvert}/{len(cibles)} cibles pourvues "
          f"({len(defs)} définitions, {sum(1 for m in cibles if cats.get(m))} catégories, "
          f"{sum(1 for m in cibles if phrases.get(m))} phrases) — "
          f"{os.path.getsize(chemin)/1000:.0f} Ko")


if __name__ == "__main__":
    for code in (sys.argv[1:] or CORPUS.keys()):
        construire(code)
