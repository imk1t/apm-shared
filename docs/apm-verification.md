# APM検証の利用

## 検証する内容

対象はAPM CLI 0.33.0のlockfile v1と、`.apm/skills/` を正本にするSkillである。`agent-skills` / `codex` は `.agents/skills/`、`claude` は `.claude/skills/` を検証する。これ以外のtargetや、Skillの選択的な展開・配置変更は現在の共通検証の対象外である。

1. 指定したCLIの版とローカルpolicyの存在を確認する。
2. ローカルSkillの正本とlockのhashを照合する。依存Skillはlockのhashを基準にする。同名Skillの所有者重複、symlink、管理外のファイルも検出する。
3. 生成済みのSkillはinstall前に照合し、既存の生成先があれば `apm audit --ci --policy <policy>` を実行する。新規checkoutで生成先がまだ存在しない場合はinstall後に検証する。既存の生成先に欠損や改変がある場合は、installで修復せず失敗する。
4. `apm install --frozen --target <targets>`、`apm compile --validate --target <targets>` を実行する。手書きの `AGENTS.md` / `CLAUDE.md` は再生成しない。
5. 展開後のSkillとpolicyを検証し、lockの内容が検証開始時から変わっていないことを確認する。

検証は生成先やMCP設定を展開するため、読み取り専用ではない。lockを更新する処理は含まない。失敗時は差分を調べ、必要な修正・通常の `apm install` による更新を行ってから再実行する。hashの手修正や検査の除外で合わせない。

## GitHub Actions

利用側でcheckoutし、更新済みの `apm.lock.yaml` とローカルpolicyをコミットしておく。

```yaml
name: APM
on: [pull_request, push]
permissions:
  contents: read
jobs:
  verify:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
      - uses: imk1t/apm-shared@v0.1.3
        with:
          working-directory: .
          apm-version: 0.33.0
          targets: agent-skills,claude,codex
          policy: apm-policy.yml
```

| 入力 | 既定値 | 内容 |
|---|---|---|
| `working-directory` | `.` | checkoutした利用側のディレクトリ |
| `apm-version` | `0.33.0` | インストールし、完全一致を確認するAPM CLIの版 |
| `targets` | `agent-skills,claude,codex` | 検証するtarget。3種類から必要なものだけをカンマ区切りで指定 |
| `policy` | `apm-policy.yml` | 利用側のディレクトリを基準にしたローカルpolicyのpath |

`targets` は利用側のmanifest・lockを生成した対象に合わせる。共通検証が走らせるauditはlock全体を検証するため、複数targetのlockを単一targetの検証で部分的に無視することはできない。

ActionはPython 3.12を用意し、その環境に指定版の `apm-cli` をインストールする。版を変える場合はlockの形式と生成先が対応していることを確認する。private依存の認証は利用側で準備する。固有のチェックはこのActionの前後に残す。

policyのpackage/MCP allowlist、targetの許可、独自ルールは利用側で維持する。このリポジトリの `apm-policy.yml` はパッケージ自身のCI用であり、利用側のpolicyを置き換えるものではない。

## ローカル実行

同じtagのapm-sharedを別途checkoutし、その `scripts/verify_apm.py` を利用側のディレクトリから実行する。スクリプトを利用側へ複製する必要はない。Actionと同じく、APM経由のSkill展開とは独立した配布物である。

```bash
# Python環境の準備は初回だけ行う
python3 -m venv .venv-apm
. .venv-apm/bin/activate
python -m pip install apm-cli==0.33.0

# /path/to/apm-sharedは、利用するtagをcheckoutした場所
python /path/to/apm-shared/scripts/verify_apm.py \
  --project . \
  --apm-version 0.33.0 \
  --targets agent-skills,claude,codex \
  --policy apm-policy.yml
```

利用側で検証専用venvを作る場合はGit管理の対象外にする。既存のPython環境で `apm` とPyYAMLが使えるなら、その環境でも実行できる。

## 既存リポジトリからの移行

`v0.1.3` のリリース後に、利用側で次を行う。

1. 同名のローカル `project-docs-sync` / `code-hygiene` があれば、取引仕様・デザイン規約・固定コマンド・互換性方針などを `AGENTS.md` や関連仕様の正本へ残す。固有の検査scriptやテストも維持する。
2. 同名Skillがある場合は、その正本と生成済みコピーの差分を確認し、独自の変更を失わないよう作業用ディレクトリへ退避する。旧 `apm.lock.yaml` と `apm_modules/` もプロジェクト外へ退避し、旧ローカルSkillの正本と各生成先の該当ディレクトリを取り除く。他のSkillとMCP設定は保持する。同名Skillがなければ、この退避・再生成は不要。
3. `apm.yml` の共通依存を `imk1t/apm-shared#v0.1.3` に更新し、`apm install --target agent-skills,claude,codex` でlockと展開先を生成する。ローカルSkillへの参照も利用側のSkill管理方針に合わせて更新する。
4. 新旧lockを比較し、共通依存以外の参照・解決済みcommitに意図しない変更がないことを確認する。異なる場合は理由を確認し、必要に応じて旧commitへ固定して再生成する。targetが異なる場合は利用側の指定に合わせ、利用側に固定したAPM CLIを使う。lockのhashは直接編集しない。
5. 既存のAPM検証処理を共通Actionまたは共通スクリプトの呼び出しへ置き換える。policy、固有の静的解析・文書検査、workflowの監視pathは利用側に合わせる。
6. 共通検証と固有の検査を実行し、manifest・lock・CI・指示の差分をレビューする。

APM 0.33.0では、ローカル版の削除と共通版への更新を通常のinstallだけで行うと、同じpathに旧所有情報が残り、次回のfrozen installで旧内容が復元される場合がある。同名Skillがある移行では、上記の退避・再生成を行う。この処理は所有者を切り替える移行時だけのもので、通常の検証ではlockを再生成しない。移行後の検証が通るまで退避物を保持する。

`project-docs-sync` は文書と参照の追従、`code-hygiene` は不要な実装や依存の整理を担当する。両方が関係する変更では併用する。API互換性や文書保存方針は利用側の契約に従う。
