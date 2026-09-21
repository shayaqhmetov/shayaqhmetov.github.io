#!/usr/bin/env python3
"""Build the static portfolio site.

Sources:  src/content.json          - all copy, English and Russian
          src/design-system/        - tokens.json + bundle.css from the design system
Output:   repository root           - index.html, ru/, projects/, ru/projects/, assets/

Run:      python3 src/build.py
"""

import json
import os
import shutil
from html import escape

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DS = os.path.join(HERE, "design-system")

LANGS = ("en", "ru")


# --------------------------------------------------------------------------
# tokens.json -> tokens.css
# --------------------------------------------------------------------------

def value_for(token, theme, first_theme):
    v = token.get("value")
    if isinstance(v, str):
        return v if theme == first_theme else None
    return v.get(theme)


def build_tokens_css(tokens):
    color = tokens["color"]
    themes = [t["id"] for t in color["themes"]]
    first = themes[0]
    out = ["/* Generated from src/design-system/tokens.json - do not edit by hand. */", ""]

    def color_block(selector, theme, only_overrides):
        lines = []
        for t in color["tokens"]:
            val = value_for(t, theme, first)
            if val is None:
                if only_overrides:
                    continue
                val = value_for(t, first, first)
            if val is None:
                continue
            if val.startswith("{") and val.endswith("}"):
                val = "var(--%s)" % val[1:-1]
            lines.append("  --%s: %s;" % (t["name"], val))
        for t in tokens.get("shadow", {}).get("tokens", []):
            val = value_for(t, theme, first)
            if val is None:
                if only_overrides:
                    continue
                val = value_for(t, first, first)
            if val is None:
                continue
            lines.append("  --%s: %s;" % (t["name"], val))
        if not lines:
            return []
        return ["%s {" % selector] + lines + ["}", ""]

    out += color_block(':root, [data-theme="%s"]' % first, first, False)
    for theme in themes[1:]:
        out += color_block('[data-theme="%s"]' % theme, theme, False)

    scalar = []
    for family in ("spacing", "radius", "border", "layout"):
        for t in tokens.get(family, {}).get("tokens", []):
            scalar.append("  --%s: %s;" % (t["name"], t["value"]))
    for key, stack in tokens["type"]["families"].items():
        scalar.append("  --font-%s: %s;" % (key, stack))
    out += [":root {"] + scalar + ["}", ""]

    for group in tokens["type"]["groups"]:
        default_family = group.get("family")
        for style in group["styles"]:
            fam = style.get("family", default_family)
            decls = ["  font-family: var(--font-%s);" % fam]
            decls.append("  font-size: %s;" % style["fontSize"])
            if "lineHeight" in style:
                decls.append("  line-height: %s;" % style["lineHeight"])
            if "fontWeight" in style:
                decls.append("  font-weight: %s;" % style["fontWeight"])
            if "letterSpacing" in style:
                decls.append("  letter-spacing: %s;" % style["letterSpacing"])
            out += [".%s {" % style["name"]] + decls + ["}", ""]

    return "\n".join(out).rstrip() + "\n"


# --------------------------------------------------------------------------
# small html helpers
# --------------------------------------------------------------------------

def e(text):
    return escape(str(text), quote=True)


def tags(items):
    if not items:
        return ""
    return ('<div class="rs-tag-row">'
            + "".join('<span class="rs-tag">%s</span>' % e(i) for i in items)
            + "</div>")


def stat(s):
    cls = "rs-stat rs-stat--measured" if s.get("measured") else "rs-stat"
    note = '<div class="rs-stat__note">%s</div>' % e(s["note"]) if s.get("note") else ""
    return ('<div class="%s"><div class="rs-stat__value">%s</div>'
            '<div class="rs-stat__label">%s</div>%s</div>'
            % (cls, e(s["value"]), e(s["label"]), note))


def stat_grid(items):
    return '<div class="rs-stat-grid">%s</div>' % "".join(stat(s) for s in items)


