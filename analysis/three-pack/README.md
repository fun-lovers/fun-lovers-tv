# Three-package crawler analysis — full-retention revision

This revision follows the user's latest instruction: retain Fantaiying (饭太硬), netdisk/cloud-drive sources, and all previously named exclusions. No category-based filtering is applied to sites, JS, Python, JARs, or extension assets.

The three supplied packages contain 1,563 site records:
- 300 JS/Python file-backed and CMS entries in `tvbox-unified.json`
- 1,051 JAR-backed entries across 16 single-JAR configs
- 212 native/remote entries retained in the complete catalog for later adaptation

Inventory: 442 file paths, 340 unique contents (190 JS, 129 Python, 21 JAR); 102 exact duplicate copies. All 442 inventory rows are marked included. Excluded site/JAR arrays are empty. No missing local references were found.

Keyword matches (overlapping, not additive): 饭太硬 49; 网盘 92; 云盘 25; 夸克 16. The supplied packages did not contain explicit Internet Archive/archive.org/NASA science-media site records; these categories are no longer filtered and will be retained if encountered in future imports.

Different JAR Spider implementations remain in separate configs because a standard TVBox config generally exposes one top-level `spider` field. Online source availability and real-device playback remain unverified.

The complete runtime ZIP is a separate local deliverable and is not yet uploaded to this branch. Upload it as `unified-tvbox-bundle.zip` at the repository root to enable the Pages workflow described in DEPLOYMENT.md.
