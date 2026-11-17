# Plan: Export Local QZone Backup to Hexo + GitHub Pages (Markdown)

**Date:** 2026-11-16
**Source:** `Documents/qqZone2026/QQ空间备份_36110494` (QZoneExport, local export)
**Target:** Hexo blog hosted on GitHub Pages, posts in Markdown format
**Status:** Live at https://yanzhuwen.github.io/qqblog/ (2026-11-16). Steps 1–3 done: repo `YanzhuWen/qqblog` (public), `site/` is the git repo, `.github/workflows/pages.yml` deploys on every push to `main`, `_config.yml` has `url: https://yanzhuwen.github.io/qqblog` + `root: /qqblog/`. Step 5 done 2026-11-16: 5,504 images uploaded to R2 bucket `qqzone-images` via `upload-images.sh` (credentials in `r2.env`, not in git); posts now point to the bucket's r2.dev URL. 78 referenced images were never in the local export (list: `upload-failed.txt`); fixed 2026-11-16: 7 QQ emoticon GIFs re-fetched to R2, the other 71 (dead 2010 photo.qq.com photos, empty-src placeholders, a Weibo badge) removed from posts, and `convert.py` now does the same on re-runs. Step 4 done: title 枚 时光日志, author 枚. All plan steps complete.

---

## 1. Source inventory (what we have)

| Item | Detail |
|---|---|
| Export tool | QZoneExport v3.0 (browser extension), QR-code login, data stays local |
| Export folder | `Documents/qqZone2026/QQ空间备份_36110494/` |
| Logs (Blogs) | **721 posts**, 2009-08 → 2026-06 |
| Logs with photos | 534 posts |
| Images referenced | **5,582 unique files** in `Blogs/images/` (~7,025 files total, est. 2–4 GB) |
| Data file | `Blogs/json/blogs.json` (15.1 MB) — title, publish time, category, `custom_html` body, cover image, comment count |
| Old video posts | 44 posts are Youku embeds only (2010-era); video files themselves are not in the export |
| Not in scope for this export | 说说 (Moments), 留言板 (guestbook), 相册 (albums), 视频 (41 mp4s in `Videos/`), comment bodies (only counts kept) |

Key data facts that shape the plan:

- The readable post body is the `custom_html` field (offline-viewer HTML with local image refs `Blogs/images/xxx.jpeg`). The legacy `html` field is messier and is not used.
- In-body photos are `<img src="Blogs/images/xxx.jpeg">`; each post's cover image is in the `img[].custom_url` field.
- Publish times are Unix timestamps in Beijing time (UTC+8); dates are kept as originally published.
- The 5,582 images are too large for a GitHub repo (2–4 GB), so images live on a separate image host (see §5), not in the repo.

---

## 2. Target design (Hexo + GitHub Pages)

- **Generator:** Hexo 8.1.2, **theme:** Butterfly 5.7.2, **language:** zh-CN.
- **Hosting:** GitHub Pages (free). The site is a static site: no server, no database.
- **Repo layout** (source repo, not the generated output):

```
site/
├── _config.yml            # site title, author, url, language, theme
├── package.json           # hexo + hexo-renderer-pug + hexo-renderer-stylus
├── scaffolds/
├── source/
│   └── _posts/            # 721 Markdown posts (one file per log)
└── themes/
    └── butterfly/         # theme files
```

- **Post file format** — one Markdown file per log, named `YYYY-MM-DD-<blogId>.md`:

```markdown
---
title: <original log title>
date: 'YYYY-MM-DD HH:mm:ss'     # Beijing publish time
categories:
- <QQ category, e.g. 个人日记 / 我的图志>
qzone_id: '<blogId>'
cover: /images/qzone/<first-image>.jpeg   # if the post has photos
comments_count: <number>                   # if > 0
---

<post body converted from HTML to Markdown>

![图片](/images/qzone/xxx.jpeg)
```

- **Conversion rules** (already implemented in `convert.py`):
  - Clean legacy QQ markup: drop loading/spacer/remote-emoticon gifs, empty `<p>&nbsp;</p>`, inline styles, `lightgallery` link wrappers (keep the image).
  - Convert cleaned HTML to Markdown (ATX headings, `-` bullets).
  - Rewrite local image refs to the image-base path (`/images/qzone/<file>` by default).
  - Preserve old Youku video embeds as links (`▶ 原视频（优酷，可能已失效）`) instead of dropping them — this keeps the 44 video-only posts non-empty.
  - Filenames use publish date + blogId, so there are no collisions even for duplicate titles (e.g. monthly `2025年12月` posts).

