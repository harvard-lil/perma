from time import sleep

def retry_on_exception(func, args=[], kwargs={}, exception=Exception, attempts=8, log=True):
    """
        Retry func(*args, **kwargs) with exponential backoff, starting from 100ms delay.
    """
    for attempt in range(attempts):
        try:
            return func(*args, **kwargs)
        except exception:
            if attempt < attempts-1:
                if log:
                    print(f"sleeping {(.1*2**attempt)}")
                sleep(.1*2**attempt)
            else:
                raise
