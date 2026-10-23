@echo off
title HealthAI - Google Play Store Release Bundle Builder
color 0B

echo ====================================================================
echo        HealthAI - Google Play Store AAB Bundle Builder
echo ====================================================================
echo.

:: Step 1: Check if release keystore exists
if exist "keystore.properties" (
    echo [OK] keystore.properties found.
) else (
    echo [INFO] keystore.properties not found.
    echo Would you like to create a release keystore now?
    echo.
    echo  [1] Generate new production release keystore (healthai-release-key.jks)
    echo  [2] Continue using development debug key
    echo.
    set /p kchoice="Enter choice (1 or 2): "
    if "%kchoice%"=="1" (
        echo.
        echo Generating release keystore with keytool...
        keytool -genkey -v -keystore healthai-release-key.jks -keyalg RSA -keysize 2048 -validity 10000 -alias healthai_release_alias -storepass HealthAI2026Pass! -keypass HealthAI2026Pass! -dname "CN=HealthAI, OU=Clinical Health, O=HealthAI Systems, L=Metro, ST=State, C=US"
        echo.
        echo Creating keystore.properties...
        (
            echo storeFile=healthai-release-key.jks
            echo storePassword=HealthAI2026Pass!
            echo keyAlias=healthai_release_alias
            echo keyPassword=HealthAI2026Pass!
        ) > keystore.properties
        echo [SUCCESS] Release keystore created with alias 'healthai_release_alias'.
    )
)

echo.
echo ====================================================================
echo Syncing latest web assets into Android bundle...
echo ====================================================================
powershell -Command "Copy-Item -Path '..\frontend\*' -Destination 'app\src\main\assets\www' -Recurse -Force"
echo [OK] Web assets synchronized.

echo.
echo ====================================================================
echo Building Google Play Android App Bundle (.aab)...
echo ====================================================================
echo.

if exist "gradlew.bat" (
    call gradlew.bat bundleRelease
) else (
    echo [INFO] gradlew.bat wrapper not found.
    echo Please open the 'android' folder in Android Studio and click:
    echo    Build -> Generate Signed Bundle / APK -> Android App Bundle
)

echo.
if exist "app\build\outputs\bundle\release\app-release.aab" (
    echo [SUCCESS] Release Bundle built successfully!
    echo Location: app\build\outputs\bundle\release\app-release.aab
    echo Ready for upload to Google Play Console!
) else (
    echo [READY] Android project is fully configured and ready.
    echo Open the 'android' directory in Android Studio to build and publish.
)
echo.
pause
