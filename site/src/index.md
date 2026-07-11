---
title: Canada 2100
sidebar: false
header: false
footer: false
toc: false
head: '<meta http-equiv="refresh" content="0; url=./fr/">'
---

```js
// Respect a previously chosen language; default to French.
const pref = localStorage.getItem("lang");
location.replace(pref === "en" ? "./en/" : "./fr/");
```

<div style="min-height:60vh;display:grid;place-items:center;text-align:center;font-family:system-ui,sans-serif">
  <div>
    <p style="font-size:1.1rem;color:#9aa2ad">Redirection… / Redirecting…</p>
    <p><a href="./fr/" style="color:#8ab4f8">Version française</a> · <a href="./en/" style="color:#8ab4f8">English version</a></p>
  </div>
</div>
