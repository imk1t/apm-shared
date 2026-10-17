# apm-shared

複数のリポジトリで共通に使うエージェント設定（Skill、指示、エージェント定義など）を、[APM](https://microsoft.github.io/apm/)パッケージとして配布する。プロジェクト固有のSkillは各リポジトリの `.apm/skills/` に置く。

## Skills

| Skill | 用途 |
|---|---|
| `create-pr` | コミット済みの変更からPRを作成する（`/create-pr [base]` で明示起動） |
| `code-docs` | 関数・型・定数・moduleのドキュメントコメントを書く・直す（`/code-docs [対象]`、exportの追加・変更時に自動でも使われる） |

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
    - imk1t/apm-shared#v0.1.2
```

更新はこのリポジトリで変更してtagを打ち、利用側で参照tagを上げてlockを更新する。リポジトリ固有の規約は各リポジトリの `AGENTS.md` 等に書き、Skillはそれを優先して読む。

## リリース

PRで `.apm/` か `apm.yml` を変えたら、`apm.yml` の `version` を上げる（CIが既存tagとの重複を拒否する）。mainへのマージで `.github/workflows/release.yml` が `v<version>` のtagとGitHub Releaseを作る。
