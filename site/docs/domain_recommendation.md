# Recomendación de dominio — marca personal de Mario Casanova (profesional de datos)

**Tarea:** T-102 (harness) · **Rol:** thinker-domain · **Fecha:** 2026-07-05
**Estado:** recomendación para que Mario decida y ejecute. **NO se compró ningún dominio** — la compra es una compuerta humana que solo ejecuta Mario.

---

## TL;DR

- **Nombre recomendado:** `mariocasanova.com` — el `.com` exacto con tu nombre está **libre** (verificado en vivo). Es el activo de marca personal más valioso y el que menos fricción genera con reclutadores.
- **Registrador recomendado:** **Cloudflare Registrar** — precio "a costo" (registro = renovación, sin precio-gancho de primer año), WHOIS privacy y DNSSEC gratis, y encaja bien si el sitio termina en Cloudflare (ver T-101 de hosting).
- **Alternativa de registrador** si no quieres depender del DNS de Cloudflare: **Porkbun** (`.com` a $9.73 primer año / $11.08 renovación, también transparente).
- **Opcional (barato) para reforzar marca:** registrar además `mariocasanova.dev` (~$12/año) como redirección hacia el `.com`. Buena señal para un perfil técnico/datos.

---

## 1. Candidatos + disponibilidad (verificación EN VIVO, 2026-07-05)

Método: consultas RDAP autoritativas (Verisign para `.com`, registro de Google para `.dev`/`.app`) con dominios de control conocidos, y `whois` directo a `whois.nic.io` y `whois.mx` para las ccTLD (RDAP no es confiable en esos dos registros — devuelve 404 incluso para dominios registrados). Cada resultado se contrastó contra un dominio de control ya registrado para descartar falsos positivos.

| # | Candidato | Disponibilidad | Señal en vivo (cómo se verificó) |
|---|-----------|----------------|----------------------------------|
| 1 | **mariocasanova.com** | ✅ **LIBRE** | Verisign RDAP autoritativo → 404. Control `google.com` → 200. Alta confianza. |
| 2 | **mariocasanova.dev** | ✅ **LIBRE** | rdap.org → 404. Control `web.dev` → 200 (registrado). Alta confianza. |
| 3 | **mariocasanova.io** | ✅ **LIBRE** | `whois.nic.io` responde literalmente "Domain not found". Alta confianza. |
| 4 | **mariocasanova.mx** | ✅ **LIBRE** | `whois.mx` responde "No_Se_Encontro_El_Objeto / Object_Not_Found". Alta confianza. |
| 5 | **mariocasanova.app** | ✅ **LIBRE** | rdap.org → 404. Control `web.app` → 200 (registrado). Alta confianza. |
| 6 | **macasanova.com** | ✅ **LIBRE** | Verisign RDAP autoritativo → 404. Alta confianza. |
| 7 | **mario-casanova.com** | ✅ **LIBRE** | Verisign RDAP autoritativo → 404. Alta confianza. |

**Los siete candidatos están libres.** Es un lujo poco común: el `.com` exacto de tu nombre rara vez está disponible.

**Caveats de verificación (viajan con la afirmación):**
- La disponibilidad RDAP/WHOIS es un fuerte indicio, **no una garantía de compra**: un dominio puede tener estatus "premium", reserva del registro o un precio especial que solo se revela en el checkout del registrador. Nada de esto se pudo confirmar sin iniciar una compra (compuerta de dinero — no ejecutada).
- Para `.mx` no pude confirmar en vivo si el registro impone verificación de titular / requisito de presencia local en el momento de compra (Cloudflare documenta que `.ca`, `.mx`, `.nz` tienen "registrant verification requirements"). Verificar en el checkout.
- `mariocasanova.data` **no es candidato viable**: `.data` no es un TLD delegado (no existe como extensión comprable).
- `macasanova.*` y `mario-casanova.*` los verifiqué solo en `.com`; no repetí en otras TLD porque no son la recomendación.

---

## 2. Comparación de registradores (precio 1er año vs. RENOVACIÓN)

Todos los precios en USD/año. La renovación importa más que el primer año: muchos registradores usan un precio-gancho el primer año y suben fuerte al renovar.

| TLD | **Cloudflare** (registro = renovación) | **Porkbun** (1er año / renovación) | **Namecheap** (1er año / renovación) |
|-----|----------------------------------------|------------------------------------|--------------------------------------|
| `.com` | **$10.46** (igual siempre) | $9.73 / **$11.08** | ~$6.79–9.58 promo / **~$14.78** |
| `.dev` | **$12.20** (igual siempre) | ~$12 / ~$12 | promo aplica / ~$13–15 (no confirmado) |
| `.io` | **$50.00** (igual siempre) | $32.37 / **$51.80** | $32.98+ / alto (premium) |
| `.mx` | **$30.70** (listado como soportado) | soporte/precio no confirmado | varía |
| `.app` | **$14.20** (igual siempre) | ~$12 / ~$12 | — |

