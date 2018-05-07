# Internal
import typing as T

from asyncio import gather
from functools import partial

# Project
from ...stream import SingleStream
from ...abstract import Observer, Observable, Disposable
from ...observable import observe
from ...disposable import CompositeDisposable

K = T.TypeVar("K")


class Concat(Observable):
    """Observable that is the concatenation of multiple observables"""

    class Sink(SingleStream):
        async def __aclose__(self) -> None:
            self._logger.debug("Concat._:close()")
            self.cancel()

    @staticmethod
    def _sinking(sink: "Concat.Sink",
                 observable: Observable) -> T.Awaitable[Disposable]:
        return observe(observable, sink)

    def __init__(self, *sources: Observable, **kwargs) -> None:
        """Concat constructor.

        Args:
            sources: Observables to be concatenated
            kwargs: BaseObservable superclass named parameters
        """
        super().__init__(**kwargs)

        self._sources_iterator = iter(sources)

    async def __aobserve__(self, observer: Observer[K]) -> Disposable:
        sink = Concat.Sink()

        observations = (
            list(map(partial(self._sinking, sink), self._sources_iterator)) +
            [observe(sink, observer)]
        )

        return CompositeDisposable(
            *(await gather(observations, loop=observer.loop))
        )


def concat(*operators: Observable) -> Observable:
    """Concatenate multiple source streams.

    Returns:
        Concatenated source stream.
    """
    return Concat(*operators)
