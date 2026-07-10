# GitHub Release Checklist v1.0

## Pre-Release (T-0)
- [ ] Create repo at https://github.com/new → name: `bioresearch-agent`
- [ ] Copy description from REPO_METADATA.md
- [ ] Add topics from REPO_METADATA.md
- [ ] Set MIT license
- [ ] Push `main` branch (commit a0f07b0)
- [ ] Verify CI badge green
- [ ] Verify 3 demos run on GitHub Actions
- [x] Tag v1.1.0 release
- [ ] Copy release notes from docs/RELEASE_NOTES.md

## Post-Release (T+0 to T+6h)
- [ ] Verify `pip install -e .` works on fresh clone
- [ ] Verify `bioresearch doctor` passes 10/10
- [ ] Verify `bioresearch run literature` produces output
- [ ] Social preview image uploaded (optional)

## Done Criteria
- [ ] GitHub stars > 0 (first star)
- [ ] CI remains green for 7 days
