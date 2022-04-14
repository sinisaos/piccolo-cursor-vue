import typing as t

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from piccolo_admin.endpoints import create_admin
from piccolo_api.crud.serializers import create_pydantic_model
from piccolo_cursor_pagination.pagination import CursorPagination
from piccolo.engine import engine_finder
from starlette.routing import Route, Mount
from starlette.staticfiles import StaticFiles

from home.endpoints import HomeEndpoint
from home.piccolo_app import APP_CONFIG
from home.tables import Task


app = FastAPI(
    routes=[
        Route("/", HomeEndpoint),
        Mount(
            "/admin/",
            create_admin(
                tables=APP_CONFIG.table_classes,
                # Required when running under HTTPS:
                # allowed_hosts=['my_site.com']
            ),
        ),
        Mount("/static/", StaticFiles(directory="static")),
    ],
)


TaskModelIn: t.Any = create_pydantic_model(
    table=Task, model_name="TaskModelIn"
)
TaskModelOut: t.Any = create_pydantic_model(
    table=Task, include_default_columns=True, model_name="TaskModelOut"
)

origins = [
    "http://localhost:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=[
        "next_cursor",
        "first_row",
        "last_row",
    ],
)

# if we use ascending order
@app.get("/tasks/", response_model=t.List[TaskModelOut])
async def tasks(
    request: Request,
    __cursor: t.Optional[str] = None,
    __previous: t.Optional[str] = None,
):
    first_row = await Task.select().limit(1).first().run()
    last_row = (
        await Task.select()
        .order_by(Task._meta.primary_key, ascending=False)
        .limit(1)
        .first()
        .run()
    )
    try:
        previous = request.query_params["__previous"]
        paginator = CursorPagination(
            cursor=__cursor, page_size=3, order_by="id"
        )
        rows_result, headers_result = await paginator.get_cursor_rows(
            Task, request
        )
        rows = await rows_result.run()
        headers = headers_result
        response = JSONResponse(
            {"rows": rows[::-1]},
            headers={
                "next_cursor": headers["cursor"],
                "first_row": str(first_row["id"]),
                "last_row": str(last_row["id"]),
            },
        )
    except KeyError:
        paginator = CursorPagination(
            cursor=__cursor, page_size=3, order_by="id"
        )
        rows_result, headers_result = await paginator.get_cursor_rows(
            Task, request
        )
        rows = await rows_result.run()
        headers = headers_result
        response = JSONResponse(
            {"rows": rows},
            headers={
                "next_cursor": headers["cursor"],
                "first_row": str(first_row["id"]),
                "last_row": str(last_row["id"]),
            },
        )
    return response


# if we use descending order
# @app.get("/tasks/", response_model=t.List[TaskModelOut])
# async def tasks(
#     request: Request,
#     __cursor: t.Optional[str] = None,
#     __previous: t.Optional[str] = None,
# ):
#     first_row = await Task.select().limit(1).first().run()
#     last_row = (
#         await Task.select()
#         .order_by(Task._meta.primary_key, ascending=False)
#         .limit(1)
#         .first()
#         .run()
#     )
#     try:
#         previous = request.query_params["__previous"]
#         paginator = CursorPagination(cursor=__cursor, page_size=3)
#         rows_result, headers_result = await paginator.get_cursor_rows(
#             Task, request
#         )
#         rows = await rows_result.run()
#         headers = headers_result
#         response = JSONResponse(
#             {"rows": rows[::-1]},
#             headers={
#                 "next_cursor": headers["cursor"],
#                 "first_row": str(last_row["id"]),
#                 "last_row": str(first_row["id"]),
#             },
#         )
#     except KeyError:
#         paginator = CursorPagination(cursor=__cursor, page_size=3)
#         rows_result, headers_result = await paginator.get_cursor_rows(
#             Task, request
#         )
#         rows = await rows_result.run()
#         headers = headers_result
#         response = JSONResponse(
#             {"rows": rows},
#             headers={
#                 "next_cursor": headers["cursor"],
#                 "first_row": str(last_row["id"]),
#                 "last_row": str(first_row["id"]),
#             },
#         )
#     return response


@app.post("/tasks/", response_model=TaskModelOut)
async def create_task(task_model: TaskModelIn):
    task = Task(**task_model.dict())
    await task.save()
    return task.to_dict()


@app.put("/tasks/{task_id}/", response_model=TaskModelOut)
async def update_task(task_id: int, task_model: TaskModelIn):
    task = await Task.objects().get(Task.id == task_id)
    if not task:
        return JSONResponse({}, status_code=404)

    for key, value in task_model.dict().items():
        setattr(task, key, value)

    await task.save()

    return task.to_dict()


@app.delete("/tasks/{task_id}/")
async def delete_task(task_id: int):
    task = await Task.objects().get(Task.id == task_id)
    if not task:
        return JSONResponse({}, status_code=404)

    await task.remove()

    return JSONResponse({})


@app.on_event("startup")
async def open_database_connection_pool():
    try:
        engine = engine_finder()
        await engine.start_connection_pool(max_size=9)
    except Exception:
        print("Unable to connect to the database")


@app.on_event("shutdown")
async def close_database_connection_pool():
    try:
        engine = engine_finder()
        await engine.close_connection_pool()
    except Exception:
        print("Unable to connect to the database")
