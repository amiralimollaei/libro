import asyncio
from collections.abc import Awaitable, Callable
from typing import Any


class DelayedTaskScheduler:
    def __init__(self):
        self._tasks: dict[str, asyncio.Task] = {}

    def debounce(
        self,
        delay: float,
        coro_factory: Callable[[], Awaitable[Any]],
        key: str,
    ) -> None:
        old_task = self._tasks.pop(key, None)
        if old_task is not None:
            old_task.cancel()

        async def runner():
            try:
                await asyncio.sleep(delay)
                await coro_factory()
            except asyncio.CancelledError:
                pass
            finally:
                self._tasks.pop(key, None)

        task = asyncio.create_task(runner())
        self._tasks[key] = task
