class CancelToken:
    def __init__(self):
        self._cancel = False

    @property
    def is_cancelled(self) -> bool:
        return self._cancel

    def cancel(self) -> None:
        self._cancel = True
