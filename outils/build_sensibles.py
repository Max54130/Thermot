#!/usr/bin/env python3
"""
Construit, pour chaque langue, la liste des mots à caractère sexuel ou vulgaire.

Méthode : on part d'amorces explicites, incontestables, on prend le centre de
leurs vecteurs, et on retient les mots qui s'en approchent au-delà d'un seuil.
Le seuil est fixé à 0,40 : en dessous, la liste attrape des mots parfaitement
innocents comme « douceur », « jalousie » ou « cancer », dont la proximité tient
au contexte des phrases et non au sens.

Une liste de rattrapage retire les faux positifs repérés à la relecture, et une
liste d'ajouts force des mots que le voisinage ne remonte pas.

Sortie : lexiques/sensibles-XX.txt, un mot par ligne.
"""
import os, sys
import numpy as np

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEX = os.path.join(RACINE, "app/src/main/assets/www/lexiques")
VECTEURS = os.environ.get("VECTEURS", os.path.join(RACINE, "..", "data"))
SEUIL = 0.40

AMORCES = {
"fr": "bite chatte salope pute enculé baiser bander orgasme masturbation porno sexe éjaculation vagin pénis fellation sodomie",
"en": "dick pussy cunt whore slut fuck orgasm masturbation porn sex ejaculation vagina penis blowjob anal boobs",
"es": "polla coño puta zorra follar orgasmo masturbación porno sexo eyaculación vagina pene mamada anal tetas",
"it": "cazzo figa troia puttana scopare orgasmo masturbazione porno sesso eiaculazione vagina pene pompino anale tette",
"de": "Schwanz Fotze Muschi Nutte Hure ficken Orgasmus Masturbation Porno Sex Ejakulation Vagina Penis Blasen anal Titten",
}

# Faux positifs relus : le voisinage les remonte, le sens ne le justifie pas.
INNOCENTS = {
"fr": """amour amoureux amoureuse câlin baiser embrasser romance couple mariage amant amante
amateur amatrice abstinence adultère fidélité séduction charme tendresse
fille demoiselle rousse nue célibataire homme femme douche pompe tube moule gaine
jalousie métaphore cancer douceur violence violente violement raide mûres asperge andouillette
psychanalyse gynécologue utérus urinaire piercing latex lingerie jarretelle nuisette jupette
tabou fantasmes excitation soumission chasteté pilosité célibat spasmes incontinence glotte
homosexuel homosexuelle bisexuels transsexualisme prostitué prostituer""",
"en": """love lover romance couple marriage kiss kissing hug cuddle amateur abstinence
adultery seduction charm tenderness
girl woman man lady single shower pump tube naked nude jealousy metaphor cancer
sweetness violence lingerie latex piercing taboo fantasy excitement submission chastity
homosexual bisexual transsexual prostitute gynecologist uterus urinary""",
"es": """amor amante romance pareja matrimonio beso abrazo caricia aficionado abstinencia
adulterio seducción encanto ternura
chica mujer hombre soltera ducha bomba tubo desnuda celos metáfora cáncer dulzura
violencia lencería látex tabú fantasía excitación sumisión castidad homosexual bisexual
transexual prostituta ginecólogo útero urinario""",
"it": """amore amante romanticismo coppia matrimonio bacio abbraccio carezza amatore astinenza
adulterio seduzione fascino tenerezza
ragazza donna uomo single doccia pompa tubo nuda gelosia metafora cancro dolcezza
violenza lingerie lattice tabù fantasia eccitazione sottomissione castità omosessuale
bisessuale transessuale prostituta ginecologo utero urinario""",
"de": """Liebe Liebhaber Romantik Paar Ehe Kuss Umarmung Zärtlichkeit Amateur Enthaltsamkeit
Ehebruch Verführung Charme
Mädchen Frau Mann Single Dusche Pumpe Rohr nackt Eifersucht Metapher Krebs Sanftheit
Gewalt Dessous Latex Tabu Fantasie Erregung Unterwerfung Keuschheit homosexuell bisexuell
transsexuell Prostituierte Frauenarzt Gebärmutter""",
}

# Injures et grossièretés que le champ sexuel ne remonte pas forcément.
AJOUTS = {
"fr": "connard connasse abruti crétin débile enfoiré foutre merde merdique chier chiant conne",
"en": "asshole bastard motherfucker bullshit shit crap dumbass jackass wanker twat",
"es": "gilipollas cabrón mierda joder capullo imbécil pendejo boludo",
"it": "stronzo stronza coglione bastardo merda cazzata idiota deficiente",
"de": "Arschloch Scheiße Scheiss Wichser Mistkerl Idiot Vollidiot Bastard",
}


def construire(code):
    Q = np.load(f"{VECTEURS}/{code}_mat.npy").astype(np.float32)
    Q /= np.linalg.norm(Q, axis=1, keepdims=True)
    mots = open(f"{VECTEURS}/{code}_mots.txt", encoding="utf-8").read().split("\n")
    idx = {m: i for i, m in enumerate(mots)}

    graines = [idx[m] for m in AMORCES[code].split() if m in idx]
    centre = Q[graines].mean(axis=0)
    centre /= np.linalg.norm(centre)
    proches = Q @ centre

    innocents = {m.lower() for m in INNOCENTS[code].split()}
    retenus = {mots[i] for i in np.where(proches > SEUIL)[0]
               if mots[i].lower() not in innocents}
    retenus |= {m for m in AJOUTS[code].split() if m in idx}
    retenus |= {mots[i] for i in graines}

    # les mots cibles ne doivent jamais être bloqués : ils sont déjà filtrés en amont
    cibles = {l.strip() for l in open(f"{LEX}/cibles-{code}.txt", encoding="utf-8") if l.strip()}
    conflits = sorted(retenus & cibles)
    retenus -= cibles

    liste = sorted(retenus)
    open(f"{LEX}/sensibles-{code}.txt", "w", encoding="utf-8").write("\n".join(liste))
    print(f"[{code}] {len(liste)} mots filtrés sur {len(mots)} "
          f"({100*len(liste)/len(mots):.1f} %)"
          + (f" | cibles en conflit, retirées de la liste : {conflits}" if conflits else ""))
    return liste


if __name__ == "__main__":
    for code in (sys.argv[1:] or ["fr", "en", "es", "it", "de"]):
        liste = construire(code)
        print("   échantillon :", " ".join(liste[:12]), "…")
