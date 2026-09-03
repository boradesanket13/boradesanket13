import html
import re
import urllib.request
import xml.etree.ElementTree as ET

HASHNODE_HOST = "boradesanket13.hashnode.dev"  
POST_COUNT = 4
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

        posts.append({
            "title": title,
            "link": link,
            "pub_date": pub_date,
            "brief": re.sub(r"<[^>]+>", "", description).strip(),
            "cover_url": first_image_url(content_encoded) or first_image_url(description),
        })

    return posts


def build_block(posts):
    lines = ["### Latest Blog Posts\n"]

    for post in posts:
        lines.append(f"#### [{post['title']}]({post['link']})")
        if post["cover_url"]:
            lines.append(f'<img src="{post["cover_url"]}" width="400"/>\n')
        if post["brief"]:
            lines.append(post["brief"])
        if post["pub_date"]:
            lines.append(f"*Published: {post['pub_date']}*\n")

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
