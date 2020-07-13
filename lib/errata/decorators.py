from lib.errata.kerberos import handle_kinit
import functools


def update_keytab(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        handle_kinit()
        func_ret = func(*args, **kwargs)
        return func_ret
    return wrapper
