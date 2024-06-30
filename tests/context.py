import sys
from contextlib import contextmanager
from copy import deepcopy
from typing import List


@contextmanager
def context_args(args: List[str], with_prog_name: bool = False):
    """Context manager for sys.argv

    Parameters
    ----------
    args : List[str]
        arguments
    with_prog_name : bool, optional
        the first element in args is the program name, by default False
    """
    orig_argv = deepcopy(sys.argv)
    if with_prog_name:
        sys.argv = args
    else:
        sys.argv = [orig_argv[0], *args]
    try:
        yield
    except SystemExit:
        pass  # Ignore
    except Exception:
        raise
    finally:
        sys.argv = orig_argv
