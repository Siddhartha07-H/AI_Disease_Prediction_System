# ProGuard & R8 Optimization Rules for HealthAI Release Builds

# Preserve JavaScript Interface methods
-keepclassmembers class * {
    @android.webkit.JavascriptInterface <methods>;
}

# Keep WebAppInterface methods
-keep class com.healthai.diseaseprediction.WebAppInterface {
    <methods>;
}

# Preserve AndroidX and Material Design components
-keep class androidx.appcompat.** { *; }
-keep class com.google.android.material.** { *; }

# Allow obfuscation of internal helper classes while keeping line numbers for crash reporting
-keepattributes SourceFile,LineNumberTable
-renamesourcefileattribute SourceFile
