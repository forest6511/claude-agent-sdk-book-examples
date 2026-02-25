# Claude Agent SDK実践入門 — コードサンプル集

書籍「**Claude Agent SDK実践入門** — 自律型AIエージェントをPython/TypeScriptで構築する」の
サンプルコードリポジトリです。

## 動作確認環境

| 項目 | バージョン |
|------|-----------|
| Python | 3.11 以上 |
| claude-agent-sdk | 0.1.43 |
| anthropic | 0.45.0 以上 |
| anyio | 4.0.0 以上 |

> **Note**: SDK は活発に開発中です。動作確認バージョンは `requirements.txt` を参照してください。
> 新バージョンで動作しない場合は `pip install claude-agent-sdk==0.1.43` で固定してください。

## セットアップ

```bash
# 1. リポジトリをクローン
git clone https://github.com/forest6511/claude-agent-sdk-book-examples.git
cd claude-agent-sdk-book-examples

# 2. 仮想環境を作成（推奨）
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 3. 依存パッケージをインストール
pip install -r requirements.txt

# 4. APIキーを設定
cp .env.example .env
# .env ファイルを開き ANTHROPIC_API_KEY を設定

# 5. 動作確認
python -c "from claude_agent_sdk import query; print('OK')"
```

## APIキーについて

`.env` ファイルに Anthropic APIキーを設定してください:

```
ANTHROPIC_API_KEY=sk-ant-api03-...
```

**`.env` ファイルは `.gitignore` に含まれており、リポジトリには絶対にコミットされません。**

## ディレクトリ構成

```
.
├── ch01/   第1章: Claude Agent SDK とは何か
├── ch02/   第2章: 環境構築と最初のエージェント
├── ch03/   第3章: メッセージ処理とストリーミング
├── ch04/   第4章: カスタムツールと MCP サーバー
├── ch05/   第5章: Hooks によるエージェント制御
├── ch06/   第6章: セッション管理と会話の継続
├── ch07/   第7章: サブエージェントとマルチエージェント連携
├── ch08/   第8章: プロダクション事例に学ぶ設計パターン
├── ch09/   第9章: コスト最適化とセキュリティ
├── ch10/   第10章: Agent Skills・ACP・エコシステムの展望
├── requirements.txt
├── .env.example
└── .github/workflows/ci.yml
```

## 章別サンプル一覧

### 第1章: Claude Agent SDK とは何か
| ファイル | 内容 |
|---------|------|
| `ch01/01_messages_api_loop.py` | Messages API の生のループ実装（SDK が解決する課題） |
| `ch01/02_basic_agent.py` | `query()` で最初のエージェントを動かす |
| `ch01/03_session_continuation.py` | `ClaudeSDKClient` でセッションを継続する |

### 第2章: 環境構築と最初のエージェント
| ファイル | 内容 |
|---------|------|
| `ch02/01_hello_agent.py` | Hello World エージェント（カスタムツール付き） |
| `ch02/02_file_agent.py` | ファイル操作エージェント |
| `ch02/03_debug_agent.py` | ToolUseBlock でツール呼び出しをデバッグする |

### 第3章: メッセージ処理とストリーミング
| ファイル | 内容 |
|---------|------|
| `ch03/01_message_patterns.py` | 最終テキスト取得・ログ付き・エラー処理の3パターン |
| `ch03/02_multi_turn_conversation.py` | マルチターン会話（文脈を保持） |
| `ch03/03_session_persistence.py` | セッション履歴の JSON 永続化 |
| `ch03/04_session_branching.py` | セッションの並列分岐比較 |

### 第4章: カスタムツールと MCP サーバー
| ファイル | 内容 |
|---------|------|
| `ch04/01_mortgage_calculator.py` | `@tool` デコレーターで住宅ローン計算ツールを作る |
| `ch04/02_github_tool.py` | async httpx で GitHub API を呼ぶツール |
| `ch04/03_mcp_servers.py` | 外部 MCP サーバー（filesystem）を接続する |

### 第5章: Hooks によるエージェント制御
| ファイル | 内容 |
|---------|------|
| `ch05/01_hook_basics.py` | PreToolUse / PostToolUse / Stop Hook の基本 |
| `ch05/02_rbac_hook.py` | ロールベースアクセス制御（RBAC）Hook |
| `ch05/03_audit_log_hook.py` | 構造化監査ログ Hook |
| `ch05/04_llm_judge_stop_hook.py` | LLM-as-Judge Stop Hook（Spotify Honk パターン） |

### 第6章: セッション管理と会話の継続
| ファイル | 内容 |
|---------|------|
| `ch06/01_session_state.py` | セッション状態の外部管理（サマリー・決定事項・コスト） |
| `ch06/02_parallel_approaches.py` | 並列アプローチ比較 — Best-of-N パターン |
| `ch06/03_checkpoint_pattern.py` | チェックポイントパターン（中断・再開） |

### 第7章: サブエージェントとマルチエージェント連携
| ファイル | 内容 |
|---------|------|
| `ch07/01_agent_definition.py` | `AgentDefinition` で専門エージェントを定義する |
| `ch07/02_two_agent_harness.py` | 2エージェント・ハーネス（Initializer + Coding Agent） |
| `ch07/03_parallel_analysis.py` | 並列エージェント + Semaphore によるレートリミット対応 |
| `ch07/04_hierarchical_agents.py` | 階層型エージェント（Supervisor パターン） |

### 第8章: プロダクション事例に学ぶ設計パターン
| ファイル | 内容 |
|---------|------|
| `ch08/01_three_layer_verification.py` | 3層検証（決定論的 + LLM-as-Judge + Stop Hook） |
| `ch08/02_context_engineering.py` | コンテキストエンジニアリング（CLAUDE.md 注入） |
| `ch08/03_tool_discipline.py` | ツール制限の美学（最小権限の原則） |

### 第9章: コスト最適化とセキュリティ
| ファイル | 内容 |
|---------|------|
| `ch09/01_cost_tracking.py` | CostTracker + モデルルーティング（Haiku / Sonnet 使い分け） |
| `ch09/02_cost_strategies.py` | ツール出力制限 + Messages Batch API |
| `ch09/03_security_hooks.py` | プロンプトインジェクション対策 + パスガード Hook |

### 第10章: Agent Skills・ACP・エコシステムの展望
| ファイル | 内容 |
|---------|------|
| `ch10/01_slack_skill.py` | Agent Skills パターン — Slack 通知スキルの実装 |

## 実行例

```bash
# 基本的なエージェント（第2章）
python ch02/01_hello_agent.py

# 2エージェント・ハーネス（第7章）
python ch07/02_two_agent_harness.py

# コスト追跡（第9章）
python ch09/01_cost_tracking.py

# チェックポイントパターン（第6章）
python ch06/03_checkpoint_pattern.py design-email-system
python ch06/03_checkpoint_pattern.py design-email-system  # 再実行: 再開
```

## トラブルシューティング

### `ModuleNotFoundError: No module named 'claude_agent_sdk'`
```bash
pip install claude-agent-sdk==0.1.43
```

### `AuthenticationError: Invalid API key`
`.env` ファイルに正しい `ANTHROPIC_API_KEY` が設定されているか確認してください。

### `RuntimeError: anyio.run(main())` のようなエラー
`anyio.run(main)` と書いてください（`main()` ではなく `main`）。

## ライセンス

MIT License

## 関連リンク

- [Claude Agent SDK Python](https://github.com/anthropics/claude-agent-sdk-python)
- [Anthropic 公式ドキュメント](https://docs.anthropic.com)
