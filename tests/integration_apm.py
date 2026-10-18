"""Use real APM to migrate local skills to a shared dependency, entirely in /tmp."""

from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

import yaml


REPOSITORY = Path(__file__).resolve().parents[1]
ROOTS = (".agents/skills", ".claude/skills")
MAINTENANCE = ("project-docs-sync", "code-hygiene")


def run(project, *command, success=True):
    result = subprocess.run(command, cwd=project, text=True, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT)
    if (result.returncode == 0) != success:
        raise AssertionError(result.stdout)
    print(f"{'PASS' if success else 'EXPECTED FAILURE'}: {' '.join(command)}", flush=True)


def main():
    with tempfile.TemporaryDirectory(prefix="apm-shared-integration-") as directory:
        fixture = Path(directory)
        package = fixture / "shared"
        consumer = fixture / "consumer"
        package.mkdir()
        consumer.mkdir()
        manifest = yaml.safe_load((REPOSITORY / "apm.yml").read_text())
        old_manifest = dict(manifest, version="0.1.2")
        (package / "apm.yml").write_text(yaml.safe_dump(old_manifest))
        for name in ("create-pr", "code-docs"):
            shutil.copytree(REPOSITORY / ".apm/skills" / name, package / ".apm/skills" / name)
        for name in MAINTENANCE:
            # Model distinct project-specific predecessors with the same skill names.
            path = consumer / ".apm/skills" / name
            path.mkdir(parents=True)
            (path / "SKILL.md").write_text(
                f"---\nname: {name}\ndescription: Maintain this fixture project.\n---\nLocal version.\n")
        local = consumer / ".apm/skills/consumer-only"
        local.mkdir()
        (local / "SKILL.md").write_text(
            "---\nname: consumer-only\ndescription: Maintain the consumer fixture.\n---\n")
        consumer_manifest = dict(manifest, name="consumer-fixture", version="1.0.0")
        consumer_manifest["dependencies"] = dict(manifest["dependencies"], apm=[{"path": "../shared"}])
        (consumer / "apm.yml").write_text(yaml.safe_dump(consumer_manifest))
        policy = yaml.safe_load((REPOSITORY / "apm-policy.yml").read_text())
        # Local fixture dependencies have no Git ref; production policies stay unchanged.
        policy["dependencies"]["require_pinned_constraint"] = False
        (consumer / "apm-policy.yml").write_text(yaml.safe_dump(policy))
        handwritten = {"AGENTS.md": "# Consumer-specific rules\n", "CLAUDE.md": "@AGENTS.md\n"}
        for name, contents in handwritten.items():
            (consumer / name).write_text(contents)
        install = ("apm", "install", "--target", "agent-skills,claude,codex")
        run(consumer, *install)

        # Rebuild ownership from a clean lock/cache when moving local skills to a dependency.
        for name in MAINTENANCE:
            shutil.rmtree(consumer / ".apm/skills" / name)
            for root in ROOTS:
                shutil.rmtree(consumer / root / name)
        shutil.copy(consumer / "apm.lock.yaml", fixture / "before-migration.lock.yaml")
        (consumer / "apm.lock.yaml").unlink()
        shutil.rmtree(consumer / "apm_modules")
        (package / "apm.yml").write_text(yaml.safe_dump(manifest))
        for name in MAINTENANCE:
            shutil.copytree(REPOSITORY / ".apm/skills" / name, package / ".apm/skills" / name)
        run(consumer, *install)
        for root in ROOTS:
            for name in MAINTENANCE:
                assert (consumer / root / name / "SKILL.md").read_bytes() == (
                    REPOSITORY / ".apm/skills" / name / "SKILL.md").read_bytes()
            assert (consumer / root / "consumer-only/SKILL.md").is_file()
            shutil.rmtree(consumer / root)

        # A fresh checkout keeps the lock and handwritten files but has no generated skills.
        lock_before = (consumer / "apm.lock.yaml").read_bytes()
        verify = (sys.executable, str(REPOSITORY / "scripts/verify_apm.py"))
        run(consumer, *verify)
        assert (consumer / "apm.lock.yaml").read_bytes() == lock_before
        for name, contents in handwritten.items():
            assert (consumer / name).read_text() == contents

        path = consumer / ROOTS[0] / "code-hygiene/SKILL.md"
        path.write_text("hand-edited generated skill\n")
        run(consumer, *verify, success=False)
        assert path.read_text() == "hand-edited generated skill\n"
        assert (consumer / "apm.lock.yaml").read_bytes() == lock_before
        print("Migration, fresh install, policy, handwritten files and drift checks passed.")


if __name__ == "__main__":
    main()
