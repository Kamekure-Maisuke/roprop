from dataclasses import dataclass
from typing import Literal
from uuid import UUID

from litestar import Router, get
from litestar.datastructures import State

from models import (
    BlogPostTable as B,
    EmployeeTable as E,
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
    if not q.strip():
        return []

    results = []

    # PC検索
    pcs = await P.raw(
        "SELECT * FROM pcs WHERE ARRAY[name, model, serial_number] &@~ {}",
        q,
    )
    for pc in pcs:
        results.append(
            SearchResult(
                type="pc",
                id=pc["id"],
                title=f"PC: {pc['name']}",
                description=f"{pc['model']} ({pc['serial_number']})",
            )
        )

    # 社員検索
    employees = await E.raw(
        "SELECT * FROM employees WHERE ARRAY[name, email] &@~ {}", q
    )
    for emp in employees:
        results.append(
            SearchResult(
                type="employee",
                id=emp["id"],
                title=f"社員: {emp['name']}",
                description=emp["email"],
            )
        )

    # ブログ検索
    blogs = await B.raw(
        "SELECT * FROM blog_posts WHERE ARRAY[title, content] &@~ {}", q
    )
    for blog in blogs:
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
