---
description: Prueba localmente un PR de Dependabot (checkout, build, migrate, pytest), con hasta 2 reintentos con fix diagnosticado.
argument-hint: <pr-number>
---

# Dependabot Test PR — Subrutina

Probás UN PR de Dependabot localmente, de punta a punta, con hasta 3 ejecuciones totales del pipeline (1 intento inicial + 2 reintentos con un fix mínimo diagnosticado entre medio). Devolvés `pass` o `fail_final` a quien te invocó, con los logs y el detalle de lo intentado.

PR a procesar: `$1` (si te invocaron desde `/dependabot-review`, ya tenés el número de PR y su `headRefName`).

## 1. Checkout seguro

Dependabot commitea en ramas del propio repo (no forks), así que:

```
git fetch origin <headRefName>
git checkout <headRefName>
```

No asumas que `headRefName` ya está actualizado localmente — siempre fetch antes del checkout.

## 2. Ciclo de hasta 3 ejecuciones

Por cada intento (1, 2, 3):

```
podman compose -f local.yml build
podman compose -f local.yml run --rm django python manage.py migrate
podman compose -f local.yml run django pytest
podman compose -f local.yml down
```

Reglas del ciclo:

- Ejecutá `down` siempre, incluso si `build` o `migrate` fallaron antes de llegar a `pytest` — nunca dejes contenedores/volúmenes huérfanos entre intentos.
- Capturá el log completo (stdout+stderr) de la primera etapa que falle. Si todo pasa (build + migrate + pytest sin errores), devolvé inmediatamente el resultado "pass" y no sigas intentando.
- Si es el intento 3 y falló: devolvé el resultado "fail_final" con los logs y el detalle de los intentos, sin aplicar ningún fix más.

## 3. Diagnóstico y fix mínimo (solo entre intentos 1→2 y 2→3, nunca después del 3)

Cuando un intento falla y todavía quedan intentos disponibles, armá el contexto de diagnóstico:

- Título y cuerpo del PR (qué dependencia sube, de qué versión a qué versión).
- Etapa exacta que falló (build / migrate / pytest).
- Log completo de esa etapa.
- Diff del PR (`gh pr diff <n>`) para ver exactamente qué cambió el bump.

Con eso, diagnosticá la causa raíz real (no genérica) y aplicá un único fix mínimo dirigido a esa causa. Ejemplos de fixes válidos: ajustar una opción de configuración en `config/settings/` que cambió de comportamiento en la nueva versión, agregar una migración de Django si el error es de esquema, ajustar un Dockerfile bajo `compose/` si el error es de build de imagen, agregar un pin adicional en `requirements/*.txt` si hace falta una dependencia transitiva compatible.

### Límites estrictos — estos NO son negociables

Permitido tocar:
- Código de la app (`watchedmovies/`, `config/settings/`, etc.)
- `requirements/base.txt`, `requirements/local.txt`, `requirements/production.txt` (agregar pines, nunca revertir el bump que hizo Dependabot)
- Dockerfiles bajo `compose/`
- Migraciones nuevas de Django (generadas con `manage.py makemigrations` si el error es de modelo/esquema)

Prohibido tocar:
- Cualquier archivo de test (rutas bajo `tests/`, `test_*.py`, `tests.py`)
- La sección de configuración de pytest/herramientas de lint en `pyproject.toml`
- `.github/workflows/ci.yml`
- El propio archivo o línea que Dependabot modificó como el bump en sí (el objetivo es que el código conviva con la versión nueva, nunca revertir el PR)

Si diagnosticás que el fix necesario requeriría tocar algo de la lista prohibida (por ejemplo, el error solo se resuelve bajando la versión de vuelta, o requiere reescribir tests) — abortá el ciclo inmediatamente y devolvé "fail_final" sin gastar el intento restante en un fix que sabés de antemano que vas a descartar.

Si el fix sí aplica dentro de los límites permitidos, aplicalo, agregá al staging solo los archivos concretos que modificaste (nunca un `add` masivo de todo el working tree), commiteá con un mensaje descriptivo del tipo "fix: adjust for dependency bump (auto-fix attempt N)", y empujá ese commit a la rama del PR (`HEAD` hacia `<headRefName>` en `origin`, nunca hacia `main`/`master`). Después volvé al paso 2 para el siguiente intento del ciclo.

## 4. Al terminar (pass o fail_final)

No hagas checkout de vuelta a la rama original acá — eso es responsabilidad de quien te invocó (`/dependabot-review`), que necesita hacerlo en su propio flujo final sin importar qué subrutina lo llamó. Vos solo devolvés el resultado ("pass" / "fail_final") con los logs y el resumen de qué se intentó en cada paso, para que el orquestador arme el plan de remediación si hace falta.

## Guardrails — no negociables

- Nunca empujes commits a `main`/`master` — solo a la rama del propio PR de Dependabot que estás procesando.
- Nunca corras dos PRs en paralelo en esta subrutina — asumís que sos la única instancia corriendo podman compose en este momento.
- Nunca toques los archivos de la lista prohibida, ni siquiera "temporalmente para probar" — si hace falta, es "fail_final", no un experimento.
