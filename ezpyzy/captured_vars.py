
import inspect as ins


class CapturedVars:

    def __init__(self, frames_back=None, capture_overwritten_vars=False):
        object.__setattr__(self, '_original_vars', None)
        object.__setattr__(self, '_capture_overwritten_vars', None)
        object.__setattr__(self, '_captured', {})
        if frames_back is not None:
            frame = ins.currentframe()
            for i in range(frames_back):
                frame = frame.f_back
                object.__setattr__(self, '_captured', frame.f_locals)

    def __getattr__(self, item):
        return self._captured[item]

    def __setattr__(self, key, value):
        self._captured[key] = value

    def __getitem__(self, item):
        return self._captured[item]

    def __setitem__(self, key, value):
        self._captured[key] = value

    def __iter__(self):
        return iter(self._captured.items())

    def __len__(self):
        return len(self._captured)

    def __contains__(self, item):
        return item in self._captured

    def __enter__(self):
        object.__setattr__(self, '_original_vars', ins.currentframe().f_back.f_locals.copy())
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        vars = ins.currentframe().f_back.f_locals.copy()
        for name, var in vars.items():
            if var is self:
                continue
            if name not in self._original_vars:
                self._captured[name] = var
            elif self._capture_overwritten_vars and self._original_vars[name] is not var:
                self._captured[name] = var

    def __str__(self):
        return f"CapturedVars({', '.join(key+': '+str(value) for key, value in self)})"