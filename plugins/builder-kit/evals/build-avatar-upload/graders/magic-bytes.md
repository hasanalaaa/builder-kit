---
type: regex
target: { source: file, path: app/api/profile/avatar/route.ts }
pattern: 'magic|file-type|fileTypeFromBuffer|0x89|0xff,?\s*0xd8|\[0\]\s*===?\s*0x|signature'
flags: i
---
