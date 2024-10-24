from functools import wraps

_log_function_io_depth = 0
def log_function_io(f):
    """ Decorator to set up conditions for working on remote Django directory (e.g. activate virtualenv if necessary, set DJANGO_SETTINGS_MODULE if necessary) """
    @wraps(f)
    def wrapper(*args, **kwargs):
        global _log_function_io_depth
        def print_tabbed(s):
            print('\n'.join(('\t'*_log_function_io_depth)+part for part in s.split('\n')))
        print_tabbed(f"Calling {f.__name__}:\n\targs: {args}\n\tkwargs: {kwargs}")
        _log_function_io_depth += 1
        try:
            result = f(*args, **kwargs)
            _log_function_io_depth -= 1
            print_tabbed(f"Return value of {f.__name__}: >>>{result}<<< ({type(result)})")
        except Exception as e:
            _log_function_io_depth -= 1
            print_tabbed(f"Exception {type(e)} raised in {f.__name__}: {e}")
            raise
        return result
    return wrapper
