# PortGoose

A tiny GitHub Pages experiment: enter text on a web page, commit it into `log.json` in this repository, and view the log on the same page.

## Launch the site

1. In **Settings → Pages**, select **Deploy from a branch**.
2. Choose the **main** branch and **/(root)**, then save.
3. Once Pages deploys, open `https://savageperson334.github.io/Upsteb/`. After renaming this repository to **PortGoose**, the expected project URL is `https://savageperson334.github.io/PortGoose/`.

The page detects the repository name from the GitHub Pages URL, so a normal rename does not require editing its JavaScript.

## Test writing an entry

1. Open [GitHub's fine-grained token creation page](https://github.com/settings/personal-access-tokens/new).
2. Set **Repository access** to **Only select repositories**, choosing this repository.
3. Set **Repository permissions → Contents** to **Read and write**; keep other permissions minimal.
4. Copy the token and paste it in the site's **GitHub token** input.
5. Type text and select **Add to log**. The page commits a new version of `log.json` on the `main` branch and refreshes the viewer.

The viewer can be used without logging in or supplying a token because the repository is public. Each committed entry has a timestamp and text. It also appears in GitHub's commit history.

**Security:** Never put a GitHub token into `index.html`, `log.json`, a commit, or a URL. The page uses the token from the input only for API requests and does not save it in browser storage. This is a personal/small-test prototype, **not an anonymous public write form**; an untrusted page, browser extension, or script could still steal a token typed into it. For general-public submissions without GitHub credentials, replace token-based writing with an authenticated serverless backend.

## Files

- `index.html` — responsive GitHub Pages UI, form and viewer; no build system.
- `log.json` — public append-only-in-practice array of entries, modified with GitHub's Contents API.
- `README.md` — setup guide.

## Repository rename

In **Settings → General → Repository name**, enter **PortGoose** and select **Rename**. If the old Pages URL no longer works, use the new `/PortGoose/` URL and verify the Pages deployment under Settings → Pages.

If this log becomes busy, a backend or per-submission GitHub issue strategy will scale better than repeatedly rewriting the whole JSON file.
