from api.kerberos import do_kinit
import functools


def update_keytab(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        do_kinit()
        func_ret = func(*args, **kwargs)
        return func_ret
    return wrapper
