import json
import os
import re
import subprocess
import tempfile

HASHNODE_HOST = "boradesanket13.hashnode.dev"  
POST_COUNT = 4
START_MARKER = "<!-- HASHNODE:START -->"
END_MARKER = "<!-- HASHNODE:END -->"
HASHNODE_PAT = os.environ.get("HASHNODE_PAT")  

QUERY = """
query GetPosts($host: String!, $first: Int!) {
  publication(host: $host) {
    followersCount
    posts(first: $first) {
      edges {
        node {
          title
          brief
          url
          publishedAt
          coverImage {
            url
          }
        }
      }
    }
  }
}
"""


def fetch_hashnode_data():
    body = json.dumps({
        "query": QUERY,
        "variables": {"host": HASHNODE_HOST, "first": POST_COUNT},
    })

    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        f.write(body)
        payload_path = f.name

    cmd = [
        "curl", "-sS", "-X", "POST",
        "https://gql.hashnode.com",
        "-H", "Content-Type: application/json",
        "-H", "Accept: application/json",
        "--data", f"@{payload_path}",
    ]
    if HASHNODE_PAT:
        cmd += ["-H", f"Authorization: {HASHNODE_PAT}"]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    os.unlink(payload_path)

    if result.returncode != 0:
        raise RuntimeError(f"curl failed (exit {result.returncode}): {result.stderr}")

    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        raise RuntimeError(f"Non-JSON response from Hashnode: {result.stdout[:500]}")

    if "errors" in data:
        raise RuntimeError(f"Hashnode API error: {data['errors']}")

    return data["data"]["publication"]


def build_block(publication):
    followers = publication["followersCount"]
    posts = [edge["node"] for edge in publication["posts"]["edges"]]

    lines = [f"### Latest Blog Posts ({followers} followers on Hashnode)\n"]

    for post in posts:
        date = post["publishedAt"][:10]
        cover = post.get("coverImage")
        cover_url = cover["url"] if cover else None

        lines.append(f"#### [{post['title']}]({post['url']})")
        if cover_url:
            lines.append(f'<img src="{cover_url}" width="400"/>\n')
        lines.append(post["brief"])
        lines.append(f"*Published: {date}*\n")

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
    publication = fetch_hashnode_data()
    block = build_block(publication)
    inject_into_readme(block)


if __name__ == "__main__":
    main()
