#!/usr/bin/env python3
"""mobile_release_check: release-readiness checks for Expo/React Native, Flutter and native iOS/Android projects.

Usage: mobile_release_check.py [root]
Checks: app identifiers, version/build numbers, icon/splash, iOS usage strings for installed permission modules,
empty/generic usage strings, iOS privacy manifest, risky Android permissions, Sign in with Apple requirement,
EAS profiles and updates runtime version. Each finding: LEVEL rule where  message. Exit 1 on any ERROR.
"""
import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "lib"))
import bk  # noqa: E402

IGNORE_DIRS = {"node_modules", ".git", "build", "dist", "Pods", ".expo", "DerivedData", ".gradle", ".dart_tool"}
MODULE_KEYS = {
    "expo-camera": ["NSCameraUsageDescription"],
    "react-native-vision-camera": ["NSCameraUsageDescription"],
    "expo-image-picker": ["NSPhotoLibraryUsageDescription"],
    "expo-media-library": ["NSPhotoLibraryUsageDescription"],
    "expo-location": ["NSLocationWhenInUseUsageDescription"],
    "expo-contacts": ["NSContactsUsageDescription"],
    "expo-calendar": ["NSCalendarsUsageDescription", "NSCalendarsFullAccessUsageDescription"],
    "expo-local-authentication": ["NSFaceIDUsageDescription"],
    "expo-tracking-transparency": ["NSUserTrackingUsageDescription"],
    "expo-sensors": ["NSMotionUsageDescription"],
    "expo-audio": ["NSMicrophoneUsageDescription"],
    "react-native-ble-plx": ["NSBluetoothAlwaysUsageDescription"],
}
RISKY_ANDROID = ["READ_SMS", "RECEIVE_SMS", "SEND_SMS", "READ_CALL_LOG", "QUERY_ALL_PACKAGES", "MANAGE_EXTERNAL_STORAGE",
                 "ACCESS_BACKGROUND_LOCATION", "SYSTEM_ALERT_WINDOW", "REQUEST_INSTALL_PACKAGES", "USE_EXACT_ALARM", "BIND_ACCESSIBILITY_SERVICE"]
SOCIAL_LOGIN = re.compile(r"@react-native-google-signin|expo-auth-session|react-native-fbsdk|@invertase/react-native-apple|react-native-app-auth|google_sign_in|flutter_facebook_auth")
APPLE_LOGIN = re.compile(r"expo-apple-authentication|@invertase/react-native-apple-authentication|sign_in_with_apple|AuthenticationServices")
GENERIC_USAGE = re.compile(r"^\s*$|this app (needs|requires|uses)|needs access|\$\(PRODUCT_NAME\) (needs|would like)|allow access", re.I)


def read(root, rel):
    try:
        with open(os.path.join(root, rel), encoding="utf-8", errors="ignore") as f:
            return f.read()
    except OSError:
        return ""


def find(root, name_rx):
    return [f for f in bk.walk(root, ignore=IGNORE_DIRS, dot_dirs=True) if re.search(name_rx, f.rsplit("/", 1)[-1])]


