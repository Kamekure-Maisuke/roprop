import os
from collections.abc import AsyncGenerator

import pytest
from unittest.mock import AsyncMock, patch
from piccolo.engine.sqlite import SQLiteEngine

# テスト環境であることを示す環境変数を設定（modelsインポート前に必要）
os.environ["TESTING"] = "1"

from models import (
    BlogLikeTable,
    BlogPostTable,
    BlogPostTagTable,
    ChatMessageTable,
    DepartmentTable,
    EmployeeTable,
    PCAssignmentHistoryTable,
    PCTable,
    TagTable,
)

# pytest-asyncioの設定
pytest_plugins = ("pytest_asyncio",)

# テスト用SQLiteエンジン（ファイルベース、テスト間で共有可能）
TEST_DB = SQLiteEngine(path="test.sqlite")


@pytest.fixture(autouse=True)
def mock_redis():
    """Redisをモック化（全テストで自動適用）"""
    mock = AsyncMock()
    mock.get.return_value = None
    mock.setex.return_value = None
    mock.delete.return_value = None
    with patch("app.cache.redis", mock):
        yield mock


@pytest.fixture(autouse=True)
def mock_slack():
    """Slack通知を無効化（全テストで自動適用）"""
    with patch("app.slack.SLACK_WEBHOOK_URL", ""):
        yield


@pytest.fixture(scope="function", autouse=True)
async def setup_test_db() -> AsyncGenerator[None, None]:
    """各テスト前にテーブル作成、テスト後にクリーンアップ"""
    tables = [
        DepartmentTable,
        EmployeeTable,
        PCTable,
        PCAssignmentHistoryTable,
        ChatMessageTable,
        BlogPostTable,
        TagTable,
        BlogPostTagTable,
        BlogLikeTable,
    ]

    # テーブルのDBエンジンをテスト用に切り替え
    for table in tables:
        table._meta._db = TEST_DB

    # テーブル作成
    for table in tables:
        await table.create_table(if_not_exists=True).run()

    yield

    # テーブル削除（クリーンアップ）
    for table in reversed(tables):
        await table.alter().drop_table(if_exists=True).run()
