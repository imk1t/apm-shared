# apm-shared

複数のリポジトリで共通に使うエージェント設定（Skill、指示、エージェント定義など）を、[APM](https://microsoft.github.io/apm/)パッケージとして配布する。プロジェクト固有のSkillは各リポジトリの `.apm/skills/` に置く。

## Skills

| Skill | 用途 |
|---|---|
| `create-pr` | コミット済みの変更からPRを作成する（`/create-pr [base]` で明示起動） |
| `code-docs` | 関数・型・定数・moduleのドキュメントコメントを書く・直す（`/code-docs [対象]`、exportの追加・変更時に自動でも使われる） |
| `project-docs-sync` | 構成・コマンド・設定・検証方法の変更に合わせ、README・関連文書・参照を同期する |
| `code-hygiene` | 移動・置換・削除後に、不要になった旧実装・参照・依存と重複処理を整理する |

追加した2つのSkillは、該当する変更時に自動でも使われる。リポジトリ固有の正本・検証コマンド・公開APIの互換性方針を優先する。

## APM検証

CLIのversion、正本と生成Skill・lockの一致、frozen install、構文検証、利用側のpolicyによるauditを共通化している。生成済みSkillの改変はinstall前に検出し、検証中にlockが変わった場合も失敗する。

GitHub Actionsでは、利用側のcheckout後にこのリポジトリのcomposite actionを呼ぶ。以下のtagはリリース後に利用できる。

```yaml
steps:
  - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
  - uses: imk1t/apm-shared@v0.1.3
    with:
      targets: agent-skills,claude,codex
      policy: apm-policy.yml
```

共通ActionとスクリプトはGitのtagで配布し、APMのSkill展開には含めない。ローカル実行、入力項目、利用側の移行手順は[APM検証](docs/apm-verification.md)を参照する。policyの許可範囲とプロジェクト固有の検査は利用側で管理する。

## MCPサーバー

| 名前 | 用途 |
|---|---|
| `context7` | ライブラリ・フレームワークの最新文書を検索する（`@upstash/context7-mcp` をversion固定） |

`apm install` で利用側の `.mcp.json`（Claude Code）と `.codex/config.toml`（Codex）に追記される。利用側のAPM policyで `context7` と `stdio` を許可し、`self_defined` を拒否しない設定にする。

## 使い方

利用側の `apm.yml` でtagを固定して取り込む。

```yaml
dependencies:
  apm:
    - imk1t/apm-shared#v0.1.3
```

更新はこのリポジトリで変更してtagを打ち、利用側で参照tagを上げてlockを更新する。リポジトリ固有の規約は各リポジトリの `AGENTS.md` 等に書き、Skillはそれを優先して読む。

同名のローカル `project-docs-sync` / `code-hygiene` がある場合は、固有の規約を利用側の指示・仕様へ残してから共通版へ移行する。詳しくは[移行手順](docs/apm-verification.md#既存リポジトリからの移行)を参照する。

## 開発時の検証

APM CLI 0.33.0と、その依存のPyYAMLを使えるPython環境で実行する。

```bash
python -m unittest discover -s tests -v
python tests/integration_apm.py
apm install --target agent-skills,claude,codex
python scripts/verify_apm.py
```

このパッケージ自身のlockは初回のinstallで生成する。利用側では更新済みlockをGit管理し、通常の検証にはfrozen installを使う。
統合検証は一時ディレクトリ内のローカル依存を使い、同名Skillの移行、生成先のないcheckoutからの展開、改変の検出を実際のAPMで確認する。

## リリース

PRで `.apm/`、`apm.yml`、`action.yml`、`scripts/`、`apm-policy.yml` を変えたら、`apm.yml` の `version` を上げる（CIが既存tagとの重複を拒否する）。mainへのマージで `.github/workflows/release.yml` が `v<version>` のtagとGitHub Releaseを作る。
