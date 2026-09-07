# -*- coding: utf-8 -*-
import io, os

"""Build worksheet.html (print) + worksheet.pdf from words.js.

words.js is the single source of truth, shared with the app (index.html).

    python3 build-worksheet.py          # rewrite worksheet.html
    python3 build-worksheet.py --pdf    # also re-render worksheet.pdf via headless Chrome
"""
import json, re, shutil, subprocess, sys, time, pathlib

HERE = pathlib.Path(__file__).resolve().parent
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"


def load_words():
    """Evaluate words.js in node and hand the data back as JSON."""
    js = 'global.window={};require(%s);console.log(JSON.stringify(window.WORDS))' % json.dumps(
        str(HERE / "words.js"))
    out = subprocess.run(["node", "-e", js], capture_output=True, text=True, check=True).stdout
    data = json.loads(out)
    for i, it in enumerate(data, 1):
        assert len(it["options"]) == 4, "item %d: needs exactly 4 options" % i
        assert len(set(it["options"])) == 4, "item %d: duplicate options" % i
        assert it["answer"] in it["options"], "item %d: answer missing from options" % i
        for o in it["options"]:
            assert o.startswith(it["onset"]), "item %d: %r does not start with %r" % (i, o, it["onset"])
    return data


ITEMS = [(it["onset"], it["pic"], it["options"], it["answer"]) for it in load_words()]

PER_SHEET = 4
out = io.StringIO()
w = out.write

