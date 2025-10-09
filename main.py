from pathlib import Path
from typing import Annotated
from uuid import UUID
from litestar import Litestar, get, post, put, delete
from litestar.contrib.jinja import JinjaTemplateEngine
from litestar.enums import RequestEncodingType
from litestar.exceptions import NotFoundException
from litestar.params import Body
from litestar.response import Template, Redirect
from litestar.status_codes import HTTP_201_CREATED, HTTP_204_NO_CONTENT
from litestar.template.config import TemplateConfig

from models import PC


# In-memory storage
pcs: dict[UUID, PC] = {}


@post("/pcs", status_code=HTTP_201_CREATED)
async def create_pc(data: PC) -> PC:
    """Create a new PC."""
    pcs[data.id] = data
    return data


@get("/pcs")
async def list_pcs() -> list[PC]:
    """Get all PCs."""
    return list(pcs.values())


@get("/pcs/{pc_id:uuid}")
async def get_pc(pc_id: UUID) -> PC:
    """Get a specific PC by ID."""
    if pc_id not in pcs:
        raise NotFoundException(detail=f"PC with ID {pc_id} not found")
    return pcs[pc_id]


@put("/pcs/{pc_id:uuid}")
async def update_pc(pc_id: UUID, data: PC) -> PC:
    """Update an existing PC."""
    if pc_id not in pcs:
        raise NotFoundException(detail=f"PC with ID {pc_id} not found")
    data.id = pc_id
    pcs[pc_id] = data
    return data


@delete("/pcs/{pc_id:uuid}", status_code=HTTP_204_NO_CONTENT)
async def delete_pc(pc_id: UUID) -> None:
    """Delete a PC."""
    if pc_id not in pcs:
        raise NotFoundException(detail=f"PC with ID {pc_id} not found")
    del pcs[pc_id]


@get("/pcs/view")
async def view_pcs() -> Template:
    """View all PCs in HTML."""
    return Template(template_name="pc_list.html", context={"pcs": list(pcs.values())})


@get("/pcs/register")
async def show_register_form() -> Template:
    """Show PC registration form."""
    return Template(template_name="pc_register.html", context={"success": False})


@post("/pcs/register")
async def register_pc(
    data: Annotated[dict[str, str], Body(media_type=RequestEncodingType.URL_ENCODED)],
) -> Template:
    """Register a new PC from form."""
    pc = PC(
        name=data["name"],
        model=data["model"],
        serial_number=data["serial_number"],
        assigned_to=data["assigned_to"],
    )
    pcs[pc.id] = pc
    return Template(template_name="pc_register.html", context={"success": True})


@get("/pcs/{pc_id:uuid}/edit")
async def show_edit_form(pc_id: UUID) -> Template:
    """Show PC edit form."""
    if pc_id not in pcs:
        raise NotFoundException(detail=f"PC with ID {pc_id} not found")
    return Template(template_name="pc_edit.html", context={"pc": pcs[pc_id]})


@post("/pcs/{pc_id:uuid}/edit")
async def edit_pc(
    pc_id: UUID,
    data: Annotated[dict[str, str], Body(media_type=RequestEncodingType.URL_ENCODED)],
) -> Redirect:
    """Update a PC from form."""
    if pc_id not in pcs:
        raise NotFoundException(detail=f"PC with ID {pc_id} not found")

    pc = PC(
        id=pc_id,
        name=data["name"],
        model=data["model"],
        serial_number=data["serial_number"],
        assigned_to=data["assigned_to"],
    )
    pcs[pc_id] = pc
    return Redirect(path="/pcs/view")


@post("/pcs/{pc_id:uuid}/delete")
async def delete_pc_form(pc_id: UUID) -> Redirect:
    """Delete a PC from form."""
    if pc_id not in pcs:
        raise NotFoundException(detail=f"PC with ID {pc_id} not found")
    del pcs[pc_id]
    return Redirect(path="/pcs/view")


def create_app() -> Litestar:
    return Litestar(
        route_handlers=[
            create_pc,
            list_pcs,
            get_pc,
            update_pc,
            delete_pc,
            view_pcs,
            show_register_form,
            register_pc,
            show_edit_form,
            edit_pc,
            delete_pc_form,
        ],
        template_config=TemplateConfig(
            directory=Path("templates"),
            engine=JinjaTemplateEngine,
        ),
    )


app = create_app()