def section_head(eyebrow, title, lede=""):
    parts = ['<header class="rs-section-head">']
    if eyebrow:
        parts.append('<div class="rs-section-head__eyebrow">%s</div>' % e(eyebrow))
    parts.append('<h2 class="rs-section-head__title">%s</h2>' % e(title))
    parts.append('<div class="rs-section-head__rule" aria-hidden="true"></div>')
    if lede:
        parts.append('<p class="rs-section-head__lede">%s</p>' % e(lede))
    parts.append("</header>")
    return "".join(parts)


def note(n):
    return ('<aside class="rs-note"><div class="rs-note__label">%s</div>'
            '<p class="rs-note__body">%s</p></aside>' % (e(n["label"]), e(n["body"])))


# --------------------------------------------------------------------------
# chrome
# --------------------------------------------------------------------------

THEME_BOOT = (
    "(function(){try{var t=localStorage.getItem('rs-theme');"
    "if(t==='light'||t==='dark'){document.documentElement.setAttribute('data-theme',t);}"
    "}catch(err){}})();"
)


def head(c, other, prefix, title, description, canonical_path, alt_path):
    person = C["person"]
    jsonld = {
        "@context": "https://schema.org",
        "@type": "Person",
        "name": c.get("displayName", person["name"]),
        "alternateName": person["name"],
        "jobTitle": "Senior Backend Engineer",
        "email": "mailto:" + person["email"],
        "url": SITE_URL + "/" if SITE_URL else "",
        "sameAs": [person["github"], person["linkedin"]],
        "address": {"@type": "PostalAddress", "addressLocality": "Bangkok", "addressCountry": "TH"},
        "knowsAbout": ["Node.js", "TypeScript", "AWS", "PostgreSQL", "NestJS", "Distributed systems"],
    }
    alternates = ""
    if SITE_URL:
        alternates = (
            '<link rel="canonical" href="%s/%s">' % (SITE_URL, canonical_path)
            + '<link rel="alternate" hreflang="%s" href="%s/%s">' % (c["lang"], SITE_URL, canonical_path)
            + '<link rel="alternate" hreflang="%s" href="%s/%s">' % (other["lang"], SITE_URL, alt_path)
            + '<link rel="alternate" hreflang="x-default" href="%s/%s">' % (SITE_URL, canonical_path if c["lang"] == "en" else alt_path)
        )
    return (
        '<!DOCTYPE html>\n<html lang="%s" data-theme="dark">\n<head>\n'
        '<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        '<title>%s</title>\n'
        '<meta name="description" content="%s">\n'
        '<meta name="color-scheme" content="dark light">\n'
        '<meta property="og:type" content="profile">\n'
        '<meta property="og:title" content="%s">\n'
        '<meta property="og:description" content="%s">\n'
        '<meta name="twitter:card" content="summary">\n'
        '%s'
        '<link rel="icon" href="%sassets/favicon.svg" type="image/svg+xml">\n'
        '<link rel="preconnect" href="https://fonts.googleapis.com">\n'
        '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
        '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?'
        'family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;500;600&display=swap">\n'
        '<link rel="stylesheet" href="%sassets/css/tokens.css">\n'
        '<link rel="stylesheet" href="%sassets/css/components.css">\n'
        '<link rel="stylesheet" href="%sassets/css/site.css">\n'
        '<script>%s</script>\n'
        '<script type="application/ld+json">%s</script>\n'
        '</head>\n'
        % (c["lang"], e(title), e(description), e(title), e(description),
           alternates, prefix, prefix, prefix, prefix, THEME_BOOT, json.dumps(jsonld, ensure_ascii=False))
    )


