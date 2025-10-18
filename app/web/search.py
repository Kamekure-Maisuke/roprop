from cachetools import TTLCache
from litestar import Request, Router, get
from litestar.response import Template

from app.auth import session_auth_guard
from models import BlogPostTable as B, EmployeeTable as E, PCTable as P

search_cache = TTLCache(maxsize=1000, ttl=300)


@get("/search/view")
async def view_search(request: Request, q: str = "") -> Template:
    results = []
    if query := q.strip():
        # クエリ正規化してキャッシュチェック
        cache_key = query.lower()
        if cache_key not in search_cache:
            cached_results = []

            # PC検索
            for pc in await P.raw(
                "SELECT * FROM pcs WHERE ARRAY[name, model, serial_number] &@~ {}",
                query,
            ):
                cached_results.append(
                    {
                        "type": "pc",
                        "id": str(pc["id"]),
                        "title": f"PC: {pc['name']}",
                        "description": f"{pc['model']} ({pc['serial_number']})",
                        "link": f"/pcs/{pc['id']}/show",
                    }
                )

            # 社員検索
            for emp in await E.raw(
                "SELECT * FROM employees WHERE ARRAY[name, email] &@~ {}", query
            ):
                cached_results.append(
                    {
                        "type": "employee",
                        "id": str(emp["id"]),
                        "title": f"社員: {emp['name']}",
                        "description": emp["email"],
                        "link": f"/employees/{emp['id']}/show",
                    }
                )

            # ブログ検索
            for blog in await B.raw(
                "SELECT * FROM blog_posts WHERE ARRAY[title, content] &@~ {}", query
            ):
                cached_results.append(
                    {
                        "type": "blog",
                        "id": str(blog["id"]),
                        "title": f"ブログ: {blog['title']}",
                        "description": blog["content"][:100] + "..."
                        if len(blog["content"]) > 100
                        else blog["content"],
                        "link": f"/blogs/{blog['id']}/detail",
                    }
                )

            search_cache[cache_key] = cached_results

        results = search_cache[cache_key]

    return Template(
        "search.html",
        context={
            "query": q,
            "results": results,
            "user_id": request.state.user_id,
            "user_role": request.state.role.value,
        },
    )


search_web_router = Router(
    path="", route_handlers=[view_search], guards=[session_auth_guard]
)
