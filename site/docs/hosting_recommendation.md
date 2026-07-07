# Recomendación de hosting para el sitio Astro

**Tarea:** T-101 — Investigar y recomendar plataforma de hosting.
**Rol:** thinker (solo recomienda; la decisión final es de Mario).
**Fecha:** 2026-07-05.
**Alcance:** sin compras, sin despliegues, sin editar código fuente.

---

## TL;DR — Recomendación

**Cloudflare Pages.**

Tres razones decisivas:

1. **Ancho de banda ilimitado gratis.** Es el único de los cuatro que no impone tope de 100 GB/mes. Para un portafolio ligado a búsqueda de empleo, un pico de tráfico (una publicación que se vuelve visible, un reclutador compartiéndolo) nunca degrada ni bloquea el sitio ni empuja a un plan de pago.
2. **Soporte nativo de monorepo por configuración (no por workflow a mano).** El sitio no vive en la raíz del repo, sino en `Portfolio-repo/site`. Cloudflare Pages resuelve esto con un único campo en el panel — *Root directory (advanced) → Path* = `Portfolio-repo/site` — sin escribir ni mantener un GitHub Action propio. Build System V2 (por defecto en proyectos nuevos) trae este soporte.
3. **Cero lock-in real y despliegue trivial.** El sitio compila a un `dist/` estático puro (12 páginas, ya verificado con `npm run build`). Ese `dist/` es 100% portable: si mañana Cloudflare deja de convenir, se mueve a cualquier otro host en minutos. No se usa ningún adaptador SSR ni función serverless propietaria, así que no hay dependencia técnica de la plataforma.

Custom domain en la raíz + HTTPS automático y gratuito (certificado gestionado por Cloudflare) vienen incluidos, y el fetch del RSS de Substack en build funciona porque el build corre en servidores de Cloudflare con salida de red. Ver detalles y salvedad de base-path más abajo.

---

## Contexto del sitio (hechos de partida)

- **Stack:** Astro 6 (`^6.2.2`) + MDX + React 19 + KaTeX + Shiki. **100% estático** — `astro.config.mjs` no declara `output` ni adaptador, así que la salida es SSG puro.
- **El sitio NO está en la raíz del repo.** Está en `Portfolio-repo/site`, dentro del monorepo `github.com/MarioCasanovacf/Portfolio`. La subcarpeta desde la raíz del repo es exactamente `Portfolio-repo/site`. Este es el hecho que más discrimina entre hosts.
- **Build ya limpio:** `npm run build` produce `dist/` con 12 páginas. Comando de build = `npm run build`; directorio de salida = `dist`.
- **Node:** `package.json` pide `engines.node >= 22.12.0`. Cualquier host debe fijarse en una imagen de build Node ≥ 22 (variable `NODE_VERSION` o equivalente).
- **RSS en build:** el sitio hace fetch del RSS de Substack en tiempo de build. Requiere que el entorno de build tenga salida de red hacia Substack — la tienen los cuatro candidatos. Como todo se resuelve en build, el resultado es HTML estático: **no hay diferencia de compatibilidad entre hosts** en este punto.
- **Dominio:** se contempla dominio propio (el registrador se investiga en T-102). Con dominio propio en la raíz, **ningún** host necesita `base` (ver salvedad).

---

## Comparativa

