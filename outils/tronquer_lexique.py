#!/usr/bin/env python3
"""
Dérive un lexique plus léger d'un lexique complet, sans relire le corpus.

Les mots sont rangés par fréquence décroissante dans le fichier : une troncature
aux N premiers garde donc le vocabulaire le plus courant. Les mots cibles sont
conservés même s'ils tombent au-delà de N, sinon le mot du jour disparaîtrait.

Usage : tronquer_lexique.py <code> <nombre de mots> <dossier de sortie>
"""
import os, struct, sys
import numpy as np

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEX = os.path.join(RACINE, "app/src/main/assets/www/lexiques")


def lire(chemin):
    b = open(chemin, "rb").read()
    assert b[:4] == b"MOTX"
    n, dim, taille = struct.unpack("<IHI", b[4:14])
    p = 14
    mots = b[p:p + taille].decode("utf-8").split("\n")
    p += taille
    vect = np.frombuffer(b, dtype=np.int8, count=n * dim, offset=p).reshape(n, dim)
    p += n * dim
    normes = np.frombuffer(b, dtype=np.float32, count=n, offset=p)
    return mots, vect, normes, dim


def ecrire(chemin, mots, vect, normes, dim):
    bloc = "\n".join(mots).encode("utf-8")
    with open(chemin, "wb") as f:
        f.write(b"MOTX")
        f.write(struct.pack("<IHI", len(mots), dim, len(bloc)))
        f.write(bloc)
        f.write(vect.tobytes())
        f.write(normes.astype(np.float32).tobytes())


def tronquer(code, garde, sortie):
    mots, vect, normes, dim = lire(f"{LEX}/lexique-{code}.bin")
    cibles = {l.strip() for l in open(f"{LEX}/cibles-{code}.txt", encoding="utf-8") if l.strip()}

    gardes = list(range(min(garde, len(mots))))
    deja = set(gardes)
    for i, m in enumerate(mots):
        if i >= garde and m in cibles and i not in deja:
            gardes.append(i)
    gardes.sort()

    os.makedirs(sortie, exist_ok=True)
    ecrire(f"{sortie}/lexique-{code}.bin",
           [mots[i] for i in gardes], vect[gardes], normes[gardes], dim)
    manquantes = cibles - {mots[i] for i in gardes}
    taille = os.path.getsize(f"{sortie}/lexique-{code}.bin") / 1e6
    print(f"[{code}] {len(mots)} -> {len(gardes)} mots, {taille:.1f} Mo"
          + (f" | ATTENTION cibles perdues : {sorted(manquantes)[:5]}" if manquantes else ""))


if __name__ == "__main__":
    code, garde, sortie = sys.argv[1], int(sys.argv[2]), sys.argv[3]
    tronquer(code, garde, sortie)
