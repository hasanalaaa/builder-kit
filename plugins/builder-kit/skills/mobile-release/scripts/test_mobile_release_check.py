#!/usr/bin/env python3
"""Self-test for mobile_release_check. Run: python3 test_mobile_release_check.py"""
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mobile_release_check as mrc  # noqa: E402

BAD_APP = {"expo": {"name": "Rawdah", "ios": {"infoPlist": {"NSPhotoLibraryUsageDescription": "This app needs access"}},
                    "android": {"permissions": ["android.permission.READ_SMS"]}}}
GOOD_APP = {"expo": {
    "name": "Rawdah", "version": "1.0.0", "icon": "./assets/icon.png", "splash": {"image": "./assets/splash.png"},
    "runtimeVersion": {"policy": "appVersion"},
    "ios": {"bundleIdentifier": "com.rawdah.app", "privacyManifests": {"NSPrivacyAccessedAPITypes": []},
            "infoPlist": {"NSCameraUsageDescription": "Rawdah uses the camera to share photos of today's activities with parents."}},
    "android": {"package": "com.rawdah.app", "adaptiveIcon": {"foregroundImage": "./assets/adaptive.png"}},
}}


def run_on(app, deps, eas=None):
    with tempfile.TemporaryDirectory() as d:
        with open(os.path.join(d, "app.json"), "w") as f:
            json.dump(app, f)
        with open(os.path.join(d, "package.json"), "w") as f:
            json.dump({"dependencies": deps}, f)
        if eas:
            with open(os.path.join(d, "eas.json"), "w") as f:
                json.dump(eas, f)
        return {x[1] for x in mrc.run(d)}


if __name__ == "__main__":
    got = run_on(BAD_APP, {"expo": "x", "expo-camera": "x", "expo-updates": "x", "@react-native-google-signin/google-signin": "x"})
    want = {"no-bundle-id", "no-android-package", "no-version", "no-build-number", "no-icon", "no-splash", "no-adaptive-icon",
            "missing-usage-string", "generic-usage-string", "no-privacy-manifest", "risky-android-permission",
            "no-runtime-version", "no-eas-json", "sign-in-with-apple"}
    assert want <= got, sorted(want - got)
    got = run_on(GOOD_APP, {"expo": "x", "expo-camera": "x", "expo-updates": "x", "expo-apple-authentication": "x"},
                 {"cli": {"appVersionSource": "remote"}, "build": {"production": {"autoIncrement": True}}})
    assert not got, sorted(got)
    print("selftest OK")
