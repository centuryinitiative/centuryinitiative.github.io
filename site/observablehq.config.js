export default {
  title: "Canada 2100",
  root: "src",
  theme: ["near-midnight"],
  toc: false,
  // Bilingual navigation: French section first (default), English second.
  pages: [
    {
      name: "Français",
      pages: [
        { name: "L'histoire", path: "/fr/" },
        { name: "Explorateur", path: "/fr/explorer" },
        { name: "Canada autochtone", path: "/fr/indigenous" },
        { name: "Méthodologie", path: "/fr/methodology" }
      ]
    },
    {
      name: "English",
      pages: [
        { name: "The story", path: "/en/" },
        { name: "Explorer", path: "/en/explorer" },
        { name: "Indigenous Canada", path: "/en/indigenous" },
        { name: "Methodology", path: "/en/methodology" }
      ]
    }
  ],
  // Language-aware header with an FR | EN switcher that maps each page to its
  // counterpart in the other language and remembers the choice.
  header: `<div class="site-header">
    <a class="brand" id="site-brand" href="/fr/">Canada&nbsp;2100 <span class="brand-sub"></span></a>
    <span class="langswitch" id="langswitch"></span>
  </div>
  <script>{
    const p = location.pathname;
    const isEn = /^\\/en(\\/|$)/.test(p);
    const rest = p.replace(/^\\/(fr|en)/, "") || "/";
    const toFr = "/fr" + rest, toEn = "/en" + rest;
    const brand = document.getElementById("site-brand");
    if (brand) {
      brand.href = isEn ? "/en/" : "/fr/";
      const sub = brand.querySelector(".brand-sub");
      if (sub) sub.textContent = isEn ? "\\u00b7 a demographic projection" : "\\u00b7 une projection d\\u00e9mographique";
    }
    const el = document.getElementById("langswitch");
    if (el) el.innerHTML =
      '<a href="' + toFr + '" class="' + (isEn ? "" : "on") + '" onclick="localStorage.setItem(\\'lang\\',\\'fr\\')">FR</a>'
      + '<span class="sep">|</span>'
      + '<a href="' + toEn + '" class="' + (isEn ? "on" : "") + '" onclick="localStorage.setItem(\\'lang\\',\\'en\\')">EN</a>';
  }</script>
  <style>
    .site-header { display:flex; align-items:center; justify-content:space-between; gap:1rem; width:100%; }
    .site-header .brand { font-weight:600; color:#e8eaed; text-decoration:none; }
    .site-header .brand-sub { color:#6b7280; font-weight:400; }
    .langswitch { display:inline-flex; align-items:center; gap:.4rem; font-size:.8rem; font-weight:600; }
    .langswitch a { color:#8b93a1; text-decoration:none; padding:.05rem .35rem; border-radius:3px; }
    .langswitch a.on { color:#e8eaed; background:rgba(138,180,248,.18); }
    .langswitch a:hover { color:#8ab4f8; }
    .langswitch .sep { color:#3a3f48; }
  </style>`,
  head: '<meta name="viewport" content="width=device-width, initial-scale=1">',
  footer: "Agent-based demographic simulation · 1971–2100 · data self-contained"
};
