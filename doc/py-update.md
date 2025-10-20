## python更新手順
- 更新用のブランチを切る。
- .python-versionを更新
- pyproject.tomlのrequires-pythonを更新
- 以下のコマンドを実行

```shell
# 環境再構築 & 全パッケージ最新化
uv sync --upgrade --reinstall
```

- testが通るか確認。

```shell
uv run pytest
```

- 通って色々テストしてOK。