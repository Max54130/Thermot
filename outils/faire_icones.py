#!/usr/bin/env python3
"""
Produit les icônes Android à partir du logo fourni.

Deux jeux :
- icônes héritées (mipmap-*/ic_launcher.png) : le logo entier, coins rendus
  transparents pour que le masque du lanceur ne laisse pas d'angles noirs ;
- icône adaptative (Android 8+) : le contenu détouré du fond, ramené dans la
  zone sûre, posé sur un aplat de la couleur de marque.
"""
import os
import numpy as np
from PIL import Image, ImageDraw

SOURCE = "thermot/outils/logo_source.png"
BASE = "thermot/app/src/main/res"
FOND = (11, 16, 36)
DENSITES = {"mdpi": 1, "hdpi": 1.5, "xhdpi": 2, "xxhdpi": 3, "xxxhdpi": 4}


def charger():
    return Image.open(SOURCE).convert("RGBA").resize((1024, 1024), Image.LANCZOS)


def coins_transparents(img, rayon_ratio=0.225):
    """Découpe le carré arrondi : le lanceur applique ensuite son propre masque."""
    t = img.size[0]
    masque = Image.new("L", (t, t), 0)
    ImageDraw.Draw(masque).rounded_rectangle(
        [0, 0, t - 1, t - 1], radius=int(t * rayon_ratio), fill=255)
    sortie = img.copy()
    sortie.putalpha(masque)
    return sortie


def detourer(img, seuil=70):
    """
    Retire le fond bleu nuit et le pourtour noir, ne garde que le texte blanc
    et la bande colorée. Deux critères combinés : l'écart au bleu de fond, et
    la clarté, car le noir extérieur est lui aussi loin du bleu de fond.
    """
    a = np.asarray(img.convert("RGB")).astype(np.float32)
    fond = a[120:200, 120:200].reshape(-1, 3).mean(axis=0)
    ecart = np.clip((np.linalg.norm(a - fond, axis=2) - 30) / seuil, 0, 1)
    clarte = np.clip((a.max(axis=2) - 70) / 60, 0, 1)
    alpha = ecart * clarte
    return Image.fromarray(np.dstack([a, alpha * 255]).astype(np.uint8), "RGBA")


def cadrer(img, part=0.64):
    """Recentre le contenu dans la zone sûre de l'icône adaptative."""
    contenu = img.crop(img.getbbox())
    t, cible = 1024, int(1024 * part)
    ratio = min(cible / contenu.width, cible / contenu.height)
    contenu = contenu.resize((max(1, int(contenu.width * ratio)),
                              max(1, int(contenu.height * ratio))), Image.LANCZOS)
    toile = Image.new("RGBA", (t, t), (0, 0, 0, 0))
    toile.paste(contenu, ((t - contenu.width) // 2, (t - contenu.height) // 2), contenu)
    return toile


def main():
    logo = charger()

    herite = coins_transparents(logo)
    for nom, k in DENSITES.items():
        d = f"{BASE}/mipmap-{nom}"
        os.makedirs(d, exist_ok=True)
        px = int(48 * k)
        herite.resize((px, px), Image.LANCZOS).save(f"{d}/ic_launcher.png")

    premier_plan = cadrer(detourer(logo))
    for nom, k in DENSITES.items():
        px = int(108 * k)
        premier_plan.resize((px, px), Image.LANCZOS).save(
            f"{BASE}/mipmap-{nom}/ic_premier_plan.png")

    os.makedirs("out", exist_ok=True)
    logo.save("out/icone_1024.png")
    apercu = Image.new("RGBA", (1024, 1024), FOND + (255,))
    apercu.alpha_composite(premier_plan)
    apercu.save("out/icone_adaptative_apercu.png")
    print("icônes générées")


if __name__ == "__main__":
    main()