---

## 3. What is already done (2026-11-15)

- [x] QZoneExport export completed locally; offline viewer works.
- [x] Converter written: `convert.py` (Python, BeautifulSoup + markdownify + PyYAML).
- [x] All 721 logs converted to Markdown in `site/source/_posts/`; 0 empty posts; 0 leftover junk markers.
- [x] Hexo site scaffolded and verified: `hexo generate` produces 1,221 files (721 post pages + archives + categories + index); homepage renders correctly.
- [x] Full package delivered to this folder (`qqblog-site/`): site source, generated `public/` output, `convert.py`, `images-manifest.txt` (the 5,582 referenced image filenames), `README.md`.
- [x] Temporary Netlify Drop preview deployed and verified, then expired after 1 hour (anonymous deploys cannot be claimed after expiry).

---

## 4. Remaining steps to go live on GitHub Pages

### Step 1 — Confirm GitHub username (decision needed)

The site `_config.yml` currently sets `url: https://yanzhuwen.github.io`, but the username is **not verified**. Confirm the GitHub username before creating the repo.

### Step 2 — Create the repo and push the source

1. Create a GitHub repo (e.g. `qqblog`; public, since GitHub Pages on a free plan serves public repos).
2. Push the contents of `site/` (source only — no `node_modules`, no `public/`; those are generated).
3. Keep the repo as the single source of truth: all future edits (new posts, title changes) go through it.

### Step 3 — Enable GitHub Pages with Actions (recommended deploy method)

1. Repo → Settings → Pages → Build and deployment → Source: **GitHub Actions**.
2. Add a Hexo workflow (`.github/workflows/pages.yml`) that runs on every push to the default branch: checkout → setup Node 20+ → `npm install` → `npx hexo clean && npx hexo generate` → upload `public/` as a Pages artifact → deploy.
3. First deploy takes a few minutes; the site appears at `https://<username>.github.io/qqblog/` (or `https://<username>.github.io/` if the repo is named `<username>.github.io`).

Alternative (simpler, no Actions): install `hexo-deployer-git`, set `deploy` in `_config.yml` to the repo URL/branch, and run `npx hexo deploy`. It pushes the generated `public/` to a deploy branch that Pages serves.

### Step 4 — Site identity (does not block launch; change any time)

- Blog title: currently placeholder `我的QQ空间日志` (`_config.yml` → `title`).
- Author: currently Hexo default `John Doe` (`_config.yml` → `author`).
- Site URL: set `url` to the real Pages address after Step 3.

### Step 5 — Images: Cloudflare R2 image host (separate track)

Images are **not** published yet, by instruction ("先不发图片"). When ready:

1. Create a free Cloudflare account → R2 → create a bucket (e.g. `qqzone-images`).
2. Upload `Blogs/images/` (5,582 files, ~2–4 GB) from the Mac — dashboard folder drag-drop, or `rclone copy` (resumable, recommended for this size).
3. Enable public access: an `r2.dev` public URL for testing, or a custom domain on Cloudflare DNS for production.
4. Batch-replace the image prefix in all posts: `/images/qzone/` → `https://<r2-public-domain>/`, then `npx hexo clean && npx hexo generate` and redeploy.
5. Cost check: R2 free tier is 10 GB storage, 1M Class A ops, 10M Class B ops per month, egress free — this blog fits in the free tier.

Until Step 5 is done, photo posts will show broken image slots; text renders normally.

---

## 5. Ongoing maintenance

| Task | How |
|---|---|
| Add a new log | Re-export with QZoneExport → re-run `convert.py` on the new `blogs.json` → new `.md` files appear in `source/_posts/` → commit + push → Actions redeploys automatically |
| Edit a post | Edit its `.md` file, commit + push |
| Change title/author/theme | Edit `_config.yml` (site or theme), commit + push |
| Add a standalone page (e.g. About) | `npx hexo new page about`, write it, add it to the theme menu |
| Custom domain (optional) | Add the domain in Pages settings + a CNAME DNS record; free |
| Backup | The GitHub repo itself is the backup; the original QZoneExport folder stays on the Mac as the source archive |

Local preview at any time: `cd site && npm install && npx hexo server` → http://localhost:4000.

---

## 6. Decisions still open

1. **GitHub username** — confirm before Step 2 (config currently assumes `yanzhuwen`, unverified).
2. **Blog title and author name** — placeholder values in place; any name works.
3. **Image host timing** — images stay unpublished until the R2 step is done; no action needed now.
4. **Deploy method** — GitHub Actions (recommended) vs `hexo-deployer-git` (simpler).
