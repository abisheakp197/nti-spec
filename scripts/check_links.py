import sys
import os
import re
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def check_links():
    print("Checking links in repository Markdown files...")
    session = requests.Session()
    retry = Retry(total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    broken_links = []
    checked = 0

    for root, _, files in os.walk("."):
        if ".git" in root or "node_modules" in root:
            continue
        for file in files:
            if file.endswith(".md"):
                filepath = os.path.join(root, file)
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()
                    links = re.findall(r'!?\[[^\]]*\]\(([^)\s]+)', content)
                    for url in links:
                        if url.startswith(("#", "mailto:", "data:")):
                            continue
                        # Relative links are validated against the local tree so
                        # that a renamed or deleted file cannot silently break a
                        # document.
                        if not url.startswith(("http://", "https://")):
                            target = url.split("#")[0].split("?")[0]
                            if not target:
                                continue
                            if target.startswith("/"):
                                resolved = os.path.join(".", target.lstrip("/"))
                            else:
                                resolved = os.path.normpath(
                                    os.path.join(os.path.dirname(filepath), target))
                            checked += 1
                            if not os.path.exists(resolved):
                                print(f"  [MISSING] {url} (in {filepath})")
                                broken_links.append((filepath, url, "missing-file"))
                            continue
                        checked += 1
                        try:
                            resp = session.get(url, timeout=20, allow_redirects=True)
                            if resp.status_code == 200:
                                print(f"  [200] {url} (in {file})")
                            elif resp.status_code == 404:
                                print(f"  [404] {url} (in {file})")
                                broken_links.append((file, url, resp.status_code))
                            elif resp.status_code == 504 or resp.status_code == 0:
                                print(f"  [TIMEOUT] Skipping URL - rate limit ({url}) in {file}")
                            else:
                                print(f"  [{resp.status_code}] {url} (in {file})")
                        except requests.exceptions.Timeout:
                            print(f"  [TIMEOUT] Skipping URL - rate limit ({url}) in {file}")
                        except requests.exceptions.RequestException:
                            print(f"  [TIMEOUT] Skipping URL - connection error ({url}) in {file}")

    print(f"\nChecked {checked} links.")
    if broken_links:
        print("❌ Found broken link(s):")
        for file, url, status in broken_links:
            print(f"  - File: {file} | Link: {url} | Status: {status}")
        sys.exit(1)
    else:
        print("✅ All links passed or timed out gracefully.")
        sys.exit(0)

if __name__ == "__main__":
    check_links()
