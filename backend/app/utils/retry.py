import time
from functools import wraps
from typing import Callable, Type, Tuple


def retry(
        exceptions: Tuple[Type[Exception]] = (Exception,),
        max_attempts: int = 3,
        delay: float = 1.0,
        backoff: float = 2.0
):
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            attempts = 0
            current_delay = delay

            while attempts < max_attempts:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    attempts += 1
                    if attempts == max_attempts:
                        raise e

                    time.sleep(current_delay)
                    current_delay *= backoff
            return func(*args, **kwargs)

        return wrapper

    return decorator


