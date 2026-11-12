# Runtime and Dependency Issue Register

| ID | Priority | Finding | Impact | Planned treatment |
|---|---|---|---|---|
| RT-001 | P0 | No evidence yet of automated end-to-end tests across TVBox client variants | Import success does not prove spider execution or playback | Define client/runtime matrix and label untested cases clearly |
| RT-002 | P1 | drpy2 runtime is downloaded from upstream during build without a recorded immutable version/hash in the reviewed workflow | Upstream changes can alter builds unexpectedly | Pin upstream commit/release and verify SHA-256 |
| RT-003 | P1 | Python spider dependencies are not declared in a central runtime matrix | Client environments may lack requests/crypto/Brotli or provide incompatible versions | Add per-spider dependency and capability matrix; avoid assuming pip is available inside TVBox |
| RT-004 | P1 | Python spiders rely on host-specific Spider APIs and proxy behavior | Same script may fail across TVBox forks | Add compatibility adapters or explicit support declarations |
| RT-005 | P1 | Unified bundle validation is primarily structural and does not prove runtime imports/JAR linkage | Archive can validate but fail at runtime | Extend static checks and include artifact manifest |
| RT-006 | P1 | Release archive is separate from tracked source tree | Published JSON may not correspond transparently to a source commit | Record release tag, source commit, file hashes and build provenance |
| RT-007 | P2 | Pages workflow path filters do not cover every configuration/package area | Some source changes may not trigger a rebuild | Review and expand path filters after confirming desired publishing behavior |
| RT-008 | P2 | VOD health check does not verify media bytes or playback | Endpoint health can overstate usability | Separate API, media URL and client playback status |
| RT-009 | P2 | Live playlists are not covered by the same health pipeline | Broken M3U/channel URLs may remain unnoticed | Add bounded playlist/stream checks with clear rate limits |
| RT-010 | P2 | Multiple catalogues have no fully documented single-source generation contract | Configuration drift and duplicates | Define canonical inputs and deterministic generated outputs |

## Scope notes
These are findings from the first-pass workflow/config/code review, not claims that every listed issue has already caused a production failure. Items requiring a full read or an actual TVBox client remain marked for further verification.
