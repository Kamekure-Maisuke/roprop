## usage

```sh
# 構築
docker compose up
```

```sh
# 実行
uv run uvicorn main:app --reload

# lint
uv run ruff check

# format
uv run ruff format

# test
uv run pytest
```

## endpoint

```sh
# redoc
http://localhost:8000/schema

# swagger
http://localhost:8000/schema/swagger
```
