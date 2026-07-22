import os
import sys
import tomllib

with open("pyproject.toml", "rb") as f:
    data = tomllib.load(f)

project_version = data.get("project", {}).get("version")

if not project_version:
    print("::error::Could not find [project.version] in pyproject.toml")
    sys.exit(1)

git_tag = os.environ.get("RELEASE_TAG", "")

if not git_tag:
    print("::error::RELEASE_TAG environment variable is not set")
    sys.exit(1)

# Clean "v" prefix if present (e.g., v1.2.3 -> 1.2.3)
cleaned_tag = git_tag.removeprefix("v")

print(f"Detected pyproject.toml version: {project_version}")
print(f"Detected Release Tag: {git_tag} (Normalized: {cleaned_tag})")

if project_version != cleaned_tag:
    print(
        f"::error::Version mismatch! pyproject.toml version ({project_version}) "
        f"does not match Release tag ({git_tag}). Aborting build."
    )
    sys.exit(1)

print("Success: Version and Tag match!")
