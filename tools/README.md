# QQ 空间日志 → Hexo 博客

转换完成时间：2026-11-15（美国时间）
数据源：`Documents/qqZone2026/QQ空间备份_36110494/Blogs/json/blogs.json`（QZoneExport 导出）

## 成果

- **721 篇日志**，2009 年 8 月 → 2026 年 6 月，全部转成 Markdown（`site/source/_posts/`）
- **534 篇带照片**，共引用 **5,582 张不重复图片**（清单见 `images-manifest.txt`）
- **44 篇老视频日志**（2010 年左右的优酷嵌入）已保留为优酷链接，正文不再是空的
- 正文里的 QQ 加载图、空白段、表情占位都已清理；日期按北京时间保留
- Hexo 站点已生成验证：Butterfly 主题，1,221 个文件，首页、归档、分类页都正常

## 包里有什么

- `site/` — Hexo 站点源码（文章、主题、配置；`public/` 是已生成好的静态网页，可直接部署）
- `convert.py` — 转换脚本（以后导出有新增日志，重新跑一遍即可）
- `images-manifest.txt` — 5,582 张被引用图片的文件名清单

## 还差两步才能上线

### 1. 图片：传到图床（必须做，否则文章里的照片打不开）

文章里的图片现在指向 `/images/qzone/xxx.jpeg`。5,582 张图大概 2–4 GB，
放不进 GitHub 仓库，推荐用 **Cloudflare R2（免费 10 GB，流量也免费）**：

1. 登录 Cloudflare → R2 → 建一个 bucket（比如 `qqzone-images`），打开公开访问
2. 把 Mac 上 `Documents/qqZone2026/QQ空间备份_36110494/Blogs/images/` 整个文件夹拖进去上传
3. 上传后，在 `site/source/_posts/` 里把图片前缀换成 R2 的公开地址，一行命令：
   `sed -i '' 's#/images/qzone#https://你的R2公开域名#g' site/source/_posts/*.md`
   然后重新生成：`npx hexo clean && npx hexo generate`

也可以先不传图、直接上线文字版，照片以后再补。

### 2. 网站：放到 GitHub Pages（免费）

1. 在 GitHub 建一个仓库（比如 `qqblog`），把 `site/` 的内容推上去
   （不需要推 `node_modules` 和 `public`，部署时会自动生成）
2. 用 GitHub Actions 自动部署：仓库设置 → Pages → Source 选 GitHub Actions，
   加一个 Hexo 的 workflow（网上有现成模板，搜 "hexo github actions"）
3. 访问地址就是 `https://你的用户名.github.io/qqblog/`

更简单的一次性办法：把 `site/public/` 文件夹直接拖到
[Netlify Drop](https://app.netlify.com/drop) 上，立刻得到一个网址（图片还是要先传图床）。

## 本地预览

```bash
cd site
npm install
npx hexo server        # 打开 http://localhost:4000
```

## 想改的名字

- 博客标题现在是占位用的「我的QQ空间日志」，在 `site/_config.yml` 里改 `title`
- 作者名现在是 Hexo 默认的 John Doe，在 `_config.yml` 里改 `author`
- 网址现在是 `https://yanzhuwen.github.io`，按实际部署地址改 `url`

## 没导的东西（以后想加再说）

- 说说、留言板、相册、视频（Videos 文件夹里有 41 个 mp4）这次没导，只导了日志
- 每篇的留言数记在了 front-matter 的 `comments_count` 里，留言正文没导
