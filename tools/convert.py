#!/usr/bin/env python3
"""Convert QZoneExport Blogs (blogs.json) into Hexo Markdown posts.

Reads blogs.json exported by QZoneExport (QQ空间导出助手).
Uses `custom_html` (the offline-viewer HTML with local image refs).
Cleans legacy QQ markup, converts to Markdown, rewrites image paths
to IMG_BASE/<filename>, writes one .md per post with YAML front-matter.

Usage:
    python convert.py blogs.json out_dir [--img-base /images/qzone]

Images referenced by custom_html but missing from the export's Blogs/images/
folder are handled as follows (looked up through the matching <img> in the
original `html` field, via data-idx): QQ emoticons point to QQ's still-live
emoticon server; anything else (empty-src placeholders, dead 2010-era
photo.qq.com links, Tencent Weibo badges) is dropped. Covers use the first
image that exists locally and is not a GIF.
"""
import json
import re
import sys
import datetime
from pathlib import Path

from bs4 import BeautifulSoup
from markdownify import markdownify as md
import yaml

JUNK_IMG_SRC = re.compile(
    r"(qzonestyle\.gtimg\.cn/aoi/img/icenter/loading\.gif"
    r"|res\.mail\.qq\.com/zh_CN/htmledition/images/spacer\.gif"
    r"|qzonestyle\.gtimg\.cn/qzone/em/e\d+\.gif"
    r"|/qzone/em/e\d+\.gif)$"
)
EMOTICON = re.compile(r"/qzone/em/(e\d+\.gif)")
EMOTICON_BASE = "https://qzonestyle.gtimg.cn/qzone/em"
LOCAL_IMG = re.compile(r"Blogs/images/([A-Za-z0-9_.\-]+\.(?:jpeg|jpg|png|gif|cgi))")


def original_srcs(orig_html: str) -> list[str]:
    """src/orgsrc of each <img> in the original `html`, in order (data-idx)."""
    out = []
    for img in BeautifulSoup(orig_html, "html.parser").find_all("img"):
        out.append(img.get("orgsrc") or img.get("src") or "")
    return out


def clean_html(html: str, img_base: str, images_dir: Path,
               orig: list[str]) -> str:
    soup = BeautifulSoup(html, "html.parser")

    # Preserve video embeds as links: old Youku Flash iframes are dead in
    # modern browsers, but the link keeps the reference.
    for iframe in soup.find_all("iframe"):
        src = iframe.get("src", "") or ""
        m = re.search(r"player\.youku\.com/player\.php/sid/([A-Za-z0-9=_-]+)",
                      src)
        if m:
            href = f"https://v.youku.com/v_show/id_{m.group(1)}.html"
            label = "▶ 原视频（优酷，可能已失效）"
        elif src:
            href = src if src.startswith("http") else "https:" + src
            label = "▶ 原视频"
        else:
            iframe.decompose()
            continue
        link = soup.new_tag("a", href=href)
        link.string = label
        p = soup.new_tag("p")
        p.append(link)
        iframe.replace_with(p)

    # Unwrap lightgallery links, keep the <img> inside.
    for a in soup.find_all("a", class_="lightgallery"):
        a.unwrap()

    for img in soup.find_all("img"):
        src = img.get("src", "") or ""
        # Drop loading/spacer/remote-emoticon gifs.
        if JUNK_IMG_SRC.search(src):
            img.decompose()
            continue
        m = LOCAL_IMG.search(src)
        if m and not (images_dir / m.group(1)).is_file():
            # Not in the export: recover emoticons, drop everything else.
            idx = img.get("data-idx")
            o = orig[int(idx)] if idx and idx.isdigit() and int(idx) < len(orig) else ""
            e = EMOTICON.search(o)
            if e:
                img["src"] = f"{EMOTICON_BASE}/{e.group(1)}"
            else:
                img.decompose()
                continue
        elif m:
            img["src"] = f"{img_base}/{m.group(1)}"
        else:
            # Remote image with no local copy: keep only if it is a real
            # photo host (qpic), otherwise drop.
            if "qpic.cn" in src:
                img["src"] = src
            else:
                img.decompose()
                continue
        # Strip noisy attributes, keep alt.
        for attr in ("orgsrc", "data-idx", "class", "width", "height",
                     "style", "eventslistuid"):
            img.attrs.pop(attr, None)

    # Drop links that only wrapped a removed image / are empty.
    for a in soup.find_all("a"):
        if not a.get_text(strip=True) and not a.find("img"):
            a.decompose()

    # Remove empty paragraphs (<p>&nbsp;</p>, <p><br></p>, whitespace-only).
    for p in soup.find_all("p"):
        text = p.get_text().replace("\xa0", "").strip()
        if not text and not p.find("img"):
            p.decompose()

    # Strip remaining style/class attributes (keep structure only).
    for tag in soup.find_all(True):
        for attr in ("class", "style", "id"):
            tag.attrs.pop(attr, None)

    return str(soup)


