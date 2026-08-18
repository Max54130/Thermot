#!/usr/bin/env python3
"""
Construit l'asset binaire du moteur semantique (v2).
- filtre les pluriels et les doublons non accentues, qui deviennent des alias
- quantifie les vecteurs normalises en int8

Source des vecteurs : fastText cc.fr.300 (Common Crawl + Wikipedia)
https://fasttext.cc/docs/en/crawl-vectors.html  -- licence CC BY-SA 3.0
"""
import os, re, struct, unicodedata
import numpy as np

SRC = "data/fr_head.vec"
MAX_KEEP = 45000
DIM = 300
MOTIF = re.compile(r"^[a-zàâäçéèêëîïôöùûüÿœæ]{3,18}$")

def sans_accent(m):
    return "".join(c for c in unicodedata.normalize("NFD", m)
                   if unicodedata.category(c) != "Mn")

def main():
    mots, vecs = [], []
    with open(SRC, encoding="utf-8", errors="replace") as f:
        f.readline()
        for ligne in f:
            parts = ligne.rstrip("\n").split(" ")
            m = parts[0]
            if not MOTIF.match(m) or len(parts) < DIM + 1:
                continue
            v = np.asarray(parts[1:DIM + 1], dtype=np.float32)
            n = np.linalg.norm(v)
            if n < 1e-6:
                continue
            mots.append(m)
            vecs.append(v / n)
    M = np.vstack(vecs)
    rang = {m: i for i, m in enumerate(mots)}
    print(f"candidats bruts : {len(mots)}")

    garde = [True] * len(mots)
    alias = {}   # forme ecartee -> forme conservee

    # 1) pluriels : "chats" -> "chat", "chevaux" laisse tel quel
    for i, m in enumerate(mots):
        if not m.endswith(("s", "x")) or len(m) < 5:
            continue
        base = m[:-1]
        j = rang.get(base)
        if j is None or not garde[j]:
            continue
        # on n'ecarte le pluriel que si le singulier est plus frequent
        if j < i and float(M[i] @ M[j]) > 0.55:
            garde[i] = False
            alias[m] = base

    # 2) doublons non accentues : "hopital" -> "hôpital"
    for i, m in enumerate(mots):
        if not garde[i]:
            continue
        d = sans_accent(m)
        if d == m:
            continue
        j = rang.get(d)
        if j is None or not garde[j]:
            continue
        # on garde la forme la plus frequente des deux
        if float(M[i] @ M[j]) > 0.60:
            if i < j:
                garde[j] = False
                alias[d] = m
            else:
                garde[i] = False
                alias[m] = d

    gardes = [i for i in range(len(mots)) if garde[i]][:MAX_KEEP]
    final = [mots[i] for i in gardes]
    Mf = M[gardes]
    ens = set(final)
    alias = {k: v for k, v in alias.items() if v in ens and k not in ens}

    # 3) alias supplementaires : toute forme desaccentuee pointe vers sa forme accentuee
    for m in final:
        d = sans_accent(m)
        if d != m and d not in ens and d not in alias:
            alias[d] = m

    print(f"mots conserves : {len(final)}   alias : {len(alias)}")

    Q = np.clip(np.rint(Mf * 127.0), -127, 127).astype(np.int8)
    Qf = Q.astype(np.float32)
    Qf /= np.linalg.norm(Qf, axis=1, keepdims=True)
    perte = np.abs((Qf * Mf).sum(axis=1) - 1.0)
    print(f"perte cosinus moyenne {perte.mean():.6f} / max {perte.max():.6f}")

    os.makedirs("out", exist_ok=True)
    bloc = "\n".join(final).encode("utf-8")
    with open("out/lexique.bin", "wb") as f:
        f.write(b"MOTX")
        f.write(struct.pack("<IHI", len(final), DIM, len(bloc)))
        f.write(bloc)
        f.write(Q.tobytes())
    with open("out/alias.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(f"{k}\t{v}" for k, v in sorted(alias.items())))
    np.save("out/mat.npy", Q)
    with open("out/mots.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(final))
    print("lexique.bin : %.1f Mo" % (os.path.getsize("out/lexique.bin") / 1e6))
    print("alias.txt   : %.1f Ko" % (os.path.getsize("out/alias.txt") / 1e3))

if __name__ == "__main__":
    main()
