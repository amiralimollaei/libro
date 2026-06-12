import asyncio
from collections.abc import Awaitable, Callable
from typing import Any


class DelayedTaskScheduler:
    _instances: list["DelayedTaskScheduler"] = []

    def __init__(self):
        self._tasks: dict[str, tuple[asyncio.Task, Callable[[], Awaitable[Any]]]] = {}
        DelayedTaskScheduler._instances.append(self)

    def debounce(
        self,
        delay: float,
        coro_factory: Callable[[], Awaitable[Any]],
        key: str,
    ) -> None:
        old_entry = self._tasks.pop(key, None)
        if old_entry is not None:
            old_entry[0].cancel()

        async def runner():
            this_task = asyncio.current_task()
            try:
                await asyncio.sleep(delay)
                await coro_factory()
            except asyncio.CancelledError:
                pass
            finally:
                # only remove if our entry is still the current one
                current = self._tasks.get(key)
                if current is not None and current[0] is this_task:
                    self._tasks.pop(key, None)

        task = asyncio.create_task(runner())
        self._tasks[key] = (task, coro_factory)

    async def flush(self, key: str) -> None:
        """
        Cancel the pending delayed task for `key` and execute it immediately.
        If no task is registered for `key`, this does nothing.
        """
        entry = self._tasks.pop(key, None)
        if entry is None:
            return
        task, factory = entry
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
        try:
            await factory()
        except Exception:
            pass

    @classmethod
    async def flush_all(cls):
        """
        Cancel all pending delayed tasks and run them immediately.
        Called before the app closes so no events are lost.
        """

        for instance in cls._instances:
            for key in list(instance._tasks.keys()):
                await instance.flush(key)
