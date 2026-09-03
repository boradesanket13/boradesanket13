import html
import re
import urllib.request
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime

HASHNODE_HOST = "boradesanket13.hashnode.dev" 
POST_COUNT = 4
BRIEF_MAX_CHARS = 140
THUMB_WIDTH = 110
START_MARKER = "<!-- HASHNODE:START -->"
END_MARKER = "<!-- HASHNODE:END -->"

RSS_URL = f"https://{HASHNODE_HOST}/rss.xml"
CONTENT_NS = "{http://purl.org/rss/1.0/modules/content/}"


def fetch_rss():
    req = urllib.request.Request(
        RSS_URL,
        headers={"User-Agent": "Mozilla/5.0 (compatible; readme-updater-bot/1.0)"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read()


def first_image_url(html_fragment):
    if not html_fragment:
        return None
    match = re.search(r'<img[^>]+src="([^"]+)"', html_fragment)
    return match.group(1) if match else None


def format_date(pub_date):
    try:
        return parsedate_to_datetime(pub_date).strftime("%b %d, %Y")
    except (TypeError, ValueError):
        return pub_date


def truncate(text, max_chars):
    text = text.strip()
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rsplit(" ", 1)[0].rstrip(",.") + "…"


def parse_posts(xml_bytes):
    root = ET.fromstring(xml_bytes)
    items = root.findall("./channel/item")[:POST_COUNT]

    posts = []
    for item in items:
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        pub_date = (item.findtext("pubDate") or "").strip()
        description = html.unescape((item.findtext("description") or "").strip())
        content_encoded = item.findtext(f"{CONTENT_NS}encoded") or ""
        brief = re.sub(r"<[^>]+>", "", description).strip()

        posts.append({
            "title": title,
            "link": link,
            "pub_date": format_date(pub_date),
            "brief": truncate(brief, BRIEF_MAX_CHARS),
            "cover_url": first_image_url(content_encoded) or first_image_url(description),
        })

    return posts


def build_block(posts):
    lines = ["### 📝 Latest Blog Posts\n", "<table>"]

    for post in posts:
        lines.append("  <tr>")

        if post["cover_url"]:
            lines.append(
                f'    <td width="{THUMB_WIDTH + 20}">'
                f'<a href="{post["link"]}"><img src="{post["cover_url"]}" width="{THUMB_WIDTH}" style="border-radius:6px;"/></a>'
                f"</td>"
            )
        else:
            lines.append(f'    <td width="{THUMB_WIDTH + 20}"></td>')

        cell = (
            f'      <a href="{post["link"]}"><b>{post["title"]}</b></a><br/>\n'
            f'      {post["brief"]}<br/>\n'
            f'      <sub>{post["pub_date"]}</sub>'
        )
        lines.append("    <td>")
        lines.append(cell)
        lines.append("    </td>")
        lines.append("  </tr>")

    lines.append("</table>")
    return "\n".join(lines)


def inject_into_readme(block):
    with open("README.md", "r", encoding="utf-8") as f:
        readme = f.read()

    replacement = f"{START_MARKER}\n{block}\n{END_MARKER}"
    pattern = re.compile(
        re.escape(START_MARKER) + ".*?" + re.escape(END_MARKER),
        re.DOTALL,
    )

    if pattern.search(readme):
        readme = pattern.sub(replacement, readme)
    else:
        readme = readme.rstrip() + "\n\n" + replacement + "\n"

    with open("README.md", "w", encoding="utf-8") as f:
        f.write(readme)


def main():
    xml_bytes = fetch_rss()
    posts = parse_posts(xml_bytes)
    block = build_block(posts)
    inject_into_readme(block)


if __name__ == "__main__":
    main()
