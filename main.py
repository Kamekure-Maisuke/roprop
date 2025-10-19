from pathlib import Path
from litestar import Litestar, Request
from litestar.contrib.jinja import JinjaTemplateEngine
from litestar.response import Redirect
from litestar.template.config import TemplateConfig
from litestar.openapi.config import OpenAPIConfig
from litestar.openapi.spec import Components, SecurityScheme

from litestar_granian import GranianPlugin

from app.api.auth import auth_router
from app.api.pcs import pc_api_router
from app.api.employees import employee_api_router
from app.api.departments import department_api_router
from app.api.chat import chat_api_router
from app.api.search import search_router
from app.api.tags import tag_api_router
from app.api.blog_likes import blog_like_api_router

from app.auth import SessionExpiredException
from app.web.auth import auth_web_router

from app.web.pcs import pc_web_router
from app.web.employees import employee_web_router
from app.web.departments import department_web_router
from app.web.dashboard import dashboard_web_router
from app.web.chat import chat_web_router
from app.web.blogs import blog_web_router
from app.web.search import search_web_router
from app.web.tags import tag_web_router


def session_expired_handler(request: Request, exc: SessionExpiredException) -> Redirect:
    """セッション切れ時にログインページへリダイレクト"""
    return Redirect(path="/auth/login")


def create_app() -> Litestar:
    return Litestar(
        plugins=[GranianPlugin()],
        route_handlers=[
            auth_router,
            auth_web_router,
            pc_api_router,
            employee_api_router,
            department_api_router,
            chat_api_router,
            search_router,
            tag_api_router,
            blog_like_api_router,
            pc_web_router,
            employee_web_router,
            department_web_router,
            dashboard_web_router,
            chat_web_router,
            blog_web_router,
            search_web_router,
            tag_web_router,
        ],
        exception_handlers={SessionExpiredException: session_expired_handler},
        template_config=TemplateConfig(
            directory=Path("templates"),
            engine=JinjaTemplateEngine,
        ),
        openapi_config=OpenAPIConfig(
            title="PC・社員・部署管理API",
            version="1.0.0",
            components=Components(
                security_schemes={
                    "BearerAuth": SecurityScheme(
                        type="http",
                        scheme="bearer",
                        bearer_format="JWT",
                        description="APIトークンを入力してください",
                    )
                }
            ),
        ),
    )


app = create_app()