def expo_checks(root, findings, deps):
    cfg_file = next((f for f in ("app.json", "app.config.json", "app.config.ts", "app.config.js") if os.path.exists(os.path.join(root, f))), None)
    if not cfg_file:
        return False
    text = read(root, cfg_file)
    cfg = {}
    if cfg_file.endswith(".json"):
        try:
            data = json.loads(text)
            cfg = data.get("expo", data)
        except json.JSONDecodeError:
            findings.append(("ERROR", "config-invalid", cfg_file, "Invalid JSON"))
    ios, android = cfg.get("ios", {}), cfg.get("android", {})
    has = lambda key, obj=None: (key in obj) if (obj is not None and cfg) else re.search(rf"\b{key}\b\s*:", text) is not None
    eas_text = read(root, "eas.json")
    auto = '"autoIncrement": true' in eas_text.replace(" ", "").replace('":true', '": true') or "autoIncrement" in eas_text
    if not has("bundleIdentifier", ios):
        findings.append(("ERROR", "no-bundle-id", cfg_file, "ios.bundleIdentifier missing"))
    if not has("package", android):
        findings.append(("ERROR", "no-android-package", cfg_file, "android.package missing"))
    if not has("version", cfg):
        findings.append(("ERROR", "no-version", cfg_file, "version missing"))
    if not auto and not (has("buildNumber", ios) and has("versionCode", android)):
        findings.append(("WARN", "no-build-number", cfg_file, "No buildNumber/versionCode and EAS autoIncrement off"))
    if not has("icon", cfg):
        findings.append(("ERROR", "no-icon", cfg_file, "App icon missing"))
    if not (has("splash", cfg) or "expo-splash-screen" in text):
        findings.append(("WARN", "no-splash", cfg_file, "Splash screen not configured"))
    if not (has("adaptiveIcon", android)):
        findings.append(("WARN", "no-adaptive-icon", cfg_file, "android.adaptiveIcon missing"))
    for module, keys in MODULE_KEYS.items():
        if module in deps:
            plugin_with_text = re.search(rf"\[\s*['\"]{re.escape(module)}['\"]\s*,\s*\{{[^\]]*ermission", text, re.S)
            if not any(k in text for k in keys) and not plugin_with_text:
                findings.append(("ERROR", "missing-usage-string", cfg_file, f"{module} installed but no {keys[0]} (ios.infoPlist or plugin permission option)"))
    for m in re.finditer(r"\"(NS\w+UsageDescription)\"\s*:\s*\"([^\"]*)\"", text):
        if GENERIC_USAGE.search(m.group(2)):
            findings.append(("WARN", "generic-usage-string", cfg_file, f"{m.group(1)} is empty/generic: explain the user benefit"))
    if not (has("privacyManifests", ios) or find(root, r"PrivacyInfo\.xcprivacy$")):
        findings.append(("WARN", "no-privacy-manifest", cfg_file, "No iOS privacy manifest (ios.privacyManifests or PrivacyInfo.xcprivacy)"))
    for perm in RISKY_ANDROID:
        if re.search(rf"android\.permission\.{perm}\b|['\"]{perm}['\"]", text):
            findings.append(("WARN", "risky-android-permission", cfg_file, f"{perm} needs a Play declaration/justification"))
    if "expo-updates" in deps and not has("runtimeVersion", cfg):
        findings.append(("WARN", "no-runtime-version", cfg_file, "expo-updates without runtimeVersion: OTA updates may hit incompatible builds"))
    if not eas_text:
        findings.append(("WARN", "no-eas-json", ".", "No eas.json build profiles"))
    elif '"production"' not in eas_text:
        findings.append(("WARN", "no-production-profile", "eas.json", "No production build profile"))
    return True


def native_checks(root, findings, deps_blob):
    for plist in find(root, r"^Info\.plist$"):
        text = read(root, plist)
        for key, val in re.findall(r"<key>(NS\w+UsageDescription)</key>\s*<string>([^<]*)</string>", text):
            if GENERIC_USAGE.search(val):
                findings.append(("ERROR" if not val.strip() else "WARN", "generic-usage-string", plist, f"{key} is empty/generic"))
    for manifest in find(root, r"^AndroidManifest\.xml$"):
        text = read(root, manifest)
        for perm in RISKY_ANDROID:
            if f"android.permission.{perm}" in text:
                findings.append(("WARN", "risky-android-permission", manifest, f"{perm} needs a Play declaration/justification"))
    if SOCIAL_LOGIN.search(deps_blob) and not APPLE_LOGIN.search(deps_blob):
        findings.append(("WARN", "sign-in-with-apple", ".", "Third-party social login without Sign in with Apple (App Store guideline 4.8, unless an exception applies)"))


def run(root):
    findings = []
    try:
        pkg = json.loads(read(root, "package.json") or "{}")
    except json.JSONDecodeError:
        pkg = {}
    deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
    deps_blob = " ".join(deps) + read(root, "pubspec.yaml") + read(root, "Podfile") + " ".join(
        read(root, f) for f in find(root, r"\.(swift|kt)$")[:200])
    is_expo = expo_checks(root, findings, deps)
    is_mobile = is_expo or "react-native" in deps or os.path.exists(os.path.join(root, "pubspec.yaml")) \
        or find(root, r"\.xcodeproj$|^AndroidManifest\.xml$|^Info\.plist$")
    if not is_mobile:
        return findings
    native_checks(root, findings, deps_blob)
    return findings


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("root", nargs="?", default=".")
    a = p.parse_args()
    findings = run(a.root)
    return bk.report(findings, "mobile_release_check", a.root)


if __name__ == "__main__":
    sys.exit(main())
