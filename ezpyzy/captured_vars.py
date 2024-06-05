
import inspect as ins


class CapturedVars:

    def __init__(self, frames_back=1, capture_overwritten_vars=True):
        object.__setattr__(self, '_original_vars', None)
        object.__setattr__(self, '_capture_overwritten_vars', capture_overwritten_vars)
        object.__setattr__(self, '_frames_back', frames_back)
        frame = ins.currentframe()
        for i in range(object.__getattribute__(self, '_frames_back')):
            frame = frame.f_back
        object.__setattr__(self, '_frame', frame.f_locals)
        object.__setattr__(self, '_captured', frame.f_locals)

    def __getattr__(self, item):
        return self._captured[item]

    def __setattr__(self, key, value):
        self._frame[key] = value

    def __getitem__(self, item):
        return self._captured[item]

    def __setitem__(self, key, value):
        self._frame[key] = value

    def __iter__(self):
        return iter(self._captured.items())

    def __len__(self):
        return len(self._captured)

    def __contains__(self, item):
        return item in self._captured

    def __enter__(self):
        frame = ins.currentframe()
        for i in range(object.__getattribute__(self, '_frames_back')):
            frame = frame.f_back
        object.__setattr__(self, '_frame', frame.f_locals)
        object.__setattr__(self, '_original_vars', frame.f_locals.copy())
        object.__setattr__(self, '_captured', {})
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        vars = self._frame.copy()
        for name, var in vars.items():
            if var is self:
                continue
            if name not in self._original_vars:
                self._captured[name] = var
            elif self._capture_overwritten_vars and self._original_vars[name] is not var:
                self._captured[name] = var

    def __str__(self):
        return f"CapturedVars({', '.join(key+': '+str(value) for key, value in self)})"