w('''<title>צלילים פותחים לנבו</title>
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Suez+One&family=Heebo:wght@400;500;700;900&family=Assistant:wght@400;600;700&display=swap">
<style>
:root{
  --paper:#FFFFFF;
  --desk:#EDEAE3;
  --ink:#1B2430;
  --ink-soft:#5E6B7A;
  --ink-faint:#93A0AE;
  --rule:#D6DBE1;
  --rule-soft:#E8EBEF;
  --accent:#2F6F5E;
  --accent-wash:#E9F1EE;
  --key:#8A6A1F;
  --key-wash:#F6F0DF;
}
@media (prefers-color-scheme: dark){
  :root:not([data-theme="light"]){
    --paper:#FFFFFF; --desk:#15181C;
    --ink:#1B2430; --ink-soft:#5E6B7A; --ink-faint:#93A0AE;
    --rule:#D6DBE1; --rule-soft:#E8EBEF;
    --accent:#2F6F5E; --accent-wash:#E9F1EE;
    --key:#8A6A1F; --key-wash:#F6F0DF;
  }
}
:root[data-theme="dark"]{
  --paper:#FFFFFF; --desk:#15181C;
  --ink:#1B2430; --ink-soft:#5E6B7A; --ink-faint:#93A0AE;
  --rule:#D6DBE1; --rule-soft:#E8EBEF;
  --accent:#2F6F5E; --accent-wash:#E9F1EE;
  --key:#8A6A1F; --key-wash:#F6F0DF;
}

*{box-sizing:border-box}
body{
  background:var(--desk);
  color:var(--ink);
  font-family:"Assistant","Arial Hebrew",Arial,sans-serif;
  direction:rtl;
  margin:0;
  padding:22px 14px 60px;
}

/* screen-only strip */
.bar{
  max-width:210mm;margin:0 auto 20px;
  display:flex;flex-wrap:wrap;align-items:baseline;gap:10px 16px;
  color:var(--ink-soft);
}
.bar h1{
  margin:0;font-family:"Suez One","Arial Hebrew",serif;font-weight:400;
  font-size:24px;color:var(--ink);letter-spacing:.01em;
}
:root[data-theme="dark"] .bar h1,
:root[data-theme="dark"] .bar{color:#E7EAEE}
@media (prefers-color-scheme: dark){
  :root:not([data-theme="light"]) .bar h1,
  :root:not([data-theme="light"]) .bar{color:#E7EAEE}
}
.bar p{margin:0;font-size:14.5px;line-height:1.5}
.bar .btn{
  font:600 14px/1 "Assistant",Arial,sans-serif;color:var(--paper);
  background:var(--accent);border:0;border-radius:999px;padding:9px 18px;cursor:pointer;
  margin-inline-start:auto;
}
.bar .btn:focus-visible{outline:2.5px solid #7FB3A3;outline-offset:2px}

.sheet{
  width:210mm;min-height:297mm;margin:0 auto 20px;
  background:var(--paper);padding:15mm 13mm 12mm;
  box-shadow:0 1px 2px rgba(27,36,48,.10),0 10px 30px rgba(27,36,48,.13);
  display:flex;flex-direction:column;
}

/* masthead — first sheet only */
.masthead{border-bottom:2.5px solid var(--ink);padding-bottom:5mm;margin-bottom:7mm}
.eyebrow{
  font-size:11.5px;font-weight:700;letter-spacing:.16em;color:var(--accent);
  text-transform:uppercase;margin:0 0 2mm;
}
.masthead h2{
  margin:0;font-family:"Suez One","Arial Hebrew",serif;font-weight:400;
  font-size:34px;line-height:1.15;text-wrap:balance;
}
.howto{
  margin:4mm 0 0;font-size:14.5px;line-height:1.55;color:var(--ink-soft);max-width:62ch;
}
.howto b{color:var(--ink);font-weight:700}
.meta{display:flex;gap:12mm;margin-top:5mm;font-size:14px;color:var(--ink-soft)}
.meta span{display:flex;align-items:baseline;gap:2mm}
.meta i{font-style:normal;font-weight:700;color:var(--ink)}
.fill{display:inline-block;min-width:32mm;border-bottom:1.4px solid var(--rule)}

/* running header — later sheets */
.runhead{
  display:flex;justify-content:space-between;align-items:baseline;
  border-bottom:1.4px solid var(--rule);padding-bottom:3mm;margin-bottom:7mm;
  font-size:12.5px;color:var(--ink-faint);letter-spacing:.06em;
}
.runhead b{color:var(--ink-soft);font-weight:700;letter-spacing:.14em}

.grid{display:grid;grid-template-columns:1fr 1fr;gap:7mm;flex:1}

.item{
  border:1.4px solid var(--rule);border-radius:3mm;
  padding:5mm 5mm 6mm;
  display:flex;flex-direction:column;align-items:center;gap:3.5mm;
}
.itemtop{
  width:100%;display:flex;justify-content:space-between;align-items:center;
}
.num{
  font:700 13px/1 "Assistant",Arial,sans-serif;color:var(--ink-soft);
  border:1.4px solid var(--rule);border-radius:50%;
  width:7.5mm;height:7.5mm;display:flex;align-items:center;justify-content:center;
  font-variant-numeric:tabular-nums;flex:none;
}
.onset{
  font-family:"Heebo","Arial Hebrew",Arial,sans-serif;font-weight:700;font-size:15px;
  color:var(--accent);background:var(--accent-wash);
  border-radius:1.5mm;padding:1mm 3mm;letter-spacing:.02em;
}
.pic{font-size:62px;line-height:1.05;height:22mm;display:flex;align-items:center}
.words{display:grid;grid-template-columns:1fr 1fr;gap:2.5mm;width:100%}
.word{
  display:flex;align-items:center;gap:2.5mm;
  border:1.4px solid var(--rule-soft);border-radius:2mm;
  padding:2.4mm 3mm;
  font-family:"Heebo","Arial Hebrew",Arial,sans-serif;
  font-size:23px;font-weight:500;line-height:1.25;
}
.bubble{
  width:4.6mm;height:4.6mm;border:1.5px solid var(--ink-faint);border-radius:50%;flex:none;
}

/* answer key */
.keyhead{border-bottom:2.5px solid var(--key);padding-bottom:4mm;margin-bottom:6mm}
.keyhead .eyebrow{color:var(--key)}
.keyhead h2{margin:0;font-family:"Suez One","Arial Hebrew",serif;font-weight:400;font-size:28px}
.keygrid{display:grid;grid-template-columns:1fr 1fr;gap:0 10mm}
.keyrow{
  display:flex;align-items:center;gap:3.5mm;
  padding:2.6mm 0;border-bottom:1px solid var(--rule-soft);
}
.keyrow .n{
  font:700 12px/1 "Assistant",Arial,sans-serif;color:var(--ink-faint);
  width:6mm;text-align:center;font-variant-numeric:tabular-nums;flex:none;
}
.keyrow .e{font-size:22px;line-height:1;width:9mm;text-align:center;flex:none}
.keyrow .wd{
  font-family:"Heebo","Arial Hebrew",Arial,sans-serif;font-weight:700;font-size:19px;
  color:var(--key);background:var(--key-wash);border-radius:1.5mm;padding:.6mm 2.5mm;
}
.keynote{margin:6mm 0 0;font-size:13.5px;line-height:1.6;color:var(--ink-soft);max-width:60ch}

.foot{
  margin-top:auto;padding-top:5mm;border-top:1px solid var(--rule-soft);
  display:flex;justify-content:space-between;
  font-size:11.5px;color:var(--ink-faint);letter-spacing:.04em;
}
.foot span{font-variant-numeric:tabular-nums}

@media print{
  @page{size:A4;margin:0}
  body{background:#fff;margin:0;padding:0}
  .bar{display:none}
  .sheet{margin:0;box-shadow:none;min-height:0;height:296mm;page-break-after:always;break-after:page}
  .sheet:last-child{page-break-after:auto;break-after:auto}
}
@media screen and (max-width:820px){
  .sheet{width:100%;min-height:0;padding:20px 16px 24px}
  .grid{grid-template-columns:1fr}
  .keygrid{grid-template-columns:1fr}
  .pic{height:auto;font-size:54px}
}
@media (prefers-reduced-motion:reduce){*{transition:none!important;animation:none!important}}
</style>

<div class="bar">
  <h1>צלילים פותחים לנבו</h1>
  <p>24 תרגילים · 6 עמודים + דף תשובות · A4</p>
  <button class="btn" onclick="window.print()">הדפסה</button>
</div>
''')

