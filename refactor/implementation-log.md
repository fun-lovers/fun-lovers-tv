# Implementation Log

## Branch and safety
- Branch: `refactor/runtime-deps-audit-2026-11`
- Base: `main` at `35bd207a4bd2f9a35800efb8f841ae955b3b5f7d`
- `main` has not been modified or merged.
- Existing source files and published URLs are retained; changes are isolated to this branch.

## Completed in this pass

### Repository inventory and dependency mapping
- Recorded the full main-branch baseline inventory: 35 tracked files across 16 directories.
- Documented the drpy2 static build, single-tvbox Python runtime, VOD health-check and unified Release/Pages build chains.
- Added a per-spider runtime matrix. Build-time Python requirements remain standard-library-only; TVBox Python dependencies are documented separately because GitHub Pages cannot install packages into the client runtime.

### Runtime and code fixes
- Pinned drpy2 runtime to upstream commit `ca23ffdbf5e429c5893ac60158668fc5af7af192`.
- Verified pinned runtime SHA-256: `fa829edf7d7e8e2453151322948940b85d9c9258144cbdd7430722e887e95a5d`; Pages build now enforces the checksum and records provenance.
- Restored TLS certificate verification in Ruyi HTTP requests and removed global urllib3 warning suppression.
- Changed Douban and Hongguo Spider import fallback paths to resolve from `__file__`, not the process working directory.
- Fixed YouTube Data API pagination to use cached `nextPageToken` values.
- Hardened unified ZIP extraction with entry-count, per-file and total-size limits, compression-ratio limits, duplicate-name checks, and rejection of symlinks/backslash paths.

### JAR/DEX audit
The Release asset `tvbox-bundle-v1/unified-tvbox-bundle.zip` was downloaded and inspected in GitHub Actions:
- 29 JARs, 25 JAR configuration JSON files, 69 JAR references.
- 29 valid ZIP/JAR containers with Android `classes.dex` payloads; 28 DEX 035 and 1 DEX 037.
- No ordinary JVM `.class` payload was found in these archives.
- DEX type tables reference CatVod host APIs, Android framework packages, protobuf, Gson, Rhino, QuickJS, RxHttp, SLF4J, OkHttp and other libraries.
- Four JARs contain native libraries: four ARMv7 and four ARM64 shared objects.
- CI emits a `jar-runtime-audit` artifact containing per-JAR SHA-256, DEX metadata, package prefixes, native ABI and configuration references.

## Validation completed

Latest refactor CI run:
- Run ID: `43182365467`
- Result: success
- Checks passed:
  - workflow YAML parsing
  - Python runtime/dependency contract checks
  - every repository JSON file parses with no duplicate keys
  - single-tvbox config validation
  - Python compileall
  - actual pinned drpy2 runtime download + SHA-256 check + static build smoke test
  - unified ZIP extraction and configuration validation smoke test
  - Release bundle unpack/validation and JAR/DEX audit
  - Node.js syntax check for all drpy2 JS rules

## Not yet verified

1. Import and playback in real TVBox/影视仓 client variants. CI cannot prove the client host APIs, proxy implementation, Android API level or native ABI are compatible.
2. Runtime execution of each of the 29 DEX JARs. The audit is structural and metadata-based, not a decompilation or device execution test.
3. Ruyi live TLS handshake and media playback after restoring certificate verification.
4. Full source-index normalization: `ysc-doc.json` and `ysc-doc-source.json` have different roles/counts that still need an explicit source-of-truth contract.
5. Remaining file-by-file call-flow and JAR-to-source mapping, especially the shared JARs used by many site entries.

No changes have been merged to `main`; the branch is ready for continued analysis and review, not yet a production release.