def to_markdown(cleaned: str) -> str:
    text = md(
        cleaned,
        heading_style="ATX",
        bullets="-",
        strong_em_symbol="*",
        strip=["script", "style"],
    )
    # Collapse runs of blank lines, trim trailing spaces.
    text = re.sub(r"[ \t]+$", "", text, flags=re.M)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip() + "\n"


def convert(blog: dict, img_base: str, images_dir: Path) -> tuple[str, dict]:
    title = (blog.get("title") or "无标题").strip()
    pubtime = blog.get("pubtime") or blog.get("pubTime") or 0
    # QQ Zone times are Beijing time; keep the original calendar date.
    dt = datetime.datetime.fromtimestamp(
        pubtime, tz=datetime.timezone(datetime.timedelta(hours=8))
    )
    date_str = dt.strftime("%Y-%m-%d %H:%M:%S")
    category = (blog.get("category") or "未分类").strip()
    blog_id = str(blog.get("blogId") or blog.get("blogid") or "")

    html = blog.get("custom_html") or blog.get("html") or ""
    orig = original_srcs(blog.get("html") or "")
    body_md = to_markdown(clean_html(html, img_base, images_dir, orig))

    images = sorted(f for f in set(LOCAL_IMG.findall(blog.get("custom_html") or ""))
                    if (images_dir / f).is_file())
    photos = [f for f in images if not f.endswith(".gif")]
    cover = f"{img_base}/{photos[0]}" if photos else None

    fm = {
        "title": title,
        "date": date_str,
        "categories": [category],
        "qzone_id": blog_id,
    }
    if cover:
        fm["cover"] = cover
    comment_num = blog.get("commentNum") or blog.get("replynum") or 0
    if comment_num:
        fm["comments_count"] = comment_num

    front = "---\n" + yaml.safe_dump(
        fm, allow_unicode=True, sort_keys=False
    ).strip() + "\n---\n\n"
    filename = f"{dt.strftime('%Y-%m-%d')}-{blog_id}.md"
    return filename, {"front": front, "body": body_md,
                      "images": images, "date": dt}


def main():
    src = Path(sys.argv[1])
    out_dir = Path(sys.argv[2])
    img_base = "/images/qzone"
    if "--img-base" in sys.argv:
        img_base = sys.argv[sys.argv.index("--img-base") + 1]
    # QZoneExport layout: Blogs/json/blogs.json next to Blogs/images/
    images_dir = src.resolve().parent.parent / "images"
    if "--images-dir" in sys.argv:
        images_dir = Path(sys.argv[sys.argv.index("--images-dir") + 1])
    out_dir.mkdir(parents=True, exist_ok=True)

    with open(src, encoding="utf-8") as f:
        blogs = json.load(f)

    stats = {"posts": 0, "with_images": 0, "images_total": 0,
             "empty_body": 0}
    all_images = set()
    for blog in blogs:
        filename, parts = convert(blog, img_base, images_dir)
        (out_dir / filename).write_text(parts["front"] + parts["body"],
                                        encoding="utf-8")
        stats["posts"] += 1
        if parts["images"]:
            stats["with_images"] += 1
            stats["images_total"] += len(parts["images"])
            all_images |= set(parts["images"])
        if not parts["body"].strip():
            stats["empty_body"] += 1

    print(json.dumps(
        {"posts": stats["posts"],
         "with_images": stats["with_images"],
         "image_refs": stats["images_total"],
         "unique_images": len(all_images),
         "empty_body": stats["empty_body"]},
        ensure_ascii=False, indent=2))
    # Write the referenced-image manifest for the upload step.
    (out_dir.parent / "images-manifest.txt").write_text(
        "\n".join(sorted(all_images)), encoding="utf-8")


if __name__ == "__main__":
    main()
