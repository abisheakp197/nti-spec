#!/usr/bin/env python3
"""
Link Checker Script for NTI-1 Spec Repository
Checks all external HTTP/HTTPS URLs and relative local links in Markdown files.
Ensures every link returns HTTP 200 or points to an existing file/directory.
"""

import glob
import os
import re
import sys
import urllib.request
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent


def check_external_url(url: str) -> int:
    """Send request with appropriate headers to check external URL status code."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status
    except urllib.error.HTTPError as e:
        return e.code
    except Exception as e:
        print(f"    Request failed for {url}: {e}")
        return 0


def main() -> None:
    print("Checking links in repository Markdown files...")
    md_files = glob.glob(str(ROOT_DIR / "**" / "*.md"), recursive=True)

    failed_links = []
    total_checked = 0

    for md_file in md_files:
        rel_md = Path(md_file).relative_to(ROOT_DIR)
        with open(md_file, "r", encoding="utf-8") as f:
            content = f.read()

        # Find Markdown links: [text](link)
        markdown_links = re.findall(r"\[([^\]]+)\]\(([^)]+)\)", content)
        # Find bare URLs: https://...
        bare_urls = re.findall(r"(https?://[^\s\)\"\'>]+)", content)

        urls_to_check = set()
        local_links_to_check = set()

        for text, link in markdown_links:
            link = link.strip()
            if link.startswith("http://") or link.startswith("https://"):
                urls_to_check.add(link)
            elif not link.startswith("#"):  # Ignore pure anchor links
                # Strip anchor part if any
                link_path = link.split("#")[0]
                if link_path:
                    local_links_to_check.add((link_path, link))

        for url in bare_urls:
            urls_to_check.add(url.strip())

        # Check external URLs
        for url in sorted(urls_to_check):
            total_checked += 1
            status = check_external_url(url)
            print(f"  [{status}] {url} (in {rel_md})")
            if not (200 <= status < 300):
                failed_links.append((str(rel_md), url, status))

        # Check local links
        for link_path, original in sorted(local_links_to_check):
            total_checked += 1
            target_path = (Path(md_file).parent / link_path).resolve()
            if target_path.exists():
                print(f"  [200 OK (local)] {original} -> {target_path.relative_to(ROOT_DIR)} (in {rel_md})")
            else:
                print(f"  [404 Local Not Found] {original} -> {target_path} (in {rel_md})")
                failed_links.append((str(rel_md), original, 404))

    print(f"\nChecked {total_checked} links.")
    if failed_links:
        print(f"❌ Found {len(failed_links)} broken link(s):")
        for file, link, status in failed_links:
            print(f"  - File: {file} | Link: {link} | Status: {status}")
        sys.exit(1)
    else:
        print("✓ All links return HTTP 2xx / verified local files!")


if __name__ == "__main__":
    main()
