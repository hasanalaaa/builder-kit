---
type: regex
target: { source: file, path: 'app/api/link-preview/route.ts' }
pattern: 'redirect\s*:\s*["''](manual|error)["'']|maxRedirects|follow\s*:\s*0|request-filtering-agent|ssrf-req-filter'
flags: i
---