**Lecturas clave:**
- **Cloudflare Registrar** vende "a costo" (precio mayorista del registro, sin margen). Consecuencia práctica: **el precio de registro es idéntico al de renovación** — no hay sorpresa en el año 2. Incluye WHOIS privacy y DNSSEC gratis, sin upsells. *Condición:* el dominio debe gestionarse dentro de una cuenta Cloudflare usando su DNS (el plan gratuito basta). No ofrece hosting de correo (usarías reenvío o correo externo — que ya es tu caso).
- **Porkbun** es el más barato en `.com` el primer año ($9.73) y su renovación ($11.08) sigue siendo baja y honesta. Buen candidato si no quieres mover el DNS a Cloudflare. WHOIS privacy, SSL Let's Encrypt y DNSSEC gratis.
- **Namecheap** tiene el gancho más agresivo el primer año ($6.79 con promo) pero **la renovación salta a ~$14.78** — el patrón clásico de precio-gancho. En un horizonte de 5+ años sale más caro que Cloudflare o Porkbun.
- En `.io`, el costo mayorista subió mucho en 2026 (~$50 a costo; Porkbun renueva a $51.80). Ya no es barato.

---

## 3. Tradeoffs por TLD

- **`.com`** — Confianza por defecto. Es lo que un reclutador teclea sin pensar; nadie duda de un `.com`. Sin peculiaridades técnicas. **Mejor opción para una marca personal basada en el nombre.**
- **`.dev`** — Fuerza HTTPS: `.dev` está en la lista de precarga HSTS del navegador, así que **siempre** carga por HTTPS (imposible servir en HTTP plano). Señal positiva de higiene técnica y muy coherente con un perfil de datos/ingeniería. Barato (~$12). Ideal como dominio secundario o de redirección.
- **`.io`** — Popular en tech, pero (a) caro (~$50/año a costo, con renovación al alza) y (b) **incertidumbre geopolítica**: `.io` es la ccTLD del Territorio Británico del Océano Índico (islas Chagos), cuya soberanía está en proceso de transferencia a Mauricio; el futuro a largo plazo de la extensión es incierto. **No lo recomiendo como dominio principal.**
- **`.mx`** — Tu país; buena señal de identidad local y disponible. Contras para tu caso: menor confianza por defecto ante una audiencia internacional/reclutadores globales, precio mayor (~$30.70) y posible verificación de titular en el registro. Excelente como **secundario/redirección**, no como principal.
- **`.app`** — Igual que `.dev`, fuerza HTTPS (HSTS preload). Más orientado a productos/aplicaciones que a marca personal; menos natural para un portafolio con tu nombre.

---

## 4. Recomendación

**Registra `mariocasanova.com` en Cloudflare Registrar.**

Razonamiento:
1. **El nombre.** El `.com` exacto de tu nombre está libre — es el activo de marca personal de mayor valor y menor fricción. Es directo, memorable y es lo que un reclutador asume por defecto.
2. **El registrador.** Cloudflare cobra a costo y **registro = renovación** ($10.46/año estable), sin el juego de precio-gancho que usa Namecheap. WHOIS privacy y DNSSEC gratis. Y si el sitio termina en Cloudflare Pages (pendiente de T-101), tener el dominio en Cloudflare simplifica DNS y certificados en un solo panel.
3. **El tradeoff aceptado.** Cloudflare exige que el DNS del dominio viva en una cuenta Cloudflare (plan gratis) y no hace hosting de correo. Para un portafolio con correo por reenvío/externo, no es limitante. Si prefieres no atar el DNS a Cloudflare, **Porkbun** es la alternativa equivalente y honesta ($9.73 → $11.08).

**Extra opcional (barato, ~$12/año):** registra también `mariocasanova.dev` y redirígelo al `.com`. Refuerza el perfil técnico y bloquea una variante obvia. No es necesario, pero es barato y coherente.

**Qué NO recomiendo como principal:** `.io` (caro + incertidumbre geopolítica) y `.mx` (menor confianza global, verificación de titular) — ambos sirven mejor como secundarios/redirecciones si quieres.

---

## 5. Siguientes pasos (los ejecuta Mario — compuerta de dinero)

1. Confirmar en el checkout del registrador que `mariocasanova.com` no aparece como "premium" ni con precio especial (no pude verificarlo sin iniciar compra).
2. Comprar en Cloudflare Registrar (o Porkbun) — **acción manual de Mario**.
3. Activar WHOIS privacy + DNSSEC (gratis en ambos).
4. Conectar el DNS al host elegido en T-101.

---

### Fuentes de precios (consultadas 2026-07-05)
- Cloudflare Registrar (precio a costo, TLD soportados): cloudflare.com/products/registrar/ ; cfdomainpricing.com
- Porkbun (precios registro/renovación): porkbun.com/products/domains
- Namecheap (precios registro/renovación): namecheap.com/domains/ ; priceworld.com/domains/namecheap/
- Disponibilidad: RDAP Verisign (`.com`), rdap.org (`.dev`/`.app`), `whois.nic.io` (`.io`), `whois.mx` (`.mx`).
