from starlette.responses import JSONResponse


class BodyLimit:
    """Bound request bodies before multipart parsing, including chunked uploads."""

    def __init__(self, app, max_bytes):
        self.app, self.max_bytes = app, max_bytes

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or scope["method"] not in {"POST", "PUT"}:
            return await self.app(scope, receive, send)
        limit = (
            1024 * 1024 if scope["method"] == "PUT" else self.max_bytes + 1024 * 1024
        )
        headers = dict(scope.get("headers", []))
        try:
            length = int(headers.get(b"content-length", b"0"))
        except ValueError:
            length = limit + 1
        response = JSONResponse(
            {"detail": "The request body is too large."}, status_code=413
        )
        if length < 0 or length > limit:
            return await response(scope, receive, send)
        consumed, exceeded, responded = 0, False, False

        async def bounded_receive():
            nonlocal consumed, exceeded, responded
            message = await receive()
            consumed += len(message.get("body", b""))
            if consumed > limit:
                exceeded = True
                if not responded:
                    await response(scope, receive, send)
                    responded = True
                return {"type": "http.disconnect"}
            return message

        async def bounded_send(message):
            nonlocal responded
            if not exceeded:
                if message["type"] == "http.response.start":
                    responded = True
                await send(message)

        try:
            await self.app(scope, bounded_receive, bounded_send)
        except Exception:
            if not exceeded:
                raise
