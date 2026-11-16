"""Write site/public/research/: the research documents as pages the Research page opens in its reader.

The Research page (site/research.html) links six documents. So that readers stay on the site, each becomes a page
here, opened in the page's reader dialog (site/src/pages/research.js):

  summary.html       research/writeup/summary.html with its two charts drawn (as research/writeup/build_summary.py
                     does for the PDF), plus screen styles; the PDF itself is copied beside it for download
  paper.html, positioning.html, references.html, causes.html, results.html
                     the Markdown files in research/, rendered

Run again after any of those documents changes.
Usage: python scripts/research_docs.py
"""
import html
import importlib.util
import shutil
from pathlib import Path

from markdown_it import MarkdownIt

ROOT = Path(__file__).resolve().parents[1]
RESEARCH = ROOT / "research"
OUT = ROOT / "site" / "public" / "research"
PDF = "EpiLag-PH-research-summary.pdf"
# page name -> (source in research/, title in the reader)
DOCS = {
    "paper": ("writeup/paper.md", "Full write-up"),
    "positioning": ("lit/positioning.md", "Where EpiLag-PH sits in the literature"),
    "references": ("lit/references.md", "References"),
    "causes": ("analysis/causes.md", "Causes: why each result came out as it did"),
    "results": ("results/README.md", "All results"),
}
FONT = '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter+Tight:wght@400;500;600;700;800&display=swap">'
# the site's colours and type (site/src/css/tokens.css)
PAGE_CSS = """
*{box-sizing:border-box}
body{margin:0 auto;max-width:860px;padding:28px 24px 56px;font:400 16px/1.6 "Inter Tight","Helvetica Neue",Arial,system-ui,sans-serif;color:#071711;background:#FBFAF4;overflow-wrap:break-word}
h1{font-size:30px;line-height:1.12;letter-spacing:-.02em;margin:0 0 16px;text-wrap:balance}
h2{font-size:23px;line-height:1.2;margin:40px 0 10px;padding-top:18px;border-top:1px solid #CFD2C4}
h3{font-size:18px;margin:26px 0 8px}h4{font-size:16px;margin:20px 0 6px}
p,ul,ol{margin:0 0 12px}ul,ol{padding-left:22px}li{margin-bottom:5px}
a{color:#055C3E;text-underline-offset:3px}
code{font:500 .86em ui-monospace,"JetBrains Mono",Consolas,monospace;background:#F3F2EA;padding:1px 5px;border-radius:5px;overflow-wrap:anywhere}
.tbl{overflow-x:auto;margin:0 0 16px;border:1px solid #E4E4D9;border-radius:10px;background:#fff}
table{border-collapse:collapse;width:100%;font-size:14px;line-height:1.4;font-variant-numeric:tabular-nums}
th,td{padding:8px 12px;text-align:left;vertical-align:top;border-bottom:1px solid #E4E4D9}
th{background:#F3F2EA;font-weight:700;white-space:nowrap}tr:last-child td{border-bottom:0}
blockquote{margin:0 0 12px;padding:10px 16px;background:#E3F0E7;border-radius:10px;color:#055C3E}
hr{border:0;border-top:1px solid #CFD2C4;margin:28px 0}
@media (max-width:560px){body{padding:20px 16px 40px;font-size:15px}h1{font-size:25px}h2{font-size:20px}}
"""
# the summary is laid out for A4 print; on a screen, a readable column that also fits a phone
SUMMARY_CSS = """
@media screen{
  html{background:#F3F2EA}
  body{max-width:820px;margin:0 auto;padding:28px 32px 48px;font-size:14px;line-height:1.5;font-family:"Inter Tight","Segoe UI",system-ui,sans-serif}
  section.cover{padding-bottom:20px}
  h1{font-size:30px}h2{font-size:21px;margin-top:30px}h3{font-size:16px}
  code{font-size:.88em}.lede{font-size:16px}.kicker,.meta,.src,.note,.tile .l,.box dl,.box dl.terms{font-size:13px}
  table{font-size:13px}.tile .v{font-size:28px}
  svg{max-width:100%;height:auto}
}
@media screen and (max-width:640px){
  body{padding:20px 16px 36px}
  .tiles{grid-template-columns:repeat(2,1fr)}
  .box dl,.box dl.terms{grid-template-columns:minmax(0,1fr)}
  .box dt{margin-top:6px}
  table{display:block;overflow-x:auto}
  h1{font-size:25px}
}
"""


def page(title: str, body: str) -> str:
    return (f'<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
            f'<meta name="viewport" content="width=device-width, initial-scale=1">\n<title>{html.escape(title)} · EpiLag-PH research</title>\n'
            f'{FONT}\n<style>{PAGE_CSS}</style>\n</head>\n<body>\n{body}</body>\n</html>\n')


def summary() -> str:
    spec = importlib.util.spec_from_file_location("build_summary", RESEARCH / "writeup" / "build_summary.py")
    build = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(build)
    text = (RESEARCH / "writeup" / "summary.html").read_text(encoding="utf-8")
    text = text.replace("{{chart_weather}}", build.weather_chart()).replace("{{chart_coverage}}", build.coverage_chart())
    assert "{{" not in text, "summary.html has a slot this script does not fill"
    head = f'<meta name="viewport" content="width=device-width, initial-scale=1">\n{FONT}\n<style>{SUMMARY_CSS}</style>\n</head>'
    return text.replace("</head>", head, 1)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    md = MarkdownIt("commonmark", {"html": False}).enable("table")
    (OUT / "summary.html").write_text(summary(), encoding="utf-8")
    shutil.copyfile(RESEARCH / PDF, OUT / PDF)
    print("summary.html and", PDF)
    for name, (src, title) in DOCS.items():
        body = md.render((RESEARCH / src).read_text(encoding="utf-8"))
        body = body.replace("<table>", '<div class="tbl"><table>').replace("</table>", "</table></div>")
        (OUT / f"{name}.html").write_text(page(title, body), encoding="utf-8")
        print(f"{name}.html  from research/{src}")


if __name__ == "__main__":
    main()
