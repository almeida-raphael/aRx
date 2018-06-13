__all__ = ("Promise", )

# Internal
import typing as T

from asyncio import shield, ensure_future, AbstractEventLoop

# Project
from .abstract.promise import Promise as AbstractPromise

K = T.TypeVar("K")
L = T.TypeVar("L")


class Promise(AbstractPromise):
    """Concrete Promise implementation that maintains the callback queue using :class:`~typing.Coroutine`."""

    @staticmethod
    async def _rejection_wrapper(
        promise: T.Awaitable[K], on_reject: T.Callable[[Exception], T.Any],
        loop: AbstractEventLoop
    ) -> L:
        """Coroutine that wraps a promise and manages a rejection callback.

        Arguments:
            promise: Promise to be wrapped.
            on_reject: Rejection callback.
            loop: Asyncio loop reference.

        Returns:
            Callback result.

        """
        try:
            result = await shield(promise, loop=loop)
        except Exception as ex:
            result = on_reject(ex)

        try:
            result = await ensure_future(result, loop=loop)
        except TypeError:
            pass

        return result

    @staticmethod
    async def _resolution_wrapper(
        promise: T.Awaitable[K], on_resolution: T.Callable[[], T.Any],
        loop: AbstractEventLoop
    ) -> L:
        """Coroutine that wraps a promise and manages a resolution callback.

        Arguments:
            promise: Promise to be wrapped.
            on_resolution: Resolution callback.
            loop: Asyncio loop reference.

        Returns:
            Callback result.

        """
        try:
            await shield(promise, loop=loop)
        except Exception:
            pass

        result = on_resolution()

        try:
            result = await ensure_future(result, loop=loop)
        except TypeError:
            pass

        return result

    @staticmethod
    async def _fulfillment_wrapper(
        promise: T.Awaitable[K], on_fulfilled: T.Callable[[Exception], T.Any],
        loop: AbstractEventLoop
    ) -> L:
        """Coroutine that wraps a promise and manages a fulfillment callback.

        Arguments:
            promise: Promise to be wrapped.
            on_fulfilled: Fulfillment callback.
            loop: Asyncio loop reference.

        Returns:
            Callback result.

        """
        result = on_fulfilled(await shield(promise, loop=loop))

        try:
            result = await ensure_future(result, loop=loop)
        except TypeError:
            pass

        return result

    def then(self, on_fulfilled: T.Callable[[L], T.Any]) -> 'Promise':
        """See: :meth:`~aRx.abstract.promise.Promise.then`"""
        return Promise(
            Promise._fulfillment_wrapper(self, on_fulfilled, self._loop),
            loop=self._loop
        )

    def catch(self, on_reject: T.Callable[[Exception], T.Any]) -> 'Promise':
        """See: :meth:`~aRx.abstract.promise.Promise.catch`"""
        return Promise(
            Promise._rejection_wrapper(self, on_reject, self._loop),
            loop=self._loop
        )

    def lastly(self, on_fulfilled: T.Callable[[L], T.Any]) -> 'Promise':
        """See: :meth:`~aRx.abstract.promise.Promise.lastly`"""
        pass
