name: Update README with Hashnode Blogs

on:
  schedule:
    - cron: '30 * * * *'   # daily at 03:00 UTC
  workflow_dispatch: {}

permissions:
  contents: write

jobs:
  update-readme:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repo
        uses: actions/checkout@v4

      - name: Fetch Hashnode data
        run: |
          curl -s -X POST https://gql.hashnode.com \
            -H "Content-Type: application/json" \
            -d '{
              "query": "query { publication(host: \"boradesanket13.hashnode.dev\") { followersCount posts(first: 4) { edges { node { title brief slug url publishedAt coverImage { url } } } } } }"
            }' \
            -o hashnode.json

      - name: Build markdown block
        run: |
          python3 << 'EOF'
          import json

          with open("hashnode.json") as f:
              data = json.load(f)["data"]["publication"]

          followers = data["followersCount"]
          posts = [e["node"] for e in data["posts"]["edges"]]

          lines = []
          lines.append(f"### ✍️ Latest Blog Posts ({followers} followers on Hashnode)\n")

          for p in posts:
              date = p["publishedAt"][:10]
              cover = p.get("coverImage", {}).get("url") if p.get("coverImage") else None
              lines.append(f"#### [{p['title']}]({p['url']})")
              if cover:
                  lines.append(f"<img src=\"{cover}\" width=\"400\"/>\n")
              lines.append(f"{p['brief']}")
              lines.append(f"*Published: {date}*\n")

          block = "\n".join(lines)

          with open("readme_block.md", "w") as f:
              f.write(block)
          EOF

      - name: Inject block into README
        run: |
          python3 << 'EOF'
          import re

          with open("README.md") as f:
              readme = f.read()

          with open("readme_block.md") as f:
              block = f.read()

          start = "<!-- HASHNODE:START -->"
          end = "<!-- HASHNODE:END -->"
          pattern = re.compile(f"{re.escape(start)}.*?{re.escape(end)}", re.DOTALL)
          replacement = f"{start}\n{block}\n{end}"

          if pattern.search(readme):
              readme = pattern.sub(replacement, readme)
          else:
              # Markers not found — append at the end
              readme = readme.rstrip() + "\n\n" + replacement + "\n"

          with open("README.md", "w") as f:
              f.write(readme)
          EOF

      - name: Commit and push if changed
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add README.md
          if git diff --cached --quiet; then
            echo "No changes to commit"
          else
            git commit -m "chore: update README with latest Hashnode blogs [skip ci]"
            git push
          fi
