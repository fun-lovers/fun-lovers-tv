# Pages deployment for the unified crawler bundle

The generated local package is not yet in this repository. To publish it:

1. Upload the generated ZIP as `unified-tvbox-bundle.zip` at the repository root (keep the archive name exact).
2. Merge this PR into `main`.
3. The existing Pages workflow will unpack the bundle into `/unified/` and validate every relative resource reference.
4. After a successful Actions run, import:

```
https://fun-lovers.github.io/fun-lovers-tv/unified/tvbox-unified.json
```

The six JAR-specific configs will be published under `/unified/jar-configs/`. They remain separate because each config uses one Spider JAR. Do not import the main config expecting it to load JAR-backed entries; it contains only JS/Python file-backed rules and direct CMS API entries.
