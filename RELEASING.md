# Releasing

SuperSlice uses [Semantic Versioning](https://semver.org/) and
[Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/). Docker
images are built and published automatically by GitHub Actions.

## Commit conventions

Every commit message starts with a type:

| Type | Use for | Version impact |
| --- | --- | --- |
| `feat:` | a new feature | minor |
| `fix:` | a bug fix | patch |
| `docs:` | documentation only | none |
| `refactor:` | code change that neither fixes a bug nor adds a feature | none |
| `chore:` | tooling, deps, housekeeping | none |
| `test:` | adding or fixing tests | none |

A `!` after the type (e.g. `feat!:`) or a `BREAKING CHANGE:` footer signals a
major bump.

## Cutting a release

1. Make sure `main` is green (the **Tests** workflow passes).
2. Move the `## [Unreleased]` items in [CHANGELOG.md](CHANGELOG.md) under a new
   version heading with today's date, and add a fresh empty `## [Unreleased]`
   section.
3. Commit the changelog: `docs: release vX.Y.Z`.
4. Tag and push:

   ```bash
   git tag -a vX.Y.Z -m "Release vX.Y.Z"
   git push origin main vX.Y.Z
   ```

## What the tag triggers

The [`docker-build`](.github/workflows/docker-build.yml) workflow publishes
images to GHCR. A `vX.Y.Z` tag produces:

- `ghcr.io/bintangtimurlangit/superslice:X.Y.Z`
- `ghcr.io/bintangtimurlangit/superslice:X.Y`
- `ghcr.io/bintangtimurlangit/superslice:X`
- `ghcr.io/bintangtimurlangit/superslice:latest`

After the workflow finishes, create a GitHub Release for the tag and paste the
changelog entry as the release notes.

## Versioning the slicer

The bundled PrusaSlicer version is independent of SuperSlice's version. If you
change it, note it in the changelog and update [docs/SLICER.md](docs/SLICER.md).
