__all__ = ("Concat", "concat_op")

import typing as T
from functools import partial

from ..disposable import CompositeDisposable
from ..abstract.observer import Observer
from ..abstract.disposable import Disposable, adispose
from ..abstract.observable import Observable, observe
from ..stream.single_stream import SingleStream

K = T.TypeVar("K")


class Concat(Observable[K]):
    """Observable that is the concatenation of multiple observables sources"""

    def __init__(self, first: Observable, second: Observable, *rest: Observable, **kwargs) -> None:
        """Concat constructor.

        Arguments:
            first: First observable to be concatenated.
            second: Second observable to be concatenated.
            rest: Optional observables to be concatenated.
            kwargs: Keyword parameters for super.

        """
        super().__init__(**kwargs)

        self._sources = (first, second) + rest

    def __observe__(self, observer: Observer[K, T.Any]) -> Disposable:
        sink = SingleStream()  # type: SingleStream[K]

        try:
            return CompositeDisposable(
                *map(lambda s: observe(s, sink), self._sources), observe(sink, observer)
            )
        except Exception as exc:
            # Dispose sink if there is a exception during observation set-up
            observer.loop.create_task(adispose(sink))
            raise exc


def concat_op(first: Observable[K]) -> T.Callable[[], Concat]:
    """Partial implementation of :class:`~.Concat` to be used with operator semantics.

    Returns:
        Partial implementation of Concat

    """
    return partial(Concat, first)