def header(c, other, prefix, home_href, alt_href, is_home):
    nav = ""
    if is_home:
        nav = ('<nav class="site-nav" aria-label="%s">'
               '<a href="#work">%s</a><a href="#experience">%s</a>'
               '<a href="#skills">%s</a><a href="#contact">%s</a></nav>'
               % (e(c["nav"]["work"]), e(c["nav"]["work"]), e(c["nav"]["experience"]),
                  e(c["nav"]["skills"]), e(c["nav"]["contact"])))
    segs = []
    for code in ("en", "ru"):
        if code == c["lang"]:
            segs.append('<span class="rs-seg__btn" aria-current="page">%s</span>' % code.upper())
        else:
            segs.append('<a class="rs-seg__btn" href="%s" hreflang="%s">%s</a>'
                        % (e(alt_href), code, code.upper()))
    lang_switch = ('<div class="rs-seg" role="group" aria-label="%s">%s</div>'
                   % (e(c["ui"]["language"]), "".join(segs)))
    theme_switch = (
        '<div class="rs-seg" role="group" aria-label="%s" id="theme-switch">'
        '<button class="rs-seg__btn" type="button" data-theme-set="dark" aria-pressed="true">%s</button>'
        '<button class="rs-seg__btn" type="button" data-theme-set="light" aria-pressed="false">%s</button>'
        '</div>' % (e(c["ui"]["theme"]), e(c["ui"]["dark"]), e(c["ui"]["light"]))
    )
    return (
        '<body>\n<a class="skip-link" href="#main">%s</a>\n'
        '<header class="site-header"><div class="page-shell site-header__inner">'
        '<a class="wordmark" href="%s" aria-label="%s">RS</a>%s'
        '<div class="site-tools">%s%s</div>'
        '</div></header>\n<main id="main">\n'
        % (e(c["ui"]["skipToContent"]), e(home_href), e(c.get("displayName", C["person"]["name"])),
           nav, lang_switch, theme_switch)
    )


def footer(c, prefix):
    p = C["person"]
    return (
        '</main>\n<footer class="site-footer"><div class="page-shell site-footer__inner">'
        '<p class="site-footer__note">%s</p>'
        '<p class="site-footer__links">'
        '<a href="mailto:%s">%s</a><a href="%s" rel="me noreferrer">%s</a>'
        '<a href="%s" rel="me noreferrer">%s</a></p>'
        '</div></footer>\n<script src="%sassets/js/site.js" defer></script>\n</body>\n</html>\n'
        % (e(c["footer"]), e(p["email"]), e(p["email"]), e(p["github"]), e(p["githubLabel"]),
           e(p["linkedin"]), e(p["linkedinLabel"]), prefix)
    )


# --------------------------------------------------------------------------
# pages
# --------------------------------------------------------------------------

