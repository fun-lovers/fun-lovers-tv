# Three-package crawler analysis

This branch adds the static-analysis and reorganization report for the Xingwei, Xiaosa, and Baohe TVBox packages.

- 442 JS/Python/JAR file paths; 340 unique contents after SHA-256 deduplication.
- 197 file-backed JS/Python and CMS entries in the unified main config.
- 247 JAR-backed entries split across six single-JAR configs.
- 916 entries excluded under the user's existing exclusions, including netdisk/cloud-drive content and the Fantaiying line.
- No missing local references in the generated local package.

Important: this branch contains analysis documentation only. The full runtime package is a separate 19 MB ZIP deliverable; it has not been uploaded to this branch or deployed to Pages. Do not treat the analysis branch as a live import endpoint.
