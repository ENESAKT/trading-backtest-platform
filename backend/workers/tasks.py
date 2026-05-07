"""Worker task entry points."""


def healthcheck() -> dict[str, str]:
    return {"status": "ready"}
