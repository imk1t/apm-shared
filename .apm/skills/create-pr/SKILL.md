---
name: create-pr
description: PR を作成する。変更のコミット後に使用する。
disable-model-invocation: true
argument-hint: '[base-branch (default: main)]'
---

# Pull Request 作成

ベースブランチ: `$ARGUMENTS` (指定がなければ `main`)

リポジトリの指示（`AGENTS.md`、`CLAUDE.md`、CONTRIBUTING等）がブランチ名、タイトル、本文、レビュー手順を定めていれば、それをこのSkillより優先する。

## 手順

### 0. レビューAgent確認

1. リポジトリの指示とReview Agent定義を確認し、変更内容に対応するReview AgentがあればPR作成前に起動する
2. Review Agentがなければ、その理由を作成報告に記録する
3. findingsはPR作成前に解消またはPR本文へ明記する

### 1. ブランチ確認

1. `git branch --show-current` で現在のブランチ名と依頼scopeを確認する
2. 既存sessionでブランチとscopeが判断できる場合は、その文脈を使って続行する。承認済み内容を再質問しない
3. ブランチが未作成、scopeと既存ブランチが矛盾、または対象が曖昧な場合だけ、リポジトリの命名規則（指定がなければ `<type>/<scope>/<説明>`）に沿う名前を提案して確認する

### 2. 事前確認

以下を並列で実行する:

- `git status` で未コミットの変更と対象diffを確認する。依頼scope内の変更は通常のPR作成作業として続行し、無関係差分または対象曖昧時だけ確認する
- `git log --oneline <base-branch>...HEAD` でベースブランチからの全コミットを確認する
- `git diff <base-branch>...HEAD` でベースブランチからの全差分を確認する

### 3. PR タイトル・本文の生成

リポジトリにPRテンプレートがあれば使用する。対応する実在Issueがある場合だけ、本文の関連Issue欄に Closes #<id> を記載する。

全コミットと差分を分析し、以下を生成する:

**タイトル**:

- 70文字以内
- Conventional Commits 形式: `<type>(<scope>): <説明>`（説明の言語はリポジトリの規約に従う）
- type/scope はブランチ名とコミットから推測する

**本文**（テンプレートがない場合）:

```markdown
## 概要

<!-- 変更内容を箇条書きで1-3点 -->

## テスト計画

<!-- 実行した検証と未実行の検証 -->
```

### 4. PR 作成

以下を順番に実行する:

1. リモートへ push する (`git push -u origin <current-branch>`)
2. `gh pr create` で PR を作成する。本文は一時ファイルを `--body-file` で渡す。`gh` が使えない環境ではGitHub MCP等の同等の手段を使う:

```bash
gh pr create --title "<タイトル>" --body-file <body-file>
```

3. 作成された PR の URL を表示する