def home(c, other):
    prefix = "../" if c["lang"] != "en" else ""
    home_href = "./" if c["lang"] == "en" else "./"
    alt_href = "ru/" if c["lang"] == "en" else "../"
    p = C["person"]
    out = [head(c, other, prefix, c["meta"]["homeTitle"], c["meta"]["homeDescription"],
                "" if c["lang"] == "en" else "ru/", "ru/" if c["lang"] == "en" else "")]
    out.append(header(c, other, prefix, home_href, alt_href, True))

    # hero
    out.append('<section class="hero"><div class="page-shell">')
    out.append('<p class="hero__role mono-label">%s</p>' % e(c["hero"]["role"]))
    out.append('<h1 class="hero__name">%s</h1>' % e(c.get("displayName", p["name"])))
    out.append('<p class="hero__location">%s</p>' % e(c["hero"]["location"]))
    out.append('<p class="hero__lede">%s</p>' % e(c["hero"]["lede"]))
    out.append('<div class="hero__actions">'
               '<a class="rs-btn rs-btn--primary" href="%s%s" download>%s</a>'
               '<a class="rs-btn rs-btn--secondary" href="%s" rel="noreferrer">GitHub</a>'
               '<a class="rs-btn rs-btn--secondary" href="%s" rel="noreferrer">LinkedIn</a>'
               '<a class="rs-btn rs-btn--ghost" href="mailto:%s">%s</a>'
               '</div>'
               % (prefix, e(p["cv"]), e(c["ui"]["downloadCv"]), e(p["github"]),
                  e(p["linkedin"]), e(p["email"]), e(p["email"])))
    out.append('<div class="hero__stats">%s</div>' % stat_grid(c["stats"]))
    out.append("</div></section>")

    # work
    out.append('<section class="section" id="work"><div class="page-shell">')
    out.append(section_head(c["work"]["eyebrow"], c["work"]["title"], c["work"]["lede"]))
    out.append('<div class="card-grid">')
    for key in ("99node", "qurbaqa"):
        card = c["cards"][key]
        proj = C["projects"][key]
        href = "%sprojects/%s.html" % ("" if c["lang"] == "en" else "", proj["slug"])
        figures = "".join(
            '<div class="rs-card__figure"><span class="rs-card__figure-value">%s</span>'
            '<span class="rs-card__figure-label">%s</span></div>' % (e(f["value"]), e(f["label"]))
            for f in card["figures"])
        out.append(
            '<a class="rs-card" href="%s">'
            '<div class="rs-card__head"><h3 class="rs-card__title">%s</h3>'
            '<span class="rs-card__role">%s</span></div>'
            '<p class="rs-card__lede">%s</p>%s'
            '<div class="rs-card__figures">%s</div></a>'
            % (e(href), e(card["title"]), e(card["role"]), e(card["lede"]),
               tags(proj["stack"][:6]), figures))
    out.append("</div></div></section>")

    # experience
    out.append('<section class="section" id="experience"><div class="page-shell">')
    out.append(section_head(c["experienceSection"]["eyebrow"], c["experienceSection"]["title"]))
    for job in c["experience"]:
        points = "".join("<li>%s</li>" % e(pt) for pt in job["points"])
        context = '<p class="rs-entry__context">%s</p>' % e(job["context"]) if job["context"] else ""
        org = '<div class="rs-entry__org">%s</div>' % e(job["org"]) if job.get("org") else ""
        out.append(
            '<article class="rs-entry"><div class="rs-entry__period">%s</div><div>'
            '<h3 class="rs-entry__title">%s</h3>%s%s'
            '<ul class="rs-entry__points">%s</ul>%s</div></article>'
            % (e(job["period"]), e(job["title"]), org, context, points, tags(job["stack"])))
    out.append("</div></section>")

    # skills
    out.append('<section class="section" id="skills"><div class="page-shell">')
    out.append(section_head(c["skillsSection"]["eyebrow"], c["skillsSection"]["title"]))
    out.append('<dl class="skills">')
    for group in c["skills"]:
        out.append('<div class="skills__row"><dt class="heading-s">%s</dt><dd>%s</dd></div>'
                   % (e(group["name"]), tags(group["items"])))
    out.append("</dl>")
    out.append('<div class="education"><p class="mono-label">%s</p>'
               '<p class="education__title heading-m">%s</p><p class="education__line">%s</p></div>'
               % (e(c["education"]["eyebrow"]), e(c["education"]["title"]), e(c["education"]["line"])))
    out.append("</div></section>")

    # contact
    out.append('<section class="section" id="contact"><div class="page-shell">')
    out.append(section_head(c["contact"]["eyebrow"], c["contact"]["title"], c["contact"]["lede"]))
    out.append('<p class="contact__availability">%s</p>' % e(c["contact"]["availability"]))
    out.append('<div class="hero__actions">'
               '<a class="rs-btn rs-btn--primary" href="mailto:%s">%s</a>'
               '<a class="rs-btn rs-btn--secondary" href="%s%s" download>%s</a>'
               '<a class="rs-btn rs-btn--ghost" href="%s" rel="noreferrer">%s</a></div>'
               % (e(p["email"]), e(p["email"]), prefix, e(p["cv"]), e(c["ui"]["downloadCv"]),
                  e(p["linkedin"]), e(p["linkedinLabel"])))
    out.append("</div></section>")

    out.append(footer(c, prefix))
    return "".join(out)


