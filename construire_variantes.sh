#!/usr/bin/env bash
# Construit les six APK : une variante par langue, plus la variante multilingue.
#
# Chaque variante monolingue n'embarque que son propre lexique, ce qui lui
# permet d'aller beaucoup plus loin dans le corpus sans peser des centaines de
# mégaoctets. Les variantes portent des identifiants d'application distincts et
# peuvent donc cohabiter sur le même téléphone.
#
# Usage : ANDROID_HOME=/chemin/sdk ./construire_variantes.sh
set -euo pipefail

SDK="${ANDROID_HOME:?définis ANDROID_HOME}"
BT="$SDK/build-tools/34.0.0"
PLAT="$SDK/platforms/android-34/android.jar"
RACINE="$(cd "$(dirname "$0")" && pwd)"
SRC="$RACINE/app/src/main"
CLE="$RACINE/cle-thermot.jks"
SORTIE="$RACINE/build/variantes"
VERSION="4.3.0"
CODE=26
# lexiques allégés de la variante multilingue, produits par tronquer_lexique.py
LEX_MULTI="${LEX_MULTI:-/tmp/lexmulti}"

declare -A NOM=( [fr]="Thermot" [en]="Thermot EN" [es]="Thermot ES" [it]="Thermot IT" [de]="Thermot DE" )

# La variante française garde l'identifiant historique « fr.thermot.jeu » : elle
# se met donc à jour par-dessus les versions installées avant la 4.0, en
# conservant parties en cours, statistiques et réglages. Les autres variantes
# portent un suffixe et cohabitent avec elle.
declare -A PAQUET=( [fr]="" [en]=".en" [es]=".es" [it]=".it" [de]=".de" [multi]=".multi" )

rm -rf "$SORTIE"; mkdir -p "$SORTIE"

batir() {                       # $1 = variante, $2 = étiquette, $3 = suffixe de paquet
  local variante="$1" etiquette="$2" paquet="$3"
  local T="$RACINE/build/tmp-$variante"
  rm -rf "$T"; mkdir -p "$T/gen" "$T/classes" "$T/dex" "$T/assets/www" "$T/res"

  cp -r "$SRC/res/." "$T/res/"
  # tout sauf les lexiques, copiés ensuite selon la variante
  for f in "$SRC/assets/www"/*; do
    [ "$(basename "$f")" = "lexiques" ] || cp -r "$f" "$T/assets/www/"
  done
  mkdir -p "$T/assets/www/lexiques"

  if [ "$variante" = "multi" ]; then
    cp "$SRC/assets/www/lexiques"/{alias,cibles,indices,sensibles}-*.* "$T/assets/www/lexiques/"
    cp "$LEX_MULTI"/lexique-*.bin "$T/assets/www/lexiques/"
    echo 'window.LANGUE_UNIQUE = null;' > "$T/assets/www/variante.js"
  else
    for motif in lexique alias cibles indices sensibles; do
      cp "$SRC/assets/www/lexiques/$motif-$variante".* "$T/assets/www/lexiques/"
    done
    echo "window.LANGUE_UNIQUE = \"$variante\";" > "$T/assets/www/variante.js"
  fi

  sed -e "s/package=\"fr.thermot.jeu\"/package=\"fr.thermot.jeu$paquet\"/" \
      -e "s/android:name=\".MainActivity\"/android:name=\"fr.thermot.jeu.MainActivity\"/" \
      "$SRC/AndroidManifest.xml" > "$T/AndroidManifest.xml"
  sed -e "s|<string name=\"app_name\">[^<]*</string>|<string name=\"app_name\">$etiquette</string>|" \
      "$SRC/res/values/strings.xml" > "$T/res/values/strings.xml"

  "$BT/aapt2" compile --dir "$T/res" -o "$T/res.zip" >/dev/null
  "$BT/aapt2" link -o "$T/base.apk" -I "$PLAT" --manifest "$T/AndroidManifest.xml" \
      "$T/res.zip" --java "$T/gen" --min-sdk-version 21 --target-sdk-version 34 \
      --version-code "$CODE" --version-name "$VERSION" \
      -A "$T/assets" -0 .bin -0 .woff2 >/dev/null

  # le paquet « fr.thermot.jeu.xx » devient le chemin « fr/thermot/jeu/xx »
  local chemin_r; chemin_r="$(find "$T/gen" -name R.java | head -1)"
  javac -source 8 -target 8 -nowarn -bootclasspath "$PLAT" -cp "$PLAT" -d "$T/classes" \
      "$chemin_r" "$SRC/java/fr/thermot/jeu/MainActivity.java" 2>/dev/null
  "$BT/d8" --lib "$PLAT" --min-api 21 --output "$T/dex" $(find "$T/classes" -name "*.class") >/dev/null 2>&1

  (cd "$T" && cp dex/classes.dex . && zip -q -j base.apk classes.dex)
  "$BT/zipalign" -p -f 4 "$T/base.apk" "$T/aligne.apk"
  "$BT/apksigner" sign --v4-signing-enabled false --ks "$CLE" --ks-pass pass:thermot2026 --key-pass pass:thermot2026 \
      --out "$SORTIE/thermot-$variante-$VERSION.apk" "$T/aligne.apk"
  rm -rf "$T"
  printf "%-8s %s\n" "$variante" "$(du -h "$SORTIE/thermot-$variante-$VERSION.apk" | cut -f1)"
}

VARIANTES="${VARIANTES:-multi fr en es it de}"
for L in $VARIANTES; do
  if [ "$L" = "multi" ]; then
    batir multi "Thermot Multi" "${PAQUET[multi]}"
  else
    batir "$L" "${NOM[$L]}" "${PAQUET[$L]}"
  fi
done

echo
ls -lh "$SORTIE"
