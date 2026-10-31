# UX copy

Words are interface. Most confusing UIs are confusing sentences.

## 1. Principles

- Say what it does, in the user's words, not the system's ("Couldn't save your changes", not "Error 500: PUT /api/doc failed").
- Front-load: the important word first ("Invoice sent to Sara" not "Your request to send the invoice has been completed").
- Be specific: numbers, names, times ("Deleted 3 files", "Trial ends 12 May").
- Same thing, same word, everywhere (pick "project" or "workspace", never both).
- Short, but never vague. Cut filler words, keep meaning.
- Tone matches the moment: neutral for routine, warm for success, calm and helpful for errors, never jokes in failures involving money or data.

## 2. Patterns

| Element | Formula | Example (EN) | Example (AR) |
|---------|---------|--------------|--------------|
| Button | Verb + object | Create invoice | إنشاء فاتورة |
| Destructive confirm title | Question with object | Delete "Q3 report"? | حذف "تقرير الربع الثالث"؟ |
| Destructive confirm body | Consequence | This removes it for everyone and can't be undone. | سيُحذف للجميع ولا يمكن التراجع. |
| Destructive confirm button | Repeat the verb | Delete report | حذف التقرير |
| Error | What happened + how to fix | Card was declined. Try another card or contact your bank. | رُفضت البطاقة. جرّب بطاقة أخرى أو تواصل مع البنك. |
| Field error | What's needed | Enter an email like name@example.com | أدخل بريدًا مثل name@example.com |
| Empty state | What + why + action | No invoices yet. Create your first one to get paid faster. [Create invoice] | لا توجد فواتير بعد. أنشئ أول فاتورة. [إنشاء فاتورة] |
| Success | Result + next | Invoice sent. We'll tell you when it's paid. | أُرسلت الفاتورة. سنُعلمك عند الدفع. |
| Loading | What's happening | Uploading 2 of 5… | جارٍ رفع 2 من 5… |
| Permission | Why + who | Only admins can change billing. Ask Sara (admin). | تعديل الفوترة للمشرفين فقط. |
| Tooltip | Clarifies, never essential | Shown to customers on invoices | |

## 3. Errors

- Never blame ("You entered an invalid…" → "Enter a date after today").
- Never expose internals (stack traces, SQL, IDs) — also a security issue (launch-security 20).
- Always give a next step: retry, edit, contact, or wait (with time).
- Keep the user's input after an error.

## 4. Arabic copy

- Write Arabic natively, don't translate word by word. Check with a native speaker for marketing copy.
- Choose a register and keep it: Modern Standard Arabic (فصحى مبسطة) for product UI; Gulf/local dialect only for deliberate brand voice in marketing.
- Gender: prefer forms that avoid gendering ("أدخل" vs "أدخلي") — use neutral nouns ("إدخال البريد"), imperative masculine as conventional default, or gender selection when the product knows the user's preference. Be consistent.
- Plurals: Arabic has singular, dual, plural (3–10) and 11+ forms. Use ICU MessageFormat plural rules (`zero, one, two, few, many, other`) — never "${n} ملفات" for all n.
- Punctuation: Arabic comma (،), question mark (؟), semicolon (؛). Quotes «» or "".
- Numbers and dates per locale (`Intl.NumberFormat`, `Intl.DateTimeFormat('ar-SA')` etc.); decide Latin vs Arabic-Indic digits once.
- Leave room: Arabic strings can be shorter or longer than English; never fixed-width buttons.

## 5. Voice sheet (put in DESIGN.md)

```
Voice: <3 traits, e.g. clear, warm, confident>
We say: <examples> · We don't say: <examples>
Terms: <glossary: canonical words for core concepts, AR + EN>
```
