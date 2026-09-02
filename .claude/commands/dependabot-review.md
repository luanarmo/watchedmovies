---
description: Revisa los PRs abiertos de Dependabot, los prueba localmente, y los mergea o escala a un humano.
---

# Dependabot Review — Orquestador

Sos responsable de revisar los PRs abiertos de Dependabot en este repo, probarlos LOCALMENTE, y decidir si mergearlos o escalar el problema a un humano. Nunca tomes atajos con los guardrails de seguridad de este comando — están para evitar pisar trabajo del usuario o mergear algo que no se validó de verdad.

## 0. Preflight (una sola vez, antes de tocar cualquier PR)

1. Guardá la rama actual: `git rev-parse --abbrev-ref HEAD` → `ORIGINAL_BRANCH`.
2. Corré `git status --porcelain`. **Si devuelve cualquier línea, ABORTÁ toda la corrida inmediatamente.** No hagas stash, no hagas commit por el usuario, no sigas — informá que hay cambios sin commitear y terminá acá. Nunca arranques un checkout de PR ajeno sobre un working tree sucio.
3. Corré `git fetch origin`.
4. Verificá que Podman está disponible: `podman info`. Si falla (por ejemplo, la máquina de Podman no está corriendo — `podman machine start`), abortá informando que Podman no está disponible (no es un error a "arreglar" con un fix de código).
5. Asegurate de que existen las labels de tracking en el repo (idempotente, no falla si ya existen):
   - `gh label create "dependabot-review:in-progress" --color FBCA04 --description "Auto-review en curso" --force`
   - `gh label create "dependabot-review:needs-human" --color D93F0B --description "Auto-review falló, requiere revisión humana" --force`

## 1. Listar PRs candidatos

```
gh pr list --state open --json number,author,headRefName,title,labels,body
```

Filtrá **estrictamente** por autor. Un PR solo es candidato si `author.login` corresponde a Dependabot (típicamente `app/dependabot` o `dependabot[bot]` — verificá el valor real que devuelve `gh` en este repo antes de decidir). **Nunca** confíes en el título del PR (ej. "bump X") ni en labels existentes para decidir esto — solo el autor real. Cualquier PR que no cumpla se descarta sin excepción.

## 2. Filtrar por estado de tracking

Para cada PR candidato, mirá sus labels:

- Si tiene `dependabot-review:needs-human` → **saltealo**. Ya fue escalado, un humano tiene que destrabarlo (no se reintenta solo).
- Si tiene `dependabot-review:in-progress`:
  - Mirá hace cuánto se aplicó esa label (`gh pr view <n> --json labels` no trae timestamp de label directamente; si necesitás precisión, revisá el historial de eventos del PR con `gh api repos/{owner}/{repo}/issues/<n>/timeline` filtrando el evento `labeled`). Si pasaron más de 2 horas, tratalo como una corrida colgada: quitá la label y procesalo como si fuera nuevo.
  - Si no pasaron 2 horas, **saltealo** (otra corrida ya lo está procesando, o la corrida anterior no terminó limpio recientemente).
- Si no tiene ninguna de esas dos labels → es candidato a procesar.

## 3. Procesamiento secuencial

**Nunca proceses PRs en paralelo.** Todos comparten los mismos nombres de contenedor, red y puertos de `local.yml` en esta misma máquina — correr dos a la vez produce colisiones y falsos negativos. Procesá un PR completo (de punta a punta) antes de pasar al siguiente.

Para cada PR candidato, en orden ascendente de número:

