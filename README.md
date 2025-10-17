## usage

```sh
# 構築
docker compose up
```

```sh
# env用意
# .envに保管しているものに書き換え。
cp .env.sample .env

# 実行
uv run litestar --app main:app run

# lint
uv run ruff check

# format
uv run ruff format

# test
uv run pytest
```

## 確認

```sh
curl -H "Authorization: Bearer xxxxxxxxxxx" http://localhost:8000/pcs
```

## endpoint

```sh
# swagger
http://localhost:8000/schema/swagger
```
