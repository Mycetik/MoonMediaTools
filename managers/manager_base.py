from abc import ABC, abstractmethod


class Valid(ABC):
    def __init__(self):
        self._valid: bool = True

    def check_valid(self):
        if not self._valid:
            raise RuntimeError(f"Object `{self}` is no longer valid")

    def _set_valid(self, v: bool):
        self._valid = v


    @property
    def is_valid(self) -> bool:
        return self._valid


class Manager(Valid):
    def __init__(self):
        super().__init__()
        self._set_valid(False)

    def init(self):
        if self.is_valid:
            raise RuntimeError("Manager already initialized")

        self._set_valid(True)

        try:
            self._init0()
        except Exception as e:
            self._set_valid(False)
            raise e

    def shutdown(self):
        self.check_valid()

        try:
            self._shutdown0()
        finally:
            self._set_valid(False)

    def init_if_needed(self) -> bool:
        if self.is_valid:
            return False

        self.init()
        return True

    def shutdown_if_needed(self) -> bool:
        if not self.is_valid:
            return False

        self.shutdown()
        return True

    @abstractmethod
    def _init0(self):
        pass

    @abstractmethod
    def _shutdown0(self):
        pass