total = len(ITEMS)
sheets = [ITEMS[i:i+PER_SHEET] for i in range(0, total, PER_SHEET)]
n_sheets = len(sheets)

for si, chunk in enumerate(sheets):
    w('<div class="sheet">\n')
    if si == 0:
        w('''  <header class="masthead">
    <p class="eyebrow">קריאה · צליל פותח</p>
    <h2>איזו מילה מתאימה לתמונה?</h2>
    <p class="howto">בכל תרגיל <b>כל ארבע המילים מתחילות באותו צליל</b> — האות הפותחת (או שתי האותיות הראשונות) זהה בכולן, והצליל המשותף מופיע בריבוע הירוק. לכן צריך לקרוא את המילה <b>עד הסוף</b>: ההבדל בין המילים הוא באות האחרונה. קראו את ארבע המילים בקול, הסתכלו על התמונה, וצבעו את העיגול שליד המילה הנכונה.</p>
    <div class="meta">
      <span><i>שם:</i> נבו</span>
      <span><i>תאריך:</i> <span class="fill"></span></span>
    </div>
  </header>
''')
    else:
        w('  <div class="runhead"><b>צליל פותח · איזו מילה מתאימה לתמונה?</b><span>נבו</span></div>\n')

    w('  <div class="grid">\n')
    for ii, (onset, emoji, opts, _corr) in enumerate(chunk):
        idx = si*PER_SHEET + ii + 1
        w('    <div class="item">\n')
        w('      <div class="itemtop"><span class="onset">%s־</span><span class="num">%d</span></div>\n' % (onset, idx))
        w('      <div class="pic" role="img" aria-label="תמונה לתרגיל %d">%s</div>\n' % (idx, emoji))
        w('      <div class="words">\n')
        for o in opts:
            w('        <div class="word"><span class="bubble"></span>%s</div>\n' % o)
        w('      </div>\n    </div>\n')
    w('  </div>\n')
    w('  <div class="foot"><span>צליל פותח · דף עבודה</span><span>עמוד %d מתוך %d</span></div>\n' % (si+1, n_sheets))
    w('</div>\n')

