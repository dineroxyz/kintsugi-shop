"""Kintsugi regression test, compiled from incident live_M05.

Reproduction signature: TypeError@main.py:62
Provoking request: GET /price/WIDGET/converted

Auto-generated; the embedded capture is the evidence. Do not edit by hand.
"""

import json

CAPTURE = json.loads(r'''{"service": "beta", "release": "r2", "exception_type": "TypeError", "exception_message": "unsupported operand type(s) for *: 'float' and 'NoneType'", "frames": [{"file": "/Users/ssheyii/kintsugi/libs/kintsugi_capture/__init__.py", "line": 158, "function": "__call__", "code": "await self.app(scope, buffering_receive, send)"}, {"file": "/Users/ssheyii/kintsugi/.venv/lib/python3.12/site-packages/starlette/middleware/exceptions.py", "line": 63, "function": "__call__", "code": "await wrap_app_handling_exceptions(self.app, conn)(scope, receive, send)"}, {"file": "/Users/ssheyii/kintsugi/.venv/lib/python3.12/site-packages/starlette/_exception_handler.py", "line": 53, "function": "wrapped_app", "code": "raise exc"}, {"file": "/Users/ssheyii/kintsugi/.venv/lib/python3.12/site-packages/starlette/_exception_handler.py", "line": 42, "function": "wrapped_app", "code": "await app(scope, receive, sender)"}, {"file": "/Users/ssheyii/kintsugi/.venv/lib/python3.12/site-packages/fastapi/middleware/asyncexitstack.py", "line": 18, "function": "__call__", "code": "await self.app(scope, receive, send)"}, {"file": "/Users/ssheyii/kintsugi/.venv/lib/python3.12/site-packages/starlette/routing.py", "line": 670, "function": "__call__", "code": "await self.middleware_stack(scope, receive, send)"}, {"file": "/Users/ssheyii/kintsugi/.venv/lib/python3.12/site-packages/fastapi/routing.py", "line": 2734, "function": "app", "code": "await route.handle(scope, receive, send)"}, {"file": "/Users/ssheyii/kintsugi/.venv/lib/python3.12/site-packages/fastapi/routing.py", "line": 1281, "function": "handle", "code": "await super().handle(scope, receive, send)"}, {"file": "/Users/ssheyii/kintsugi/.venv/lib/python3.12/site-packages/starlette/routing.py", "line": 280, "function": "handle", "code": "await self.app(scope, receive, send)"}, {"file": "/Users/ssheyii/kintsugi/.venv/lib/python3.12/site-packages/fastapi/routing.py", "line": 158, "function": "app", "code": "await wrap_app_handling_exceptions(app, request)(scope, receive, send)"}, {"file": "/Users/ssheyii/kintsugi/.venv/lib/python3.12/site-packages/starlette/_exception_handler.py", "line": 53, "function": "wrapped_app", "code": "raise exc"}, {"file": "/Users/ssheyii/kintsugi/.venv/lib/python3.12/site-packages/starlette/_exception_handler.py", "line": 42, "function": "wrapped_app", "code": "await app(scope, receive, sender)"}, {"file": "/Users/ssheyii/kintsugi/.venv/lib/python3.12/site-packages/fastapi/routing.py", "line": 144, "function": "app", "code": "response = await f(request)"}, {"file": "/Users/ssheyii/kintsugi/.venv/lib/python3.12/site-packages/fastapi/routing.py", "line": 706, "function": "app", "code": "raw_response = await run_endpoint_function("}, {"file": "/Users/ssheyii/kintsugi/.venv/lib/python3.12/site-packages/fastapi/routing.py", "line": 354, "function": "run_endpoint_function", "code": "return await run_in_threadpool(dependant.call, **values)"}, {"file": "/Users/ssheyii/kintsugi/.venv/lib/python3.12/site-packages/starlette/concurrency.py", "line": 34, "function": "run_in_threadpool", "code": "return await anyio.to_thread.run_sync(func)"}, {"file": "/Users/ssheyii/kintsugi/.venv/lib/python3.12/site-packages/anyio/to_thread.py", "line": 65, "function": "run_sync", "code": "return await get_async_backend().run_sync_in_worker_thread("}, {"file": "/Users/ssheyii/kintsugi/.venv/lib/python3.12/site-packages/anyio/_backends/_asyncio.py", "line": 2641, "function": "run_sync_in_worker_thread", "code": "return await future"}, {"file": "/Users/ssheyii/kintsugi/.venv/lib/python3.12/site-packages/anyio/_backends/_asyncio.py", "line": 1033, "function": "run", "code": "result = context.run(func, *args)"}, {"file": "/private/var/folders/mv/mzz_q2mn3q3c827r6pfcby640000gn/T/kintsugi-live-ggmku3_n/live_beta/beta/main.py", "line": 62, "function": "converted_price", "code": "\"price\": round(PRICES[sku] * rate, 2)}"}], "request": {"method": "GET", "path": "/price/WIDGET/converted", "query": "currency=GBP", "headers": {"host": "127.0.0.1:51720", "accept": "*/*", "accept-encoding": "gzip, deflate, br", "connection": "keep-alive", "user-agent": "python-httpx/0.28.1"}, "body": ""}, "external_calls": []}''')
SERVICE_SPEC = 'beta.main:app'
SIGNATURE = 'TypeError@main.py:62'


def test_incident_live_M05_stays_fixed():
    from control_plane.reproduction.harness import replay

    verdict = replay(CAPTURE, SERVICE_SPEC)

    assert not verdict.get("hermetic_violation"), (
        "replay attempted an unrecorded outbound call: " + json.dumps(verdict))
    assert not verdict["failed"], (
        "incident live_M05 has recurred: "
        + str(verdict["exception_type"]) + " at " + str(verdict["top_frame"]))
