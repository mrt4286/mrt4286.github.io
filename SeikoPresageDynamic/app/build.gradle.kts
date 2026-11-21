plugins {
    id("com.android.application")
}

android {
    namespace = "com.mrt4286.seikopresage"
    compileSdk = 34

    defaultConfig {
        applicationId = "com.mrt4286.seikopresage"
        // WFF v2 -> Wear OS 5 (API 34). Galaxy Watch 7 ships with Wear OS 5.
        minSdk = 34
        targetSdk = 34
        versionCode = 1
        versionName = "1.0"
    }

    buildTypes {
        release {
            isMinifyEnabled = false
        }
    }
}

// No dependencies on purpose: WFF watch faces are declarative XML + image resources (hasCode="false").