1. `gh pr edit <n> --add-label "dependabot-review:in-progress"`
2. Ejecutá el flujo de prueba local descrito en `/dependabot-test-pr` para este PR (podés invocar ese comando o seguir su lógica inline — el resultado que necesitás es uno de: `pass`, `fail_final`, junto con los logs y el detalle de qué se intentó).
3. Según el resultado:

   **Si `pass`:**
   - `gh pr review <n> --approve --body "Auto-approved: local pipeline passed (podman compose build + migrate + pytest)."`
   - `gh pr merge <n> --squash --auto` (si el repo tiene auto-merge habilitado y checks de branch protection pendientes) o `gh pr merge <n> --squash` directo si no hay checks bloqueantes pendientes además de tu propia validación local.
   - Si `gh pr merge` falla porque hay checks de branch protection pendientes que no dependen de vos, no lo tomes como error — dejalo así, se reintentará la corrida del día siguiente (quitá igualmente la label `in-progress` para que se reprocese mañana desde cero, sin agregarle ninguna label de fallo).
   - Si el merge fue exitoso: `gh pr edit <n> --remove-label "dependabot-review:in-progress"` (las demás labels de tracking no aplican en este caso porque no hubo fallos).
   - Loggeá en `.claude/loop-state/dependabot-review.log`: `[timestamp] PR #<n> "<title>": MERGED OK`.

   **Si `fail_final`** (se agotaron los 3 intentos del flujo de test — ver `/dependabot-test-pr`):
   - Redactá el plan de remediación (ver sección 4 abajo) y publicalo como comentario en el PR: `gh pr comment <n> --body-file <archivo temporal con el comentario>`.
   - Creá un issue nuevo enlazado: `gh issue create --title "Dependabot PR #<n> requiere revisión manual: <título>" --body-file <mismo contenido>` y comentá en el PR con el link al issue si no quedó ya incluido.
   - `gh pr edit <n> --add-label "dependabot-review:needs-human" --remove-label "dependabot-review:in-progress"`.
   - **No mergees este PR bajo ninguna circunstancia.**
   - Loggeá: `[timestamp] PR #<n> "<title>": ESCALATED (needs-human), issue #<issue-n>`.

4. **Pase lo que pase** (éxito, fallo, o error inesperado): volvé a la rama original con `git checkout $ORIGINAL_BRANCH` antes de pasar al siguiente PR o de terminar. Verificá `git status --porcelain` vacío en `ORIGINAL_BRANCH` al final — si no lo está, algo salió mal con la limpieza del PR anterior; investigá antes de continuar, no sigas a ciegas.

## 4. Formato del plan de remediación (`fail_final`)

Usá esta estructura para el comentario del PR y el issue:

```markdown
## Auto-review de Dependabot: requiere revisión humana

**PR**: #<n> — <título>
**Dependencia**: <ecosistema>/<paquete> <versión actual> → <versión propuesta>
**Intentos realizados**: 3 (1 inicial + 2 fixes automáticos)

### Causa raíz identificada
<tu análisis: en qué etapa falló (build/migrate/pytest) y por qué, en términos concretos
del error observado — no genérico>

### Qué se intentó
1. Intento 1: <resumen del error>
2. Fix aplicado: <resumen del diff> → resultado: <error>
3. Fix aplicado: <resumen del diff> → resultado: <error>

### Plan de remediación sugerido (requiere acción humana)
- [ ] <paso concreto 1>
- [ ] <paso concreto 2>
- [ ] <paso concreto 3>

### Riesgos
- <riesgo concreto 1>
- <riesgo concreto 2>

### Estado
Label `dependabot-review:needs-human` aplicada. Este PR NO fue mergeado automáticamente.
```

## Guardrails — no negociables

- Nunca mergees un PR cuyo autor no sea Dependabot, sin importar qué otras señales tenga.
- Nunca hagas `git push` a `main`/`master`/la rama original — solo a la rama del propio PR de Dependabot que estás procesando.
- Nunca toques archivos de test, `pyproject.toml` (config de pytest), o `.github/workflows/ci.yml` como parte de un "fix" — eso es responsabilidad del flujo de `/dependabot-test-pr`, pero si en algún punto de este orquestador considerás hacerlo, no lo hagas.
- Si el working tree no está limpio al preflight, abortá — no hay excepción a esto.
