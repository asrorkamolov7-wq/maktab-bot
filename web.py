"""Render uchun mini veb-server (health-check)."""
from __future__ import annotations

from aiohttp import web


async def _ping(_: web.Request) -> web.Response:
    return web.Response(text="OK")


async def start_web_server(port: int) -> web.AppRunner:
    app = web.Application()
    app.router.add_get("/", _ping)
    app.router.add_get("/health", _ping)
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, "0.0.0.0", port).start()
    return runner
