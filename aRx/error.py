__all__ = (
    "ARxError", "ObserverError", "ObserverClosedError", "SingleStreamError",
    "MultiStreamError", "ARxWarning", "DisposeWarning"
)

# Internal
import typing as T


class ARxError(Exception):
    """aRx base error class."""
    pass


class ObserverError(ARxError):
    """aRx error exclusive to observer."""
    pass


class ObserverClosedError(ObserverError):
    """aRx error for when observer is used when closed."""

    def __init__(self, instance):
        """ObserverClosedError constructor.

        Arguments:
            instance: Observer instance.

        """
        super().__init__(f"{type(instance).__qualname__} is closed")

    pass


class SingleStreamError(ARxError):
    """aRx error for when SingleStream are subscribe more than once."""
    pass


class MultiStreamError(ARxError):
    """aRx error for when SingleStream are subscribe more than once."""
    pass


class ARxWarning(Warning):
    """aRx base warning class."""

    def __init__(self, msg: str, error: T.Optional[Exception] = None):
        from traceback import TracebackException
        if error is not None:
            msg += (
                "\n" +
                "".join(TracebackException.from_exception(error).format())
            )

        super().__init__(msg)


class DisposeWarning(ARxWarning):
    """aRx error for when dispose fails."""
    pass
