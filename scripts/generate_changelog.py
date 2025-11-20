"""
Generate changelog from git commits.
Used in release workflow to create release notes.
"""
import subprocess
import re
import sys
from datetime import datetime
from typing import List, Dict, Tuple, Optional
from collections import defaultdict


# Commit type mapping for conventional commits
COMMIT_TYPES = {
    'feat': '✨ Features',
    'fix': '🐛 Bug Fixes',
    'docs': '📝 Documentation',
    'style': '💅 Style Changes',
    'refactor': '♻️ Code Refactoring',
    'perf': '⚡ Performance Improvements',
    'test': '✅ Tests',
    'build': '👷 Build System',
    'ci': '🚀 CI/CD',
    'chore': '🔧 Chores',
    'revert': '⏪ Reverts',
    'security': '🔒 Security',
    'breaking': '💥 BREAKING CHANGES'
}


def get_latest_tag() -> Optional[str]:
    """Get the most recent tag."""
    try:
        result = subprocess.run(
            ['git', 'describe', '--tags', '--abbrev=0'],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        # No tags found
        return None


def get_commits_since_tag(tag: Optional[str]) -> List[str]:
    """Get all commits since the specified tag (or all commits if no tag)."""
    if tag:
        cmd = ['git', 'log', f'{tag}..HEAD', '--pretty=format:%H|%s|%b|%an|%ae|%ai']
    else:
        cmd = ['git', 'log', '--pretty=format:%H|%s|%b|%an|%ae|%ai']
    
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    
    commits = []
    for line in result.stdout.strip().split('\n'):
        if line:
            commits.append(line)
    
    return commits


def parse_commit(commit_line: str) -> Dict[str, str]:
    """Parse a commit line into its components."""
    parts = commit_line.split('|', 5)
    if len(parts) < 6:
        return None
    
    commit_hash, subject, body, author_name, author_email, date = parts
    
    # Parse conventional commit format
    match = re.match(r'^(\w+)(?:\(([^)]+)\))?\s*:\s*(.+)$', subject)
    
    if match:
        commit_type = match.group(1)
        scope = match.group(2) or ''
        description = match.group(3)
    else:
        # Non-conventional commit
        commit_type = 'other'
        scope = ''
        description = subject
    
    # Check for breaking changes
    is_breaking = False
    breaking_description = ''
    if 'BREAKING CHANGE' in body or 'BREAKING-CHANGE' in body:
        is_breaking = True
        breaking_match = re.search(r'BREAKING[\s-]CHANGE:\s*(.+)', body, re.IGNORECASE)
        if breaking_match:
            breaking_description = breaking_match.group(1).strip()
    
    return {
        'hash': commit_hash[:7],  # Short hash
        'type': commit_type,
        'scope': scope,
        'description': description,
        'body': body,
        'author_name': author_name,
        'author_email': author_email,
        'date': date,
        'is_breaking': is_breaking,
        'breaking_description': breaking_description
    }


def group_commits_by_type(commits: List[Dict]) -> Dict[str, List[Dict]]:
    """Group commits by their type."""
    grouped = defaultdict(list)
    
    for commit in commits:
        if commit:
            commit_type = commit['type']
            
            # Group breaking changes separately
            if commit['is_breaking']:
                grouped['breaking'].append(commit)
            
            # Map to known types or 'other'
            if commit_type in COMMIT_TYPES:
                grouped[commit_type].append(commit)
            else:
                grouped['other'].append(commit)
    
    return grouped


def get_contributors(commits: List[Dict]) -> List[Tuple[str, str]]:
    """Get unique contributors from commits."""
    contributors = {}
    
    for commit in commits:
        if commit:
            email = commit['author_email']
            name = commit['author_name']
            contributors[email] = name
    
    # Sort by name
    return sorted(contributors.items(), key=lambda x: x[1].lower())


def format_commit(commit: Dict) -> str:
    """Format a single commit for the changelog."""
    scope = f"**{commit['scope']}**: " if commit['scope'] else ""
    author = f" ({commit['author_name']})" if commit.get('show_author') else ""
    
    # Add PR link if found in description
    pr_match = re.search(r'#(\d+)', commit['description'])
    pr_link = f" ([#{pr_match.group(1)}](#{pr_match.group(1)}))" if pr_match else ""
    
    return f"- {scope}{commit['description']}{pr_link}{author}"


def generate_changelog(since_tag: Optional[str] = None) -> str:
    """Generate the changelog."""
    # Get commits
    commits_raw = get_commits_since_tag(since_tag)
    
    if not commits_raw:
        return "No changes found."
    
    # Parse commits
    commits = [parse_commit(commit) for commit in commits_raw]
    commits = [c for c in commits if c]  # Filter out None values
    
    if not commits:
        return "No conventional commits found."
    
    # Group commits
    grouped_commits = group_commits_by_type(commits)
    
    # Get contributors
    contributors = get_contributors(commits)
    
    # Build changelog
    changelog = []
    
    # Breaking changes first
    if 'breaking' in grouped_commits:
        changelog.append(f"### {COMMIT_TYPES.get('breaking', 'Breaking Changes')}\n")
        for commit in grouped_commits['breaking']:
            changelog.append(format_commit(commit))
            if commit['breaking_description']:
                changelog.append(f"  \n  {commit['breaking_description']}")
        changelog.append("")
    
    # Then features and fixes
    priority_types = ['feat', 'fix', 'security']
    for commit_type in priority_types:
        if commit_type in grouped_commits:
            changelog.append(f"### {COMMIT_TYPES[commit_type]}\n")
            for commit in grouped_commits[commit_type]:
                changelog.append(format_commit(commit))
            changelog.append("")
    
    # Then other types
    other_types = [t for t in COMMIT_TYPES.keys() 
                   if t not in priority_types + ['breaking'] and t in grouped_commits]
    
    for commit_type in sorted(other_types):
        if grouped_commits[commit_type]:
            changelog.append(f"### {COMMIT_TYPES[commit_type]}\n")
            for commit in grouped_commits[commit_type]:
                changelog.append(format_commit(commit))
            changelog.append("")
    
    # Other commits
    if 'other' in grouped_commits and grouped_commits['other']:
        changelog.append("### 🔄 Other Changes\n")
        for commit in grouped_commits['other']:
            changelog.append(format_commit(commit))
        changelog.append("")
    
    # Statistics
    changelog.append("### 📊 Statistics\n")
    changelog.append(f"- Total commits: {len(commits)}")
    changelog.append(f"- Contributors: {len(contributors)}")
    changelog.append("")
    
    # Contributors section
    if contributors:
        changelog.append("### 👥 Contributors\n")
        changelog.append("Thanks to all contributors for this release!\n")
        for email, name in contributors:
            # Try to create GitHub link from email
            if 'users.noreply.github.com' in email:
                username = email.split('@')[0].split('+')[-1]
                changelog.append(f"- [{name}](https://github.com/{username})")
            else:
                changelog.append(f"- {name}")
        changelog.append("")
    
    return '\n'.join(changelog)


def main():
    """Main function."""
    # Check if we're in a git repository
    try:
        subprocess.run(['git', 'rev-parse', '--git-dir'], 
                      capture_output=True, check=True)
    except subprocess.CalledProcessError:
        print("Error: Not in a git repository", file=sys.stderr)
        sys.exit(1)
    
    # Get the latest tag
    latest_tag = get_latest_tag()
    
    if latest_tag:
        print(f"# Changes since {latest_tag}\n", file=sys.stderr)
    else:
        print("# All Changes\n", file=sys.stderr)
    
    # Generate and print changelog
    changelog = generate_changelog(latest_tag)
    print(changelog)


if __name__ == "__main__":
    main()
