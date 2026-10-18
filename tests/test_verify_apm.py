"""Exercise verification against an isolated consumer and a recording APM CLI."""

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

import yaml


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/verify_apm.py"
ROOTS = (".agents/skills", ".claude/skills")
FAKE_APM = r'''
import json, os, pathlib, shutil, sys
import yaml

args = sys.argv[1:]
with open("calls.jsonl", "a") as log:
    log.write(json.dumps(args) + "\n")
if args == ["--version"]:
    print("Agent Package Manager (APM) CLI version " + os.environ.get("FAKE_VERSION", "0.33.0"))
elif args[0] == "install":
    assert args[1] == "--frozen"
    targets = args[args.index("--target") + 1].split(",")
    roots = set(".claude/skills" if target == "claude" else ".agents/skills" for target in targets)
    for root in roots:
        pathlib.Path(root).mkdir(parents=True, exist_ok=True)
        for source in (pathlib.Path(".apm/skills"), pathlib.Path("dependency-fixture")):
            if source.exists():
                shutil.copytree(source, root, dirs_exist_ok=True)
    if os.environ.get("FAKE_MUTATE_LOCK"):
        with open("apm.lock.yaml", "a") as lock:
            lock.write("\n# changed\n")
    if os.environ.get("FAKE_BAD_INSTALL"):
        pathlib.Path(next(iter(roots)), "unmanaged.txt").write_text("unexpected")
elif args[0] == "compile":
    assert args[1] == "--validate"
elif args[0] == "audit":
    assert args[1:3] == ["--ci", "--policy"]
    assert pathlib.Path(args[3]).is_file()
    if os.environ.get("FAKE_AUDIT_FAILURE"):
        sys.exit(1)
else:
    sys.exit(2)
'''


class VerifyAPMTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.project = Path(self.temporary.name)
        executable = self.project / "bin/apm"
        executable.parent.mkdir()
        executable.write_text(f"#!{sys.executable}\n" + FAKE_APM)
        executable.chmod(0o755)
        self.env = dict(os.environ, PATH=str(executable.parent) + os.pathsep + os.environ["PATH"])
        self.source = self.project / ".apm/skills/local/SKILL.md"
        self.source.parent.mkdir(parents=True)
        self.source.write_text("---\nname: local\ndescription: Local fixture.\n---\n")
        self.dependency = self.project / "dependency-fixture/shared/SKILL.md"
        self.dependency.parent.mkdir(parents=True)
        self.dependency.write_text("---\nname: shared\ndescription: Shared fixture.\n---\n")
        self.lock = {"lockfile_version": "1", "dependencies": [{"deployed_file_hashes": {
            f"{root}/shared/SKILL.md": self.digest(self.dependency) for root in ROOTS
        }}], "local_deployed_file_hashes": {
            f"{root}/local/SKILL.md": self.digest(self.source) for root in ROOTS
        }}
        self.write_lock()
        (self.project / "apm.yml").write_text("name: fixture\n")
        (self.project / "apm-policy.yml").write_text("name: fixture-policy\n")

    @staticmethod
    def digest(path):
        return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()

    def write_lock(self):
        (self.project / "apm.lock.yaml").write_text(yaml.safe_dump(self.lock))

    def deploy(self):
        for root in ROOTS:
            shutil.copytree(self.source.parent.parent, self.project / root)
            shutil.copytree(self.dependency.parent.parent, self.project / root, dirs_exist_ok=True)

    def run_verify(self, *arguments, **env):
        return subprocess.run([sys.executable, str(SCRIPT), "--project", str(self.project), *arguments],
                              text=True, capture_output=True, env=dict(self.env, **env))

    def calls(self):
        return [json.loads(line) for line in (self.project / "calls.jsonl").read_text().splitlines()]

    def assert_preinstall_failure(self, result):
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertFalse(any(call[0] == "install" for call in self.calls()))

    def test_fresh_checkout_installs_then_checks_policy_and_preserves_lock(self):
        before = (self.project / "apm.lock.yaml").read_bytes()
        result = self.run_verify()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual([call[0] for call in self.calls()], ["--version", "install", "compile", "audit"])
        self.assertEqual((self.project / "apm.lock.yaml").read_bytes(), before)
        self.assertTrue((self.project / ROOTS[0] / "shared/SKILL.md").is_file())

    def test_existing_output_is_audited_before_install(self):
        self.deploy()
        result = self.run_verify()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual([call[0] for call in self.calls()],
                         ["--version", "audit", "install", "compile", "audit"])

    def test_modified_dependency_is_not_overwritten(self):
        self.deploy()
        path = self.project / ROOTS[0] / "shared/SKILL.md"
        path.write_text("hand edit")
        self.assert_preinstall_failure(self.run_verify())
        self.assertEqual(path.read_text(), "hand edit")

    def test_changed_source_requires_explicit_lock_update(self):
        self.source.write_text("changed source")
        self.assert_preinstall_failure(self.run_verify())

    def test_missing_file_inside_existing_root_is_drift(self):
        self.deploy()
        (self.project / ROOTS[0] / "local/SKILL.md").unlink()
        self.assert_preinstall_failure(self.run_verify())

    def test_deleted_local_skill_is_detected(self):
        shutil.rmtree(self.source.parent)
        self.assert_preinstall_failure(self.run_verify())

    def test_unmanaged_file_is_detected(self):
        self.deploy()
        (self.project / ROOTS[0] / "extra.txt").write_text("unmanaged")
        self.assert_preinstall_failure(self.run_verify())

    def test_symlink_in_output_is_rejected(self):
        self.deploy()
        (self.project / ROOTS[0] / "linked").symlink_to(self.dependency.parent)
        self.assert_preinstall_failure(self.run_verify())

    def test_symlinked_parent_is_rejected_before_apm_runs(self):
        (self.project / ".agents").symlink_to(self.project / "dependency-fixture")
        result = self.run_verify()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("symlink", result.stderr)
        self.assertFalse((self.project / "calls.jsonl").exists())

    def test_lock_mutation_during_install_fails(self):
        result = self.run_verify(FAKE_MUTATE_LOCK="1")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("changed during verification", result.stderr)

    def test_unexpected_output_from_install_fails(self):
        result = self.run_verify(FAKE_BAD_INSTALL="1")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unmanaged", result.stderr)

    def test_policy_failure_before_install_is_propagated(self):
        self.deploy()
        self.assert_preinstall_failure(self.run_verify(FAKE_AUDIT_FAILURE="1"))

    def test_wrong_cli_version_fails_before_install(self):
        self.assert_preinstall_failure(self.run_verify(FAKE_VERSION="0.32.0"))

    def test_dependency_only_project_needs_no_local_skill_directory(self):
        shutil.rmtree(self.source.parent.parent)
        del self.lock["local_deployed_file_hashes"]
        self.write_lock()
        result = self.run_verify()
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_claude_only_does_not_require_agents_output(self):
        self.lock["local_deployed_file_hashes"] = {
            name: digest for name, digest in self.lock["local_deployed_file_hashes"].items()
            if name.startswith(".claude/")
        }
        dependency = self.lock["dependencies"][0]
        dependency["deployed_file_hashes"] = {
            name: digest for name, digest in dependency["deployed_file_hashes"].items()
            if name.startswith(".claude/")
        }
        self.write_lock()
        result = self.run_verify("--targets", "claude")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse((self.project / ".agents").exists())

    def test_duplicate_ownership_fails(self):
        self.lock["dependencies"][0]["deployed_file_hashes"].update(self.lock["local_deployed_file_hashes"])
        self.write_lock()
        self.assert_preinstall_failure(self.run_verify())

    def test_path_traversal_in_lock_is_rejected(self):
        self.lock["dependencies"][0]["deployed_file_hashes"][".agents/skills/../outside"] = self.digest(self.source)
        self.write_lock()
        self.assert_preinstall_failure(self.run_verify())


if __name__ == "__main__":
    unittest.main()