# answer key
w('''<div class="sheet">
  <header class="keyhead">
    <p class="eyebrow">למבוגר · לא להדפיס לילד</p>
    <h2>דף תשובות</h2>
  </header>
  <div class="keygrid">
''')
for i, (onset, emoji, opts, corr) in enumerate(ITEMS, 1):
    w('    <div class="keyrow"><span class="n">%d</span><span class="e">%s</span><span class="wd">%s</span></div>\n' % (i, emoji, corr))
w('''  </div>
  <p class="keynote">אם נבו מתבלבל, כסו את סוף המילה באצבע וקראו יחד רק את הצליל הפותח — כל האפשרויות יישמעו זהות. אחר כך גלו אות אחת בכל פעם. ההבדל תמיד באות האחרונה.</p>
  <div class="foot"><span>צליל פותח · דף תשובות</span><span>24 תרגילים</span></div>
</div>
''')

# --- assemble a standalone printable document -------------------------------
raw = out.getvalue()

raw = raw.replace(".bar .btn:focus-visible", """.bar .actions{margin-inline-start:auto;display:flex;gap:8px;align-items:center}
.bar .btn{margin-inline-start:0}
.bar .ghost{
  background:transparent;color:var(--accent);border:1.5px solid var(--accent);
  text-decoration:none;display:inline-flex;align-items:center;
}
.bar .btn:focus-visible""", 1)

raw = raw.replace(
    '  <button class="btn" onclick="window.print()">\u05d4\u05d3\u05e4\u05e1\u05d4</button>\n',
    '  <span class="actions">'
    '<a class="btn ghost" href="index.html">\u2190 \u05dc\u05de\u05e9\u05d7\u05e7</a>'
    '<button class="btn" onclick="window.print()">\u05d4\u05d3\u05e4\u05e1\u05d4</button>'
    '</span>\n', 1)

head, rest = raw.split("</style>", 1)
doc = ('<!doctype html>\n<html lang="he" dir="rtl">\n<head>\n<meta charset="utf-8">\n'
       '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
       + head + "</style>\n</head>\n<body>\n" + rest.lstrip("\n") + "</body>\n</html>\n")

html_path = HERE / "worksheet.html"
html_path.write_text(doc, encoding="utf-8")
print("wrote %s (%d bytes) - %d items, %d sheets + answer key"
      % (html_path.name, len(doc), total, n_sheets))

if "--pdf" in sys.argv:
    pdf_path = HERE / "worksheet.pdf"
    profile = HERE / ".chrome-tmp"
    if pdf_path.exists():
        pdf_path.unlink()
    proc = subprocess.Popen([CHROME, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                             "--virtual-time-budget=15000",
                             "--user-data-dir=" + str(profile),
                             "--print-to-pdf=" + str(pdf_path),
                             html_path.as_uri()],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    # headless Chrome writes the PDF but does not always exit on its own, so poll and stop it
    for _ in range(60):
        time.sleep(2)
        if pdf_path.exists() and pdf_path.stat().st_size > 0:
            time.sleep(2)
            break
    proc.terminate()
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        proc.kill()
    shutil.rmtree(profile, ignore_errors=True)

    if not pdf_path.exists():
        sys.exit("Chrome did not produce %s - print worksheet.html from the browser instead"
                 % pdf_path.name)
    pages = re.findall(rb"/Type\s*/Page[^s]", pdf_path.read_bytes())
    print("wrote %s (%d bytes, %d pages)" % (pdf_path.name, pdf_path.stat().st_size, len(pages)))
    expected = n_sheets + 1  # question sheets + the answer key
    if len(pages) != expected:
        print("  warning: expected %d pages, got %d - a sheet is overflowing"
              % (expected, len(pages)))
