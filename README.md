# Portfolio - Ruslan Shayakhmetov

Static bilingual portfolio site (EN / RU), built for GitHub Pages. No framework, no build
step at serve time, no tracking. Every page is plain HTML generated from one content file.

```
index.html                  English home page
ru/index.html               Russian home page
projects/99node.html        project page, EN
projects/qurbaqa.html       project page, EN
ru/projects/*.html          the same pages in Russian
assets/css/tokens.css       generated from the design system's tokens.json
assets/css/components.css   copied from the design system's bundle.css
assets/css/site.css         page layout only
assets/js/site.js           theme switch (dark by default)
sitemap.xml                 generated when SITE_URL is set
cv/                         the CV PDF the hero links to
src/content.json            ALL copy, both languages - edit this
src/build.py                the generator
src/design-system/          tokens.json + bundle.css, copied from the design system
```

## Deploying

Pushing to `main` runs `.github/workflows/deploy.yml`, which regenerates the pages,
fails if the committed HTML is stale, and publishes everything except `src/` and the
repo's own files to the `gh-pages` branch. GitHub Pages serves that branch at
<https://shayaqhmetov.github.io>. Nothing in Settings needs to change.

The workflow needs one secret: `GH_PAT`, a token with `contents: write` on this
repository.

`.nojekyll` is present, so GitHub serves the files as they are instead of running Jekyll.

The site URL lives in one place, the `SITE_URL` env of that workflow. It is what canonical
tags, `hreflang` links and `sitemap.xml` are built from - change it there and in the local
build command below if the site ever moves.

## Editing

All copy lives in `src/content.json`, English under `en`, Russian under `ru`. Change it,
then regenerate:

```sh
SITE_URL=https://shayaqhmetov.github.io python3 src/build.py
```

Nothing else is needed - no dependencies, Python 3 only. Commit the regenerated HTML.

`SITE_URL` is what produces `sitemap.xml` and the `<link rel="canonical">` and `hreflang`
tags. Build without it and those disappear, and CI will reject the result as stale - so
keep it on the command.

## Design system

Colours, type, spacing, radii and component classes come from a separate design system.
`src/design-system/tokens.json` and `src/design-system/bundle.css` are copies of it;
`build.py` compiles `tokens.json` into the CSS custom properties in `assets/css/tokens.css`.

When the design system changes, replace those two files and rebuild. Do not edit
`assets/css/tokens.css` or `assets/css/components.css` by hand - they are generated or
copied and will be overwritten.

Page-specific layout belongs in `assets/css/site.css`; anything reusable belongs in the
design system instead.

## Accessibility notes

Every text colour clears 4.5:1 against the surfaces it is used on, in both themes;
control borders and the focus ring clear 3:1. Focus outlines are never removed. The theme
choice is stored in `localStorage` when the browser allows it and the site works without it.
