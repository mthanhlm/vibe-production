#!/usr/bin/env python3
"""Render .vibe/plan.md to .vibe/plan.html — a self-contained, styled page
with an EN/VI language toggle.

The markdown plan is English-only and stays the source of truth. The
translation lives ONLY inside plan.html:
  --vi FILE   read translated markdown from FILE ('-' = stdin)
  (no --vi)   reuse the translation embedded in the existing plan.html,
              so re-renders (ticked checkboxes, status changes) keep it.

Usage: render_plan_html.py [project_dir] [--vi FILE|-]
Stdlib only; no network, no dependencies.
"""
import argparse
import datetime
import html
import os
import re
import sys

FRONTMATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.DOTALL)
VI_START, VI_END = "<!--VIBE:VI:START-->", "<!--VIBE:VI:END-->"


def parse_frontmatter(text):
    meta = {}
    m = FRONTMATTER_RE.match(text)
    if not m:
        return meta, text
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip()
    return meta, text[m.end():]


def inline(md):
    s = html.escape(md, quote=False)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<!\*)\*([^*\n]+)\*(?!\*)", r"<em>\1</em>", s)
    s = re.sub(r"\[([^\]]+)\]\((https?://[^)\s]+)\)", r'<a href="\2">\1</a>', s)
    return s


def md_to_html(md):
    out, para, in_ul, in_ol = [], [], False, False

    def flush_para():
        if para:
            out.append("<p>" + inline(" ".join(para)) + "</p>")
            para.clear()

    def close_lists():
        nonlocal in_ul, in_ol
        if in_ul:
            out.append("</ul>")
            in_ul = False
        if in_ol:
            out.append("</ol>")
            in_ol = False

    for raw in md.splitlines():
        line = raw.rstrip()
        stripped = line.strip()
        h = re.match(r"^(#{1,4})\s+(.*)$", stripped)
        li = re.match(r"^[-*]\s+(.*)$", stripped)
        oli = re.match(r"^\d+[.)]\s+(.*)$", stripped)

        if not stripped:
            flush_para()
            close_lists()
        elif h:
            flush_para(); close_lists()
            lvl = min(len(h.group(1)) + 1, 5)  # page h1 is the plan title
            out.append(f"<h{lvl}>{inline(h.group(2))}</h{lvl}>")
        elif stripped in ("---", "***"):
            flush_para(); close_lists()
            out.append("<hr>")
        elif li:
            flush_para()
            if in_ol:
                out.append("</ol>"); in_ol = False
            if not in_ul:
                out.append("<ul>"); in_ul = True
            item = li.group(1)
            box = re.match(r"^\[( |x|X)\]\s+(.*)$", item)
            if box:
                done = box.group(1).lower() == "x"
                mark = "☑" if done else "☐"
                cls = "done" if done else "pending"
                out.append(f'<li class="check {cls}"><span class="box">{mark}</span> {inline(box.group(2))}</li>')
            else:
                out.append("<li>" + inline(item) + "</li>")
        elif oli:
            flush_para()
            if in_ul:
                out.append("</ul>"); in_ul = False
            if not in_ol:
                out.append("<ol>"); in_ol = True
            out.append("<li>" + inline(oli.group(1)) + "</li>")
        else:
            para.append(stripped)

    flush_para()
    close_lists()
    return "\n".join(out)


def load_vi_html(args, out_path):
    """Translation source, in priority order: --vi file/stdin (markdown),
    else the VI block embedded in the existing plan.html."""
    if args.vi:
        if args.vi == "-":
            md = sys.stdin.read()
        else:
            with open(args.vi, encoding="utf-8") as f:
                md = f.read()
        _, body = parse_frontmatter(md)
        return md_to_html(body)
    if os.path.isfile(out_path):
        with open(out_path, encoding="utf-8") as f:
            prev = f.read()
        s, e = prev.find(VI_START), prev.find(VI_END)
        if s != -1 and e != -1:
            reused = prev[s + len(VI_START):e].strip()
            if reused and 'class="missing"' not in reused:
                return reused
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("project", nargs="?",
                    default=os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd())
    ap.add_argument("--vi", metavar="FILE",
                    help="translated markdown ('-' for stdin); omit to reuse "
                         "the translation already embedded in plan.html")
    args = ap.parse_args()

    project = os.path.realpath(args.project)
    vibe = os.path.join(project, ".vibe")
    plan_path = os.path.join(vibe, "plan.md")
    out_path = os.path.join(vibe, "plan.html")

    if not os.path.isfile(plan_path):
        print(f"no plan at {plan_path}", file=sys.stderr)
        sys.exit(1)

    with open(plan_path, encoding="utf-8") as f:
        meta, body_en = parse_frontmatter(f.read())

    title_m = re.search(r"^#\s+(.+)$", body_en, re.MULTILINE)
    title = title_m.group(1).strip() if title_m else "Plan"

    chips = []
    status = meta.get("status", "draft")
    chips.append(f'<span class="chip {"ok" if status == "approved" else ""}">{html.escape(status)}</span>')
    if meta.get("created"):
        chips.append(f'<span class="chip">created {html.escape(meta["created"])}</span>')
    if meta.get("retry_budget"):
        chips.append(f'<span class="chip">retry budget {html.escape(meta["retry_budget"])}</span>')

    template_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "plan-template.html")
    with open(template_path, encoding="utf-8") as f:
        page = f.read()

    vi_html = load_vi_html(args, out_path) or (
        '<p class="missing">Chưa có bản dịch tiếng Việt — tạo bằng cách chạy '
        '<code>vibe-plan-html --vi -</code> với bản dịch markdown qua stdin '
        '(bản .md gốc luôn là tiếng Anh).</p>'
    )

    page = (page
            .replace("{{TITLE}}", html.escape(title))
            .replace("{{CHIPS}}", " ".join(chips))
            .replace("{{EN_HTML}}", md_to_html(body_en))
            .replace("{{VI_HTML}}", vi_html)
            .replace("{{STAMP}}", datetime.date.today().isoformat()))

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(page)
    print(out_path)


if __name__ == "__main__":
    main()
