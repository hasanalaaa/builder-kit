# Enforcement: make the structure impossible to erode

A rule that isn't checked by a machine will be broken, by people in a hurry and by AI agents that don't see the whole codebase. Install these on day one of a new project, or one at a time while untangling an old one. Before adding any tool: confirm it's the real, maintained package, check its current docs for config syntax, and prefer tools the project already uses.

Order of value: **formatter → linter → strict types → tests → boundary rules → dead-code and duplication checks → pre-commit → CI**.

---

## 1. Formatter (zero style debates)

- JS/TS: Prettier, or Biome (formatter + linter in one tool).
- Python: `ruff format`. Go: `gofmt`. Rust: `rustfmt`. Swift: `swift-format` / SwiftFormat. Kotlin: ktlint. Dart: `dart format`.

## 2. Linter

- JS/TS: ESLint (flat config) with the framework's recommended config, or Biome.
- Python: `ruff check` (enable at least `E,F,I,B,UP,SIM`).
- Go: `golangci-lint`. Swift: SwiftLint. Kotlin: detekt. Dart/Flutter: `flutter_lints` or `very_good_analysis`.
- Useful size/complexity rules: ESLint `max-lines`, `max-lines-per-function`, `complexity`, `max-depth`, `max-params`; ruff `C90` (mccabe) and `PLR0913`.

## 3. Strict types

TypeScript `tsconfig.json`: `"strict": true`, `"noUncheckedIndexedAccess": true`, `"noImplicitOverride": true`, `"noFallthroughCasesInSwitch": true`, plus a `paths` alias (`"@/*": ["./src/*"]`) so imports never climb `../../../`.
Python: mypy `--strict` or pyright `strict` on new code; type hints required on public functions.

---

## 4. Boundary rules (the wiring diagram as code)

### JS/TS: dependency-cruiser (CLI, runs in CI, also draws the graph)

`.dependency-cruiser.cjs`:
```js
module.exports = {
  forbidden: [
    { name: 'no-circular', severity: 'error', from: {}, to: { circular: true } },
    {
      name: 'feature-front-door',
      comment: 'A feature may import another feature only through its index file',
      severity: 'error',
      from: { path: '^src/features/([^/]+)/' },
      to: {
        path: '^src/features/[^/]+/.+',
        pathNot: ['^src/features/$1/', '^src/features/[^/]+/index\\.(ts|tsx|js|jsx)$'],
      },
    },
    {
      name: 'shared-is-a-leaf',
      comment: 'shared/ must not depend on features or the app shell',
      severity: 'error',
      from: { path: '^src/shared/' },
      to: { path: '^src/(features|app)/' },
    },
    {
      name: 'no-orphans',
      severity: 'warn',
      from: { orphan: true, pathNot: ['\\.d\\.ts$', '(^|/)\\.[^/]+\\.(js|cjs|mjs|ts|json)$'] },
      to: {},
    },
  ],
  options: {
    doNotFollow: { path: 'node_modules' },
    tsConfig: { fileName: 'tsconfig.json' },
  },
};
```
Run: `npx depcruise src --config .dependency-cruiser.cjs`. Graph: `npx depcruise src --include-only '^src' --output-type dot | dot -T svg > deps.svg`.

### JS/TS: eslint-plugin-boundaries (instant feedback in the editor)

Define element types (`app`, `feature`, `shared`) by path patterns and allow only `app → feature → shared` with entry-point-only imports between features. Check the plugin's current README for the exact rule names and settings in the installed major version. The two tools complement each other: ESLint for the editor, dependency-cruiser for CI.

### Monorepos: Nx

Tag projects (`type:app`, `type:feature`, `type:ui`, `scope:orders`) and use `@nx/enforce-module-boundaries` with `depConstraints`.

### Python: import-linter

`pyproject.toml`:
```toml
[tool.importlinter]
root_package = "app"

[[tool.importlinter.contracts]]
name = "Layered architecture"
type = "layers"
layers = [
    "app.main",
    "app.features",
    "app.core",
]

[[tool.importlinter.contracts]]
name = "Features are independent"
type = "independence"
modules = [
    "app.features.orders",
    "app.features.billing",
]
```
Run: `lint-imports`.

### Other stacks
- Go: put packages under `internal/`; enforce layer rules with `depguard` in golangci-lint.
- JVM (Java/Kotlin): ArchUnit tests. .NET: NetArchTest. Ruby: Packwerk.
- Swift: split features into local Swift packages; the compiler enforces their declared dependencies.

### Always: arch_check.py

`python3 <skill>/scripts/arch_check.py <repo>` works on any stack (JS/TS and Python get import-graph checks; every language gets size, naming, duplication and dead-code checks). Copy it into the project as `scripts/arch_check.py` so CI and teammates can run it. Tune thresholds with flags (`--help`).

---

## 5. Dead code and duplication

- JS/TS: **knip** (unused files, exports, dependencies): `npx knip`. **jscpd** (copy-paste detection): `npx jscpd --min-lines 8 src`.
- Python: **vulture** (dead code), **deptry** (unused/missing deps). Ruff catches unused imports/variables.
- Go: `staticcheck` (unused code), `golangci-lint` with `dupl`.
- Review every hit before deleting: dynamic imports, framework conventions (Next.js route files) and config files cause false positives.

---

## 6. Pre-commit hooks

- JS/TS: lefthook, or husky + lint-staged, running format + lint (+ typecheck on changed files when fast enough).
- Python/polyglot: the `pre-commit` framework with ruff and a secrets scanner (see `launch-security`).
Keep hooks under ~10 seconds; slow checks belong in CI.

---

## 7. CI (the final gate)

Every push / PR runs, failing the build on errors:
1. Install from the lockfile (frozen).
2. Format check, lint, type check.
3. Tests.
4. Boundary rules (dependency-cruiser / import-linter / Nx).
5. `python3 scripts/arch_check.py .`
6. Dead-code and duplication checks (warn first, then fail once the baseline is clean).
7. Security checks from `launch-security` (H13).

Protect the main branch: required status checks and reviews. Ratchet: when a metric improves (fewer warnings, lower duplication), tighten the threshold so it can't slide back.
