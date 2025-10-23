from dataclasses import dataclass
from typing import Literal
from uuid import UUID

from litestar import Router, get
from litestar.datastructures import State

from models import (
    BlogPostTable as B,
)
from models import (
    EmployeeTable as E,
)
from models import (
    PCTable as P,
)


@dataclass
class SearchResult:
    type: Literal["pc", "employee", "blog"]
    id: UUID
    title: str
    description: str


@get("/search")
async def search(state: State, q: str = "") -> list[SearchResult]:
    if not (query := q.strip()):
        return []

    results = []

    # PC検索
    for pc in await P.raw(
        "SELECT * FROM pcs WHERE ARRAY[name, model, serial_number] &@~ {}", query
    ):
        results.append(
            SearchResult(
                type="pc",
                id=pc["id"],
                title=f"PC: {pc['name']}",
                description=f"{pc['model']} ({pc['serial_number']})",
            )
        )

    # 社員検索
    for emp in await E.raw(
        "SELECT * FROM employees WHERE ARRAY[name, email] &@~ {}", query
    ):
        results.append(
            SearchResult(
                type="employee",
                id=emp["id"],
                title=f"社員: {emp['name']}",
                description=emp["email"],
            )
        )

    # ブログ検索
    for blog in await B.raw(
        "SELECT * FROM blog_posts WHERE ARRAY[title, content] &@~ {}", query
    ):
        results.append(
            SearchResult(
                type="blog",
                id=blog["id"],
                title=f"ブログ: {blog['title']}",
                description=blog["content"][:100] + "..."
                if len(blog["content"]) > 100
                else blog["content"],
            )
        )

    return results


search_router = Router(path="/api", route_handlers=[search])
