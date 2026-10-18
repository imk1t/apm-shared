#!/usr/bin/env python3
"""Verify consumer skills before and after frozen install without rewriting the lock."""

import argparse
import hashlib
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys

import yaml


TARGET_ROOTS = {
    "agent-skills": ".agents/skills",
    "claude": ".claude/skills",
    "codex": ".agents/skills",
}


def file_hash(contents):
    return "sha256:" + hashlib.sha256(contents).hexdigest()


def tree(path):
    """Return relative file hashes; reject symlinks instead of following them."""
    if path.is_symlink():
        raise ValueError(f"Skill path must not be a symlink: {path}")
    if not path.exists():
        return None
    if not path.is_dir():
        raise ValueError(f"Skill root must be a directory: {path}")
    found = {}
    for child in sorted(path.iterdir()):
        if child.is_symlink():
            raise ValueError(f"Skill path must not be a symlink: {child}")
        if child.is_dir():
            for name, digest in tree(child).items():
                found[f"{child.name}/{name}"] = digest
        elif child.is_file():
            found[child.name] = file_hash(child.read_bytes())
        else:
            raise ValueError(f"Unsupported skill entry: {child}")
    return found


def skill_hashes(mapping, roots):
    """Select locked skill files for the requested targets, validating their paths."""
    if not isinstance(mapping, dict):
        raise ValueError("Lockfile file hashes must be a mapping")
    selected = {}
    for name, digest in mapping.items():
        if not isinstance(name, str):
            raise ValueError("Lockfile paths must be strings")
        if not any(name.startswith(root + "/") for root in roots):
            continue
        path = PurePosixPath(name)
        if ".." in path.parts or "\\" in name or path.as_posix() != name:
            raise ValueError(f"Invalid locked skill path: {name}")
        if not isinstance(digest, str) or not re.fullmatch(r"sha256:[a-f0-9]{64}", digest):
            raise ValueError(f"Invalid locked skill hash: {name}")
        selected[name] = digest
    return selected


def expected_skills(project, lock, roots):
    source = tree(project / ".apm/skills") or {}
    local = {f"{root}/{name}": digest for root in roots for name, digest in source.items()}
    locked_local = skill_hashes(lock.get("local_deployed_file_hashes", {}), roots)
    if local != locked_local:
        changed = sorted(name for name in local.keys() | locked_local.keys()
                         if local.get(name) != locked_local.get(name))
        raise ValueError("Local skill source and lock hashes differ; run apm install: "
                         + ", ".join(changed))
    expected = dict(local)
    dependencies = lock.get("dependencies", [])
    if not isinstance(dependencies, list):
        raise ValueError("Lockfile dependencies must be a list")
    for dependency in dependencies:
        if not isinstance(dependency, dict):
            raise ValueError("Lockfile dependency must be a mapping")
        for name, digest in skill_hashes(dependency.get("deployed_file_hashes", {}), roots).items():
            if name in expected:
                raise ValueError(f"More than one skill owner: {name}")
            expected[name] = digest
    return expected


def check_generated(project, expected, roots, allow_missing):
    """Allow a fresh checkout, but never repair existing drift through install."""
    existing = False
    differences = []
    for root in roots:
        actual = tree(project / root)
        if actual is None:
            if not allow_missing and any(name.startswith(root + "/") for name in expected):
                differences.append(f"missing skill root: {root}")
            continue
        existing = True
        actual = {f"{root}/{name}": digest for name, digest in actual.items()}
        wanted = {name: digest for name, digest in expected.items() if name.startswith(root + "/")}
        for name in sorted(wanted.keys() | actual.keys()):
            if wanted.get(name) != actual.get(name):
                differences.append(f"missing, modified or unmanaged skill file: {name}")
    if differences:
        raise ValueError("\n".join(differences))
    return existing


def run_apm(project, *arguments):
    print("apm " + " ".join(arguments), flush=True)
    subprocess.run(["apm", *arguments], cwd=project, check=True)


def verify(args):
    project = args.project.resolve()
    targets = list(dict.fromkeys(item.strip() for item in args.targets.split(",")))
    if not targets or any(target not in TARGET_ROOTS for target in targets):
        raise ValueError("Targets must be a nonempty selection of agent-skills,claude,codex")
    roots = list(dict.fromkeys(TARGET_ROOTS[target] for target in targets))
    for directory in [".apm", *(root.split("/")[0] for root in roots)]:
        if (project / directory).is_symlink():
            raise ValueError(f"Skill parent must not be a symlink: {project / directory}")
    if not (project / args.policy).is_file():
        raise ValueError(f"Local policy not found: {project / args.policy}")
    version = subprocess.run(["apm", "--version"], cwd=project, check=True,
                             text=True, capture_output=True).stdout
    match = re.search(r"CLI version (\S+)", version)
    if not match or match.group(1) != args.apm_version:
        raise ValueError(f"APM CLI {args.apm_version} is required (found {version.strip()})")
    lock_path = project / "apm.lock.yaml"
    before = lock_path.read_bytes()
    lock = yaml.safe_load(before)
    if not isinstance(lock, dict) or str(lock.get("lockfile_version")) != "1":
        raise ValueError("Expected APM lockfile_version 1")
    expected = expected_skills(project, lock, roots)
    try:
        if check_generated(project, expected, roots, allow_missing=True):
            run_apm(project, "audit", "--ci", "--policy", args.policy)
        target_list = ",".join(targets)
        run_apm(project, "install", "--frozen", "--target", target_list)
        run_apm(project, "compile", "--validate", "--target", target_list)
        check_generated(project, expected, roots, allow_missing=False)
        run_apm(project, "audit", "--ci", "--policy", args.policy)
    finally:
        if not lock_path.is_file() or lock_path.read_bytes() != before:
            raise ValueError("apm.lock.yaml changed during verification; inspect the diff")
    print("APM skills, policy and lockfile verified.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, default=Path("."))
    parser.add_argument("--apm-version", default="0.33.0")
    parser.add_argument("--targets", default="agent-skills,claude,codex")
    parser.add_argument("--policy", default="apm-policy.yml")
    args = parser.parse_args()
    try:
        verify(args)
    except (ValueError, OSError, yaml.YAMLError, subprocess.CalledProcessError) as error:
        print(f"APM verification failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
