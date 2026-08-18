plugins {
    id("com.android.application")
}

android {
    namespace = "fr.thermot.jeu"
    compileSdk = 34

    defaultConfig {
        applicationId = "fr.thermot.jeu"
        minSdk = 21
        targetSdk = 34
        versionCode = 26
        versionName = "4.3.0"
    }

    // le lexique est déjà compact : le compresser ne ferait que ralentir le chargement
    androidResources {
        noCompress += listOf("bin", "woff2")
    }

    buildTypes {
        release {
            isMinifyEnabled = false
            proguardFiles(getDefaultProguardFile("proguard-android-optimize.txt"), "proguard-rules.pro")
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
}
