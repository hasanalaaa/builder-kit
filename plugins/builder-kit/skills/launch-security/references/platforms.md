# Platform-specific hardening: P1–P5

Apply SKILL.md §1 "Rules of work". Load the section for each platform the project ships on, in addition to the 27 checks (which apply to every backend).

---

## P1 · Mobile apps (iOS / Android / React Native / Expo / Flutter) · OWASP MASVS

**The app binary is public.** Anyone can decompile it, read its strings, and call its backend directly. All security decisions live on the server.

- **No secrets in the bundle** (02): no API secrets, no service_role keys, no signing secrets in code, `.plist`, `strings.xml`, `.env` baked into the build, or `EXPO_PUBLIC_*`. Use a backend route for anything secret.
- **Secure storage:** tokens in iOS **Keychain** / Android **Keystore** (`expo-secure-store`, `flutter_secure_storage`, `react-native-keychain`). Never AsyncStorage/SharedPreferences/UserDefaults for tokens or personal data.
- **Network:** HTTPS only. iOS App Transport Security on (no `NSAllowsArbitraryLoads`); Android `usesCleartextTraffic=false` + Network Security Config. Certificate pinning only if you can manage rotation safely (a wrong pin bricks the app); prefer pinning to the public key with a backup pin.
- **Deep links / universal links / app links:** validate every parameter; never perform actions (payments, account changes, login) from a link without user confirmation; verify domain association files.
- **WebViews:** disable JavaScript unless needed; never expose native bridges to untrusted content; allowlist loaded origins; no `file://` access for remote content.
- **Exported components (Android):** activities, services, receivers and providers are `exported=false` unless they must be public; protect public ones with permissions.
- **App integrity:** for abuse-sensitive actions (rewards, payments, sign-up spam), verify **App Attest / DeviceCheck** (iOS) and **Play Integrity API** (Android) tokens on the server. Root/jailbreak detection is a speed bump, not a control.
- **Data on device:** don't log personal data (device logs are readable); exclude sensitive screens from screenshots/app switcher where appropriate; clear caches on logout; disable keyboard caching on sensitive fields.
- **Builds:** release builds strip debug flags and logs; obfuscation (R8/ProGuard, Flutter `--obfuscate`) as a speed bump; signing keys stored safely; OTA updates (Expo Updates, CodePush) are code-signed.
- **Biometrics:** use them to unlock a Keychain/Keystore item, not as a boolean `isAuthenticated` check the app trusts.
- **Store rules:** run store-compliance.md S1–S10.

---

## P2 · Desktop apps (Electron / Tauri / native)

- **Electron:** `contextIsolation: true`, `nodeIntegration: false`, `sandbox: true`, `webSecurity: true`; expose only a minimal, validated API through `contextBridge`; never load remote content into a privileged window; strict CSP; validate all IPC messages (sender + payload); block `window.open`/navigation to unexpected origins (`setWindowOpenHandler`, `will-navigate`); `shell.openExternal` only with allowlisted `https:` URLs; keep Electron updated (it bundles Chromium); enable Electron fuses to disable `RunAsNode` and similar in production.
- **Tauri:** minimal capabilities/permissions per window; scope filesystem and shell access; strict CSP; validate command inputs on the Rust side.
- **Updates:** auto-updates over HTTPS and **signature-verified**; code-sign and notarize binaries (Apple notarization, Windows Authenticode).
- **Local data:** secrets in the OS keychain (Keychain, Windows Credential Manager, libsecret), not plain files; sensible file permissions.
- **Local servers:** don't open localhost HTTP servers without auth and Origin checks (other websites can call them).

---

## P3 · Browser extensions

- Minimal `permissions` and `host_permissions`; prefer `activeTab` and optional permissions.
- Manifest V3; no remote code; strict extension CSP.
- Treat content-script input from web pages as hostile; validate every message between content scripts and the service worker; check `sender`.
- Never inject untrusted HTML into pages (07); don't store tokens in `chrome.storage.sync`.

---

## P4 · AI, LLM and agent features (OWASP LLM Top 10 + Agentic AI Top 10)

Extends B1.
- **Prompt injection (direct and indirect)** is the #1 risk and is not fully solvable by prompting. Contain it by design: the model only ever has the current user's permissions; untrusted content (web pages, emails, files, tool results, RAG documents) is marked as data and never treated as instructions; high-impact actions need human confirmation.
- **Excessive agency / tool misuse:** each tool has the narrowest scope (read-only where possible, allowlisted parameters, per-user auth on the server side of the tool); no generic "run any SQL / shell / HTTP" tools; rate-limit and budget tool calls.
- **Code execution:** model-generated code runs only in an isolated sandbox (separate container/VM, no network or allowlisted egress, no secrets, CPU/memory/time limits).
- **Sensitive information disclosure:** no secrets or other users' data in system prompts or context; system prompts are assumed to leak eventually.
- **RAG / vector stores:** enforce per-user/tenant access filters at retrieval time, not after; sanitize ingested documents; track sources.
- **Memory and context poisoning:** long-term agent memory is scoped per user, validated before saving, reviewable and deletable.
- **Output handling:** model output is untrusted (07, 10, B2): escape/sanitize before rendering, parameterize before querying, validate before calling URLs or tools.
- **MCP servers and agent plugins:** install only from trusted sources; pin versions; review requested permissions; treat tool descriptions and results as untrusted input; never give an agent credentials broader than the task.
- **Multi-agent systems:** authenticate messages between agents; a compromised agent must not be able to escalate through another.
- **Cost and DoS:** auth, per-user quotas, max tokens, max tool-loop iterations, provider spend caps (B5).
- **Evaluation:** keep a regression suite of known jailbreak/injection prompts for the app's own features and run it in CI.
- **Supply chain:** model and dataset provenance; only load model weights in safe formats (e.g. safetensors, not pickle).

---

## P5 · Public APIs, SDKs and CLIs

- **API inventory** (API9): a list/OpenAPI spec of every endpoint and version; old versions retired, not left running unprotected.
- API keys for third parties: hashed at rest, shown once, scoped, revocable, with per-key rate limits and last-used timestamps.
- Unsafe consumption (API10): validate and size-limit responses from third-party APIs as if they were user input; TLS verified; timeouts.
- Webhooks you send: sign them (HMAC with timestamp), include an event ID, retry with backoff, let receivers verify.
- CLIs: never print secrets; store tokens in the OS keychain; validate file paths; don't execute downloaded code without verification.
