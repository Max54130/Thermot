package fr.thermot.jeu;

import android.app.Activity;
import android.content.res.AssetManager;
import android.graphics.Color;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.view.View;
import android.view.WindowManager;
import android.webkit.WebResourceRequest;
import android.webkit.WebResourceResponse;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;

import java.io.IOException;
import java.io.InputStream;
import java.util.HashMap;
import java.util.Map;

/**
 * Thermot : coquille native minimale.
 * L'interface et le moteur sémantique vivent dans app/src/main/assets/www.
 * Les fichiers sont servis sous une origine https virtuelle, ce qui donne
 * accès à fetch() et à localStorage sans autoriser le moindre accès réseau.
 */
public class MainActivity extends Activity {

    private static final String HOTE = "thermot.local";
    private static final String RACINE = "https://" + HOTE + "/";
    WebView vue;

    @Override
    protected void onCreate(Bundle etat) {
        super.onCreate(etat);
        getWindow().setStatusBarColor(Color.parseColor("#070A14"));   // couleurs du splash,
        getWindow().setNavigationBarColor(Color.parseColor("#070A14")); // la page les ajuste ensuite
        getWindow().setSoftInputMode(WindowManager.LayoutParams.SOFT_INPUT_ADJUST_RESIZE);
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            getWindow().getDecorView().setSystemUiVisibility(View.SYSTEM_UI_FLAG_LAYOUT_STABLE);
        }

        vue = new WebView(this);
        WebSettings p = vue.getSettings();
        p.setJavaScriptEnabled(true);
        p.setDomStorageEnabled(true);
        p.setAllowFileAccess(false);
        p.setAllowContentAccess(false);
        p.setSupportZoom(false);
        p.setBuiltInZoomControls(false);
        p.setMediaPlaybackRequiresUserGesture(true);
        vue.setBackgroundColor(Color.parseColor("#070A14"));
        vue.setOverScrollMode(View.OVER_SCROLL_NEVER);

        vue.setWebViewClient(new ClientLocal(this));
        vue.addJavascriptInterface(new Pont(this), "Pont");

        setContentView(vue);
        vue.loadUrl(RACINE + "index.html");
    }

    /**
     * Seul lien entre la page et le système : la page annonce son thème,
     * les barres système s'y accordent. Le contenu servi étant entièrement
     * embarqué, aucun code extérieur ne peut appeler ce pont.
     */
    public static class Pont {
        private final MainActivity hote;

        Pont(MainActivity hote) { this.hote = hote; }

        @android.webkit.JavascriptInterface
        public void theme(boolean clair) {
            hote.runOnUiThread(new MajBarres(hote, clair));
        }
    }

    /** Applique la couleur des barres système sur le fil principal. */
    private static class MajBarres implements Runnable {
        private final MainActivity hote;
        private final boolean clair;

        MajBarres(MainActivity hote, boolean clair) { this.hote = hote; this.clair = clair; }

        @Override
        public void run() {
            // exactement la couleur de --barre dans la feuille de style,
            // pour qu'aucun liseré n'apparaisse entre les barres et la page
            int fond = Color.parseColor(clair ? "#F3F5FD" : "#0F1630");
            hote.getWindow().setStatusBarColor(fond);
            hote.getWindow().setNavigationBarColor(fond);
            hote.vue.setBackgroundColor(fond);
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
                View racine = hote.getWindow().getDecorView();
                int drapeaux = racine.getSystemUiVisibility();
                if (clair) drapeaux |= View.SYSTEM_UI_FLAG_LIGHT_STATUS_BAR;
                else drapeaux &= ~View.SYSTEM_UI_FLAG_LIGHT_STATUS_BAR;
                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                    if (clair) drapeaux |= View.SYSTEM_UI_FLAG_LIGHT_NAVIGATION_BAR;
                    else drapeaux &= ~View.SYSTEM_UI_FLAG_LIGHT_NAVIGATION_BAR;
                }
                racine.setSystemUiVisibility(drapeaux);
            }
        }
    }

    /** Aiguille les requêtes de la page vers les fichiers embarqués. */
    private static class ClientLocal extends WebViewClient {
        private final MainActivity hote;

        ClientLocal(MainActivity hote) { this.hote = hote; }

        @Override
        public WebResourceResponse shouldInterceptRequest(WebView v, WebResourceRequest req) {
            Uri u = req.getUrl();
            // rien d'extérieur n'est servi : l'appli ne demande d'ailleurs
            // aucune permission réseau dans le manifeste
            if (!HOTE.equals(u.getHost())) return hote.refus();
            return hote.servir(u.getPath());
        }

        @Override
        public boolean shouldOverrideUrlLoading(WebView v, WebResourceRequest req) {
            return !HOTE.equals(req.getUrl().getHost());   // rien ne s'ouvre hors de l'appli
        }
    }

    /** Sert un fichier de assets/www sous l'origine virtuelle. */
    WebResourceResponse servir(String chemin) {
        if (chemin == null || chemin.contains("..")) return refus();
        if (chemin.startsWith("/")) chemin = chemin.substring(1);
        if (chemin.isEmpty()) chemin = "index.html";
        AssetManager assets = getAssets();
        try {
            InputStream flux = assets.open("www/" + chemin);
            Map<String, String> entetes = new HashMap<>();
            entetes.put("Cache-Control", "no-store");
            String type = typeMime(chemin);
            String encodage = type.startsWith("text/") || type.contains("javascript") ? "utf-8" : null;
            WebResourceResponse rep = new WebResourceResponse(type, encodage, flux);
            rep.setResponseHeaders(entetes);
            return rep;
        } catch (IOException e) {
            return refus();
        }
    }

    WebResourceResponse refus() {
        return new WebResourceResponse("text/plain", "utf-8",
                new java.io.ByteArrayInputStream("introuvable".getBytes()));
    }

    private static String typeMime(String nom) {
        if (nom.endsWith(".html")) return "text/html";
        if (nom.endsWith(".css")) return "text/css";
        if (nom.endsWith(".js")) return "text/javascript";
        if (nom.endsWith(".json")) return "application/json";
        if (nom.endsWith(".txt")) return "text/plain";
        if (nom.endsWith(".woff2")) return "font/woff2";
        if (nom.endsWith(".png")) return "image/png";
        if (nom.endsWith(".svg")) return "image/svg+xml";
        return "application/octet-stream";
    }

    /**
     * La touche retour ferme d'abord le panneau ouvert dans la page :
     * chaque panneau ajoute une entrée d'historique côté page.
     */
    @Override
    public void onBackPressed() {
        if (vue != null && vue.canGoBack()) vue.goBack();
        else finish();
    }

    @Override
    protected void onDestroy() {
        if (vue != null) {
            vue.loadUrl("about:blank");
            vue.destroy();
            vue = null;
        }
        super.onDestroy();
    }
}
