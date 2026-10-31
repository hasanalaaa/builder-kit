#!/usr/bin/env python3
"""legal_check: product-side compliance signals in a web or mobile codebase (not legal advice).

Usage: legal_check.py [root]
Checks: privacy policy and terms pages, account deletion and data export when accounts exist,
consent handling when analytics/ads load, third-party embeds that leak IPs before consent.
Each finding: LEVEL rule where  message. Exit 1 on any ERROR.
"""
import argparse
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "lib"))
import bk  # noqa: E402

IGNORE_DIRS = {"node_modules", ".git", "dist", "build", ".next", "out", "coverage", "vendor", ".venv", "venv", "__pycache__", ".turbo", ".expo"}
TEXT_EXT = (".ts", ".tsx", ".js", ".jsx", ".mjs", ".py", ".vue", ".svelte", ".astro", ".html", ".md", ".mdx", ".json", ".dart", ".swift", ".kt")
PRIVACY_ROUTE = re.compile(r"privacy|خصوصية|datenschutz|confidentialite", re.I)
TERMS_ROUTE = re.compile(r"(^|/|-)(terms|tos|conditions|legal|الشروط)", re.I)
AUTH = re.compile(r"signUp\(|sign_up|createUserWithEmailAndPassword|auth\.signUp|supabase\.auth|next-auth|@auth/|@clerk/|better-auth|firebase/auth|lucia|django\.contrib\.auth|fastapi_users|passport\.", re.I)
DELETE_ACCOUNT = re.compile(r"delete[_-]?account|deleteAccount|delete_user|deleteUser|auth\.admin\.deleteUser|account/delete|حذف الحساب|removeAccount|closeAccount", re.I)
EXPORT = re.compile(r"export[_-]?(my[_-]?)?data|download[_-]?(my[_-]?)?data|data[_-]?export|exportUserData|تنزيل بياناتي|تصدير البيانات", re.I)
TRACKERS = re.compile(r"gtag\(|googletagmanager|fbq\(|connect\.facebook\.net|hotjar|clarity\.ms|posthog\.init|mixpanel\.init|amplitude\.init|segment\.com/analytics|snap\.licdn|tiktok|@vercel/analytics|react-ga|googleadservices|doubleclick", re.I)
CONSENT = re.compile(r"consent|cookiebot|onetrust|klaro|cookieyes|iubenda|osano|termly|usercentrics|cookie-?banner|opt_out_capturing|optOut|cookieless", re.I)
GFONTS = re.compile(r"fonts\.googleapis\.com|fonts\.gstatic\.com")
YOUTUBE = re.compile(r"youtube\.com/embed/")
MAPS = re.compile(r"google\.com/maps/embed|maps\.googleapis\.com/maps/api/js")


def walk(root):
    return bk.walk(root, None, IGNORE_DIRS)


def run(root):
    files = walk(root)
    texts = {}
    for f in files:
        if f.endswith(TEXT_EXT):
            try:
                with open(os.path.join(root, f), encoding="utf-8", errors="ignore") as fh:
                    texts[f] = fh.read()
            except OSError:
                pass  # unreadable file: skip it
    blob = "\n".join(texts.values())
    findings = []
    is_product = any(f.endswith((".tsx", ".jsx", ".vue", ".svelte", ".astro", ".html", ".dart", ".swift", ".kt")) for f in files)
    if not is_product:
        return findings
    has_privacy = any(PRIVACY_ROUTE.search(f) for f in files) or re.search(r"href=[\"'{][^\"'}]*privacy|privacyPolicyUrl|privacy_policy_url", blob, re.I)
    has_terms = any(TERMS_ROUTE.search(f) for f in files) or re.search(r"href=[\"'{][^\"'}]*/(terms|tos)\b", blob, re.I)
    has_auth = bool(AUTH.search(blob))
    if not has_privacy:
        findings.append(("ERROR", "no-privacy-policy", ".", "No privacy policy page/link found (required by law in most regions and by app stores)"))
    if not has_terms and has_auth:
        findings.append(("WARN", "no-terms", ".", "No terms of service page/link found"))
    if has_auth and not DELETE_ACCOUNT.search(blob):
        findings.append(("ERROR", "no-account-deletion", ".", "Accounts exist but no account deletion flow (GDPR/PDPL right to erasure; App Store and Google Play require in-app deletion)"))
    if has_auth and not EXPORT.search(blob):
        findings.append(("WARN", "no-data-export", ".", "No data export/download flow (right of access/portability)"))
    if TRACKERS.search(blob) and not CONSENT.search(blob):
        findings.append(("WARN", "trackers-no-consent", ".", "Analytics/ads trackers without visible consent management"))
    for rx, rule, msg in ((GFONTS, "google-fonts-cdn", "Google Fonts loaded from Google's CDN shares visitor IPs: self-host fonts (next/font, fontsource)"),
                          (YOUTUBE, "youtube-embed", "YouTube embed sets cookies before consent: use youtube-nocookie.com or click-to-load"),
                          (MAPS, "maps-embed", "Google Maps embed loads before consent: use a static image + click-to-load")):
        hits = [f for f, t in texts.items() if rx.search(t) and not f.endswith(".md")]
        if hits:
            findings.append(("WARN", rule, hits[0], msg))
    return findings


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("root", nargs="?", default=".")
    a = p.parse_args()
    findings = run(a.root)
    return bk.report(findings, "legal_check", a.root, note=" (signals only, not legal advice)")


if __name__ == "__main__":
    sys.exit(main())
