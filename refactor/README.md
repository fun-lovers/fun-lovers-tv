# Runtime and Dependency Refactor

This branch is an additive refactor workspace. Existing project files and published entry points are preserved.

## Baseline
- Source branch: `main`
- Scope: repository inventory, runtime/dependency mapping, issue register, then isolated fixes and validation.
- Deployment target: GitHub Pages static hosting; Python is used only for build/check tasks unless a separate backend is explicitly deployed.
- Client-side Python spiders depend on the Python/Spider APIs supplied by the target TVBox-compatible client.

## Work sequence
1. Inventory and dependency map.
2. Runtime compatibility and dependency declarations.
3. Isolated fixes in new files or additive configuration.
4. Static checks and GitHub Actions verification.
5. Client import/playback verification where a real client is available.

## Important limits
A successful JSON parse, HTTP status, or GitHub Pages deployment does not prove that a TVBox client can execute a spider or decode a media stream. Those are separate validation layers.
