# PortGoose · Mutation Lab

**Live website:** https://savageperson334.github.io/PortGoose/

PortGoose is a GitHub Pages experiment where **buttons mutate an evolving procedural form**. The page stores a stack of operations in GitHub, GitHub Actions runs a Python geometry engine, and the page renders the generated result.

The old text/log experiment is still present as a read-only archive; **text commands no longer control the sandbox**.

## How to try it

1. Open the website.
2. Paste the same **fine-grained PortGoose token** as before into the GitHub session field (repository-scoped **Contents: Read and write**). You only need it to save changes; anyone can view the specimen.
3. Select a mutation from the library, such as **Grow**, **Fork**, **Twist**, **Mirror**, **Ripple**, **Bloom**, **Prune**, or **Thicken**.
4. Reorder the mutation stack with **↑ / ↓**, disable an operation with **◎**, or remove it with **×**. The order matters: each stage transforms the shape created by earlier stages.
5. Use **Re-seed** to alter deterministic growth, **Surprise mutation** to add a random operation, or **Reset stack** to return to the single stem.

Each click that changes state commits `sandbox-input.json`. The [Python mutation workflow](.github/workflows/python-sandbox.yml) runs [the safe geometry engine](scripts/mutate.py) and commits `sandbox.json`. The browser fetches both files from GitHub and draws the geometry as SVG. It checks more frequently after your own authenticated mutations; public views refresh more slowly to avoid GitHub's API rate limit.

The initial organism was generated with **Grow → Fork → Bloom**, giving 4 segments and 2 blossoms. Multiple sequential mutations can create branching, reflections, warping and decorated tips.

## Data pipeline

```text
Click button / change stack
    ↓
sandbox-input.json (ordered, enabled/disabled operation definitions)
    ↓
GitHub Actions (standard runner, Python 3.11, unit tests)
    ↓
scripts/mutate.py
    ↓
sandbox.json (segments, blooms, counts, bounds, revision)
    ↓
GitHub Pages SVG visualisation
```

The engine never evaluates arbitrary submitted Python or expression text. It only recognizes an explicitly whitelisted set of operations with bounded geometry output and a maximum 18-step stack. Public repo files and mutations can be inspected in GitHub's commit history.

## Files

| Path | Purpose |
| --- | --- |
| `index.html` | Button-based mutation lab and read-only legacy log |
| `mutation-app.js` | GitHub input/output synchronization and SVG visualisation |
| `mutation-style.css` | Responsive dark interface |
| `sandbox-input.json` | Source-of-truth operation stack, enabled flags and seed |
| `scripts/mutate.py` | Pure-Python procedural geometry engine |
| `tests/test_mutate.py` | Tests for ordering, toggling, caps and determinism |
| `.github/workflows/python-sandbox.yml` | Compute and commit pipeline |
| `sandbox.json` | Generated model and stats |
| `log.json`, `scripts/process_log.py` | Retained from earlier text/math experiment; no longer in the current workflow |

## Notes

- **Actions cost:** For this public repository, normal GitHub-hosted standard runners are free. Each mutation still creates Git commits and an Actions run, and Actions has usage limits.
- **GitHub security:** The browser sends your token directly to GitHub for writes, does not save it in browser storage, and never includes it in a commit. Only enter it on the correct PortGoose website. Since the repository is public, all mutations and generated models are public. This is a small personal experiment, not a secure, token-free public submission service.
- **Deploy:** Pages builds `main` from `/(root)`. The viewer fetches the new generated `sandbox.json` without needing a new Pages build.
- **Concurrency:** The workflow fetches the latest `main` before computing and retries if another mutation arrives, so an older pending run should not overwrite newer inputs.
