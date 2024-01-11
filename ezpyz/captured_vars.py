
import inspect as ins


class CapturedVars(dict):

    def __init__(self, capture_overwritten_vars=False):
        self._original_vars = None
        self._capture_overwritten_vars = capture_overwritten_vars

    def __enter__(self):
        self._original_vars = ins.currentframe().f_back.f_locals.copy()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        vars = ins.currentframe().f_back.f_locals.copy()
        for name, var in vars.items():
            if var is self:
                continue
            if name not in self._original_vars:
                self[name] = var
            elif self._capture_overwritten_vars and self._original_vars[name] is not var:
                self[name] = var