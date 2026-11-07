# PortGoose

A GitHub Pages experiment: submit a note or math command from a website; commit it into the repository; watch GitHub Actions process commands with Python and display the result in a sandbox on the same page.

**Website:** https://savageperson334.github.io/PortGoose/

## What works

1. **New entry:** submit text using a fine-grained GitHub token restricted to this repository.
2. **Log:** `log.json` is updated via GitHub's Contents API; the page displays the log.
3. **Python sandbox:** a push changing `log.json` triggers [the workflow](.github/workflows/python-sandbox.yml). It runs [a safe Python expression evaluator](scripts/process_log.py), writes `sandbox.json`, and commits the result.
4. **Live viewer:** the sandbox section reads `sandbox.json` directly from GitHub. It can show a calculated value or a function graph without rebuilding the website.

The first end-to-end checks were `calc (12+8)*3` (result **60**) and `plot sin(x)` (**81** samples from −10 to +10).

### Commands

Submit any of these in the regular message field:

```text
calc (12+8)*3
calc sqrt(144)
calc 2^10
plot sin(x)
plot cos(x)*3
plot x^2
plot sqrt(x)
```

The latest valid `calc` or `plot` command determines the current sandbox. Ordinary notes such as `Howdy` remain in the log but do not change the sandbox. Invalid math commands show a friendly error.

This is **not general Python execution**. The AST-based evaluator only supports arithmetic, constants `pi`/`e`, `x` for plots, and a small whitelist of functions. The code has depth/length/size limits and tests. It does not execute arbitrary scripts, imports, file access, or submitted shell commands.

### Setup / permission

Pages is published from `main` / `(root)` under **Settings → Pages**.

To submit entries, generate a [fine-grained token](https://github.com/settings/personal-access-tokens/new) limited to **PortGoose** with **Contents: Read and write** permission. Paste it into the form when submitting. The site does not save tokens to GitHub or browser storage.

GitHub Actions uses the built-in `GITHUB_TOKEN` with **Contents: write** permission to commit just `sandbox.json`; no extra secret is required. Actions workflow changes and manual runs can also trigger sandbox processing.

**Privacy/security:** the repo and log are public. Never enter passwords, secrets, or personal information in the log. Never commit a GitHub token. This is a single-user experiment, not a secure anonymous public form. The token is sent directly to GitHub by the page, but visiting any untrusted page or running untrusted browser extensions can expose secrets.

**Updates:** after sending a math command, the page checks the result periodically and offers a manual **Check result** button. A GitHub Actions run may take a little time. Its own commits do not necessarily trigger a Pages redeploy, which is why the viewer reads the GitHub file directly.

## Repository files

| Path | Purpose |
| --- | --- |
| `index.html` | Forms, log viewer, math sandbox and SVG plot |
| `log.json` | Public notes and math command history |
| `sandbox.json` | Current Python-calculated result/plot data |
| `scripts/process_log.py` | Restricted math parser and processor |
| `tests/test_processor.py` | Built-in unit tests |
| `.github/workflows/python-sandbox.yml` | GitHub Actions worker |

## Potential future work

A browser-only sandbox would be even faster for simple math, while a separately authenticated agent could eventually propose edits to sandbox configurations. For now, expressions are deliberately limited so submitting a message cannot execute arbitrary Python on a GitHub Actions runner.