def project(c, other, key):
    prefix = "../" if c["lang"] == "en" else "../../"
    home_href = "../" if c["lang"] == "en" else "../"
    alt_href = ("../ru/projects/%s.html" % key) if c["lang"] == "en" else ("../../projects/%s.html" % key)
    page = c["pages"][key]
    proj = C["projects"][key]
    canonical = "projects/%s.html" % key if c["lang"] == "en" else "ru/projects/%s.html" % key
    alt = "ru/projects/%s.html" % key if c["lang"] == "en" else "projects/%s.html" % key
    title = "%s - %s" % (page["title"], c.get("displayName", C["person"]["name"]))
    out = [head(c, other, prefix, title, page["lede"][:180], canonical, alt)]
    out.append(header(c, other, prefix, home_href, alt_href, False))

    out.append('<section class="project-hero"><div class="page-shell">')
    out.append('<a class="back-link" href="%s">&#8592; %s</a>' % (e(home_href), e(c["nav"]["back"])))
    out.append('<p class="mono-label project-hero__eyebrow">%s</p>' % e(c["ui"]["petProject"]))
    out.append('<h1 class="project-hero__title">%s</h1>' % e(page["title"]))
    out.append('<p class="project-hero__role">%s</p>' % e(page["role"]))
    out.append('<p class="project-hero__lede">%s</p>' % e(page["lede"]))
    out.append('<p class="project-hero__diff">%s</p>' % e(page["differentiator"]))
    out.append('<div class="hero__actions">'
               '<a class="rs-btn rs-btn--primary" href="%s" rel="noreferrer">%s '
               '<span class="rs-btn__arrow" aria-hidden="true">&#8594;</span></a></div>'
               % (e(proj["url"]), e(c["ui"]["liveSite"])))
    out.append('<div class="hero__stats">%s</div>' % stat_grid(page["stats"]))
    out.append("</div></section>")

    out.append('<section class="section"><div class="page-shell">')
    out.append(section_head("", c["ui"]["decisions"]))
    out.append('<div class="decisions">')
    for d in page["decisions"]:
        out.append('<article class="decision"><h3 class="decision__h">%s</h3>'
                   '<p class="decision__p">%s</p></article>' % (e(d["h"]), e(d["p"])))
    out.append("</div></div></section>")

    out.append('<section class="section"><div class="page-shell columns">')
    out.append('<div><h2 class="heading-m">%s</h2><ul class="plain-list">%s</ul></div>'
               % (e(c["ui"]["whatToLook"]),
                  "".join("<li>%s</li>" % e(x) for x in page["look"])))
    if page.get("scaleList"):
        out.append('<div><h2 class="heading-m">%s</h2><ul class="plain-list">%s</ul></div>'
                   % (e(c["ui"]["scale"]),
                      "".join("<li>%s</li>" % e(x) for x in page["scaleList"])))
    out.append('<div><h2 class="heading-m">%s</h2>%s</div>' % (e(c["ui"]["stack"]), tags(proj["stack"])))
    out.append("</div></section>")

    out.append('<section class="section"><div class="page-shell">%s</div></section>' % note(page["note"]))

    out.append(footer(c, prefix))
    return "".join(out)


# --------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------

def write(path, text):
    full = os.path.join(ROOT, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        f.write(text)
    print("  %s" % path)


C = json.load(open(os.path.join(HERE, "content.json"), encoding="utf-8"))
SITE_URL = os.environ.get("SITE_URL", "").rstrip("/")


def main():
    tokens = json.load(open(os.path.join(DS, "tokens.json"), encoding="utf-8"))
    print("building:")
    write("assets/css/tokens.css", build_tokens_css(tokens))
    shutil.copyfile(os.path.join(DS, "bundle.css"), os.path.join(ROOT, "assets/css/components.css"))
    print("  assets/css/components.css")

    en, ru = C["en"], C["ru"]
    write("index.html", home(en, ru))
    write("ru/index.html", home(ru, en))
    for key in ("99node", "qurbaqa"):
        write("projects/%s.html" % key, project(en, ru, key))
        write("ru/projects/%s.html" % key, project(ru, en, key))

    if SITE_URL:
        urls = ["", "ru/", "projects/99node.html", "projects/qurbaqa.html",
                "ru/projects/99node.html", "ru/projects/qurbaqa.html"]
        sm = ['<?xml version="1.0" encoding="UTF-8"?>',
              '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
        for u in urls:
            sm.append("<url><loc>%s/%s</loc></url>" % (SITE_URL, u))
        sm.append("</urlset>")
        write("sitemap.xml", "\n".join(sm) + "\n")
    print("done.")


if __name__ == "__main__":
    main()
