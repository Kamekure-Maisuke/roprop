from pathlib import Path
from litestar import Litestar
from litestar.contrib.jinja import JinjaTemplateEngine
from litestar.template.config import TemplateConfig
from litestar.openapi.config import OpenAPIConfig
from litestar.openapi.spec import Components, SecurityScheme

from app.api.pcs import pc_api_router
from app.api.employees import employee_api_router
from app.api.departments import department_api_router
from app.web.pcs import pc_web_router
from app.web.employees import employee_web_router
from app.web.departments import department_web_router
from app.web.dashboard import dashboard_web_router


def create_app() -> Litestar:
    return Litestar(
        route_handlers=[
            pc_api_router,
            employee_api_router,
            department_api_router,
            pc_web_router,
            employee_web_router,
            department_web_router,
            dashboard_web_router,
        ],
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
