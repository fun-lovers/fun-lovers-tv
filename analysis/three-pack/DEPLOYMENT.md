# Pages deployment for the unified crawler bundle

The unified crawler ZIP is stored as a GitHub Release asset, not committed to the Git repository. This avoids the 25 MiB browser file-upload limit for repository files and keeps the binary bundle out of Git history.

## Upload using only the GitHub website

1. Open the repository: https://github.com/fun-lovers/fun-lovers-tv
2. Open **Releases** (or visit https://github.com/fun-lovers/fun-lovers-tv/releases).
3. Choose **Draft a new release**.
4. Create a tag such as `tvbox-bundle-v1`.
5. For **Target**, choose `feature/three-pack-unified-crawlers` while this PR is still open. After the PR is merged, use `main` for later bundle updates.
6. Set the release title, for example `TVBox unified bundle v1`.
7. In **Attach binaries by dropping them here or selecting them**, select the complete `unified-tvbox-bundle.zip` (about 42–56.5 MiB). Do not rename it.
8. Wait until the upload finishes and the asset appears in the release draft, then click **Publish release**.

GitHub documents a maximum size below 2 GiB per release asset. The 25 MiB limit shown on the repository's **Add file → Upload files** page applies to regular repository files, not Release assets.

## What happens after publishing

- The `release: published` event starts `.github/workflows/deploy-drpy2-pages.yml`.
- GitHub Actions downloads the exact release asset named `unified-tvbox-bundle.zip`.
- The workflow safely unpacks `unified-deliverable/` into `dist/unified`, validates the main JSON and local relative resource paths, then deploys Pages.
- After the PR is merged, pushes to `main` also pick up the latest published release asset when one exists.
- You can also run the workflow manually and optionally enter a release tag; leaving it blank uses the latest published release.

After a successful Pages deployment, the main import URL is:

```
https://fun-lovers.github.io/fun-lovers-tv/unified/tvbox-unified.json
```

The JAR-specific configs are published under `/unified/jar-configs/`. They remain separate because each config uses one Spider JAR. The main config contains JS/Python file-backed rules and direct CMS API entries; it does not automatically load the separate JAR-backed configs.

## Important

The old locally generated ZIP is not currently present in the working session, so it must be regenerated or recovered before it can be attached to the Release. The workflow changes do not themselves recreate the binary package. Static validation also does not prove that sources are online or that playback works in a TVBox client.
