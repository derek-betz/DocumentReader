#!/usr/bin/env python3
"""
Script to check for updates to ML models used in Roadway-Doc-Engine.

This script checks various sources for new versions of:
- LayoutLMv3 and related models
- PaddleOCR
- Tesseract OCR
- LayoutParser models
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple
import requests
from packaging import version as pkg_version


def check_pypi_package(package_name: str, current_version: str = None) -> Tuple[bool, str, str]:
    """
    Check PyPI for the latest version of a package.
    
    Returns:
        Tuple of (has_update, latest_version, release_date)
    """
    try:
        response = requests.get(f"https://pypi.org/pypi/{package_name}/json", timeout=10)
        response.raise_for_status()
        data = response.json()
        
        latest_version = data['info']['version']
        releases = data['releases']
        
        if latest_version in releases and releases[latest_version]:
            release_date = releases[latest_version][0]['upload_time']
        else:
            release_date = 'Unknown'
        
        has_update = False
        if current_version:
            try:
                has_update = pkg_version.parse(latest_version) > pkg_version.parse(current_version)
            except Exception:
                has_update = latest_version != current_version
        
        return has_update, latest_version, release_date
    
    except Exception as e:
        print(f"Error checking {package_name}: {e}", file=sys.stderr)
        return False, "Unknown", "Unknown"


def check_huggingface_model(model_id: str) -> Tuple[bool, str]:
    """
    Check Hugging Face for model updates.
    
    Returns:
        Tuple of (success, last_modified)
    """
    try:
        response = requests.get(
            f"https://huggingface.co/api/models/{model_id}",
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        
        last_modified = data.get('lastModified', 'Unknown')
        return True, last_modified
    
    except Exception as e:
        print(f"Error checking Hugging Face model {model_id}: {e}", file=sys.stderr)
        return False, "Unknown"


def check_github_releases(repo: str, current_version: str = None) -> Tuple[bool, str, str]:
    """
    Check GitHub releases for the latest version.
    
    Args:
        repo: Format "owner/repo"
        current_version: Current version to compare against
    
    Returns:
        Tuple of (has_update, latest_version, release_date)
    """
    try:
        response = requests.get(
            f"https://api.github.com/repos/{repo}/releases/latest",
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        
        latest_version = data['tag_name'].lstrip('v')
        release_date = data['published_at']
        
        has_update = False
        if current_version:
            try:
                has_update = pkg_version.parse(latest_version) > pkg_version.parse(current_version)
            except Exception:
                has_update = latest_version != current_version
        
        return has_update, latest_version, release_date
    
    except Exception as e:
        print(f"Error checking GitHub repo {repo}: {e}", file=sys.stderr)
        return False, "Unknown", "Unknown"


def main():
    """Main function to check for model updates."""
    
    print("Checking for ML model updates...")
    
    updates = []
    
    # Check PaddleOCR
    print("Checking PaddleOCR...")
    has_update, version, date = check_pypi_package("paddleocr", "2.6.0")
    if has_update:
        updates.append(f"- **PaddleOCR**: New version `{version}` available (released: {date[:10]})")
    
    # Check PaddlePaddle
    print("Checking PaddlePaddle...")
    has_update, version, date = check_pypi_package("paddlepaddle", "2.4.0")
    if has_update:
        updates.append(f"- **PaddlePaddle**: New version `{version}` available (released: {date[:10]})")
    
    # Check LayoutParser
    print("Checking LayoutParser...")
    has_update, version, date = check_pypi_package("layoutparser", "0.3.4")
    if has_update:
        updates.append(f"- **LayoutParser**: New version `{version}` available (released: {date[:10]})")
    
    # Check OpenAI Python SDK
    print("Checking OpenAI SDK...")
    has_update, version, date = check_pypi_package("openai", "1.0.0")
    if has_update:
        updates.append(f"- **OpenAI SDK**: New version `{version}` available (released: {date[:10]})")
    
    # Check Anthropic SDK
    print("Checking Anthropic SDK...")
    has_update, version, date = check_pypi_package("anthropic", "0.7.0")
    if has_update:
        updates.append(f"- **Anthropic SDK**: New version `{version}` available (released: {date[:10]})")
    
    # Check PyTesseract
    print("Checking PyTesseract...")
    has_update, version, date = check_pypi_package("pytesseract", "0.3.10")
    if has_update:
        updates.append(f"- **PyTesseract**: New version `{version}` available (released: {date[:10]})")
    
    # Check LayoutLMv3 on Hugging Face
    print("Checking LayoutLMv3...")
    success, last_modified = check_huggingface_model("microsoft/layoutlmv3-base")
    if success and last_modified != "Unknown":
        # Check if modified in last 7 days
        from datetime import datetime, timedelta
        try:
            mod_date = datetime.fromisoformat(last_modified.replace('Z', '+00:00'))
            if datetime.now(mod_date.tzinfo) - mod_date < timedelta(days=7):
                updates.append(f"- **LayoutLMv3**: Model updated recently on Hugging Face (last modified: {last_modified[:10]})")
        except Exception:
            pass
    
    # Write results
    updates_found = len(updates) > 0
    
    if updates_found:
        print(f"\n✓ Found {len(updates)} update(s)")
        
        # Write updates to file for GitHub Actions
        with open('model_updates.txt', 'w') as f:
            f.write('\n'.join(updates))
        
        # Set output for GitHub Actions
        if 'GITHUB_OUTPUT' in os.environ:
            with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
                f.write('updates_found=true\n')
        
        # Print updates
        print("\nUpdates found:")
        for update in updates:
            print(update)
    else:
        print("\n✓ All models are up to date")
        
        if 'GITHUB_OUTPUT' in os.environ:
            with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
                f.write('updates_found=false\n')
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
