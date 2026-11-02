// Browser half of verify_ui.py: reads {root, pkg, axe, base, routes, out} as JSON on stdin,
// opens every route at each viewport and prints one JSON line: {pages: [...]} or {error, message}.
// The Python side turns the raw facts into findings, so all judgement stays testable without Node.
import { createRequire } from "node:module";
import { readFileSync } from "node:fs";
import path from "node:path";

const cfg = JSON.parse(readFileSync(0, "utf8"));
// Resolve from the project, not from this plugin folder: the project owns the Playwright version.
const { chromium } = createRequire(path.join(cfg.root, "package.json"))(cfg.pkg);
const VIEWPORTS = [{ width: 375, height: 812 }, { width: 1280, height: 800 }];
const slug = (route) => route.replace(/^\/+|\/+$/g, "").replace(/[^\w.-]+/g, "_") || "index";

function inPage() {
  const W = window.innerWidth;
  const de = document.documentElement;
  let overflow = null;
  if (de.scrollWidth > W) {
    let worst = null;
    let right = W;
    for (const el of document.body ? document.body.querySelectorAll("*") : []) {
      const r = el.getBoundingClientRect().right;
      if (r > right + 0.5) { right = r; worst = el; }
    }
    const name = worst ? worst.tagName.toLowerCase() + (worst.id ? "#" + worst.id : "") + (worst.classList[0] ? "." + worst.classList[0] : "") : "";
    overflow = { width: de.scrollWidth, el: name };
  }
  const imgs = [...document.images];
  const src = (i) => i.getAttribute("src") || i.currentSrc || "(no src)";
  return {
    overflow,
    lang: de.lang || "",
    dir: de.dir || (document.body && document.body.dir) || "",
    imgNoAlt: imgs.filter((i) => !i.hasAttribute("alt")).map(src),
    imgBroken: imgs.filter((i) => i.complete && i.getAttribute("src") && !i.naturalWidth).map(src),
  };
}

let browser;
try {
  browser = await chromium.launch();
} catch (e) {
  console.log(JSON.stringify({ error: "browser", message: String(e.message).split("\n")[0] }));
  process.exit(3);
}
const pages = [];
try {
  for (const vp of VIEWPORTS) {
    const ctx = await browser.newContext({ viewport: vp, bypassCSP: true });
    for (const route of cfg.routes) {
      const page = await ctx.newPage();
      const r = { route, viewport: vp.width, console: [], pageErrors: [], requests: [], navError: null };
      page.on("console", (m) => { if (m.type() === "error") r.console.push(m.text()); });
      page.on("pageerror", (e) => r.pageErrors.push(String(e.message || e)));
      page.on("requestfailed", (q) => r.requests.push({ url: q.url(), method: q.method(), failure: q.failure()?.errorText || "failed" }));
      page.on("response", (s) => { if (s.status() >= 400) r.requests.push({ url: s.url(), method: s.request().method(), status: s.status() }); });
      try {
        await page.goto(cfg.base + route, { waitUntil: "load", timeout: 30000 });
        // Requests fired on load (fetch in an effect) finish after "load"; dev servers may never go idle,
        // so a timeout here is expected and the checks run anyway. bk-ignore: promise-catch-noop
        await page.waitForLoadState("networkidle", { timeout: 5000 }).catch(() => {});
        Object.assign(r, await page.evaluate(inPage));
        if (cfg.axe) {
          await page.addScriptTag({ content: readFileSync(cfg.axe, "utf8") });
          r.axe = await page.evaluate(async () => (await window.axe.run(document, { resultTypes: ["violations"] })).violations
            .map((v) => ({ id: v.id, impact: v.impact, help: v.help, nodes: v.nodes.length, target: String(v.nodes[0]?.target?.[0] ?? "") })));
        }
        r.shot = path.join(cfg.out, `${slug(route)}-${vp.width}.png`);
        await page.screenshot({ path: r.shot, fullPage: true });
      } catch (e) {
        r.navError = String(e.message).split("\n")[0];
      }
      pages.push(r);
      await page.close();
    }
    await ctx.close();
  }
} finally {
  await browser.close();
}
console.log(JSON.stringify({ pages }));
