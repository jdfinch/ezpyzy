
import traceback
import typing
import logging
import sys


catcherlog = logging.getLogger(__name__)
catcherlog.setLevel(logging.WARN)
catcherlogstream = logging.StreamHandler(sys.stderr)
catcherlogstream.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
catcherlog.addHandler(catcherlogstream)

F = typing.TypeVar('F')

def catch(exceptions=(Exception,), log: typing.Optional[callable] = catcherlog.warning):
    """
    Decorator that will catch exceptions and return None, logging traceback to stderr by default
    """
    def decorator(f: F) -> F:
        def wrapper(*args, **kwargs):
            try:
                return f(*args, **kwargs)
            except exceptions:
                if log:
                    log(traceback.format_exc())
            return None
        return wrapper
    return decorator

def snatch(exceptions=(Exception,)):
    """
    Decorator that will silently catch exceptions and return None
    """
    return catch(exceptions=exceptions, log=None)



if __name__ == '__main__':

    @snatch()
    def foo(x, y):
        return x + y / 0
    

    z = foo(3, 5)

    print(z)

