#!/usr/bin/env bash
# Construit et signe Thermot sans Gradle : aapt2, javac, d8, zipalign, apksigner.
# Usage : ANDROID_HOME=/chemin/vers/sdk ./construire.sh
set -euo pipefail

SDK="${ANDROID_HOME:?définis ANDROID_HOME vers ton SDK Android}"
BT="$SDK/build-tools/34.0.0"
PLAT="$SDK/platforms/android-34/android.jar"
RACINE="$(cd "$(dirname "$0")" && pwd)"
SRC="$RACINE/app/src/main"
B="$RACINE/build"
VERSION="4.3.0"
CODE=26
CLE="$RACINE/cle-thermot.jks"

for outil in "$BT/aapt2" "$BT/d8" "$BT/zipalign" "$BT/apksigner" "$PLAT"; do
  [ -e "$outil" ] || { echo "introuvable : $outil"; exit 1; }
done

rm -rf "$B"
mkdir -p "$B/gen" "$B/classes" "$B/dex"

echo "1/5  ressources"
"$BT/aapt2" compile --dir "$SRC/res" -o "$B/res.zip"
"$BT/aapt2" link -o "$B/base.apk" -I "$PLAT" \
  --manifest "$SRC/AndroidManifest.xml" "$B/res.zip" \
  --java "$B/gen" --min-sdk-version 21 --target-sdk-version 34 \
  --version-code "$CODE" --version-name "$VERSION" \
  -A "$SRC/assets" -0 .bin -0 .woff2

echo "2/5  compilation Java"
javac -source 8 -target 8 -nowarn -bootclasspath "$PLAT" -cp "$PLAT" \
  -d "$B/classes" "$B/gen/fr/thermot/jeu/R.java" \
  "$SRC/java/fr/thermot/jeu/MainActivity.java"

echo "3/5  dex"
# note : d8 8.2.2 échoue sur les classes internes non statiques,
# le code n'en contient donc aucune.
"$BT/d8" --lib "$PLAT" --min-api 21 --output "$B/dex" $(find "$B/classes" -name "*.class")

echo "4/5  assemblage"
cd "$B"
cp dex/classes.dex .
zip -q -j base.apk classes.dex
"$BT/zipalign" -p -f 4 base.apk thermot-aligne.apk

echo "5/5  signature"
if [ ! -f "$CLE" ]; then
  keytool -genkeypair -v -keystore "$CLE" -alias thermot \
    -keyalg RSA -keysize 2048 -validity 10950 \
    -storepass thermot2026 -keypass thermot2026 \
    -dname "CN=Thermot, OU=Perso, O=Thermot, L=Nancy, C=FR"
fi
"$BT/apksigner" sign --ks "$CLE" \
  --ks-pass pass:thermot2026 --key-pass pass:thermot2026 \
  --out "$B/thermot-$VERSION.apk" thermot-aligne.apk
"$BT/apksigner" verify "$B/thermot-$VERSION.apk"

echo
echo "APK prêt : $B/thermot-$VERSION.apk"
ls -lh "$B/thermot-$VERSION.apk"