| Criterio | Cloudflare Pages | Vercel (Hobby) | Netlify (Free) | GitHub Pages |
|---|---|---|---|---|
| **Dominio propio + HTTPS** | Sí, HTTPS auto gratis | Sí, HTTPS auto gratis | Sí, HTTPS auto gratis | Sí, HTTPS auto gratis (Let's Encrypt) |
| **Build desde subcarpeta (monorepo)** | Campo *Root directory (advanced)* | Ajuste *Root Directory* | *Base directory* | **Requiere Action a mano** con `working-directory` + `path` |
| **Implicación de base-path** | Ninguna con dominio en raíz | Ninguna con dominio en raíz | Ninguna con dominio en raíz | Ninguna con dominio en raíz; **pero** `user.github.io/Portfolio/` exigiría `base: '/Portfolio/'` |
| **Ancho de banda gratis** | **Ilimitado** | 100 GB/mes | 100 GB/mes | ~100 GB/mes (límite blando) |
| **Builds gratis** | 500 builds/mes | Sí (Hobby) | Pool de 300 créditos/mes | Actions: gratis ilimitado en repos públicos |
| **RSS en build** | Compatible | Compatible | Compatible | Compatible |
| **Lock-in (sitio estático)** | Mínimo (`dist/` portable) | Mínimo, pero cultura SSR/serverless | Mínimo | Mínimo |
| **Salvedad de licencia** | — | **Hobby restringe uso comercial** por ToS (zona gris para portafolio de empleo) | — | — |

### Por qué NO cada alternativa

- **GitHub Pages.** Funciona y es gratis (Actions ilimitado en repo público), pero es la opción con más fricción para este caso: al no estar el sitio en la raíz del repo hay que **escribir y mantener a mano** un workflow de GitHub Actions (`actions/upload-pages-artifact` con `path: Portfolio-repo/site/dist`, y build con `working-directory`). Además, si en algún momento se usara la URL de proyecto `MarioCasanovacf.github.io/Portfolio/` en vez de dominio propio, obligaría a fijar `base: '/Portfolio/'` en `astro.config.mjs`, lo que complica el desarrollo local y los enlaces. Con dominio propio en la raíz eso desaparece, pero el coste de mantener el workflow permanece.
- **Vercel.** DX excelente y ajuste *Root Directory* trivial, pero (a) el plan Hobby gratuito tiene una **restricción de uso comercial** en sus términos — un portafolio explícitamente orientado a conseguir empleo cae en zona gris; (b) tope de 100 GB; (c) su valor diferencial es SSR/serverless, que este sitio estático no usa. Pagar potencia que no se necesita, con menos margen gratuito que Cloudflare.
- **Netlify.** Sólida y con *Base directory* para monorepo, pero el tope de 100 GB y el pool de 300 créditos/mes de build son menos holgados que el ancho de banda ilimitado de Cloudflare. No hay razón de peso que la ponga por delante para un sitio estático puro.

---

## Salvedad importante: dominio propio en raíz vs. subpágina

La recomendación asume **dominio propio servido en la raíz** (p. ej. `mariocasanova.com/`). En ese escenario, con cualquiera de los cuatro hosts:

- **No hace falta `base`** en `astro.config.mjs`.
- Sí conviene fijar `site: 'https://<dominio>'` en `astro.config.mjs` para que sitemap, URLs canónicas y el RSS generen enlaces absolutos correctos. Esto es independiente del host (nota: hoy el config **no** define `site`). *(Solo observación; el thinker no edita fuente.)*

Único caso donde base-path importa: si se renunciara al dominio propio y se usara la **URL de proyecto de GitHub Pages** `MarioCasanovacf.github.io/Portfolio/` (una subruta, no la raíz). Ahí **sí** habría que poner `base: '/Portfolio/'`. Las URLs por defecto de Cloudflare (`*.pages.dev`), Vercel (`*.vercel.app`) y Netlify (`*.netlify.app`) sirven en la raíz de un subdominio, así que **no** necesitan base aunque no haya dominio propio todavía. Esto refuerza a Cloudflare: incluso antes de comprar el dominio, `*.pages.dev` funciona sin tocar el config.

---

## Knobs de configuración concretos por host

### Cloudflare Pages (recomendado)
- Conectar el repo `github.com/MarioCasanovacf/Portfolio` en *Workers & Pages → Create → Pages → Import Git repository*.
- **Root directory (advanced) → Path:** `Portfolio-repo/site`
- **Build command:** `npm run build`
- **Build output directory:** `dist`
- **Production branch:** `main`
- **Node:** variable de entorno `NODE_VERSION` = `22.12.0` (o superior).
- **Custom domain:** *Custom domains → Set up domain*; apuntar DNS al proyecto (Cloudflare emite el certificado HTTPS automáticamente).
- **Base path:** no fijar (dominio en raíz).
- No requiere fichero de workflow ni CNAME en el repo.

### GitHub Pages (alternativa más manual)
- **Fichero `public/CNAME`** con una sola línea: el dominio propio.
- **`astro.config.mjs`:** `site: 'https://<dominio>'`; **sin** `base` si es dominio en raíz — **con** `base: '/Portfolio/'` solo si se usa la URL de proyecto.
- **Workflow `.github/workflows/deploy.yml`** propio: `actions/checkout` → setup Node ≥ 22 → `npm ci` + `npm run build` con `working-directory: Portfolio-repo/site` → `actions/upload-pages-artifact` con `path: Portfolio-repo/site/dist` → `actions/deploy-pages`.
- **Settings → Pages:** source = GitHub Actions; configurar el custom domain (HTTPS gestionado por GitHub).

### Vercel (alternativa)
- Importar el repo; **Root Directory** = `Portfolio-repo/site`.
- Framework preset = Astro (build `npm run build`, output `dist` autodetectados).
- **Node:** ajustar versión de Node ≥ 22 en *Settings → Build & Development*.
- **Domains:** añadir dominio propio; HTTPS automático.
- Revisar la restricción de uso comercial del plan Hobby antes de elegirlo.

### Netlify (alternativa)
- Importar el repo; **Base directory** = `Portfolio-repo/site`.
- **Build command:** `npm run build`; **Publish directory:** `Portfolio-repo/site/dist` (o `dist` relativo a la base).
- **Node:** `NODE_VERSION` = `22.12.0` (env var o `.nvmrc`).
- **Domain management:** añadir dominio propio; HTTPS automático (Let's Encrypt).

---

## Cierre

Para un Astro estático puro en subcarpeta de monorepo con dominio propio, **Cloudflare Pages** ofrece el mejor equilibrio: monorepo por configuración (sin mantener un workflow), ancho de banda ilimitado gratis, HTTPS y dominio propio incluidos, y cero lock-in gracias al `dist/` portable. GitHub Pages queda como plan B legítimo si se prefiere no depender de un tercero fuera de GitHub, a cambio de mantener un workflow propio. La decisión final es de Mario.
