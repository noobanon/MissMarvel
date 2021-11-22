import time
from functools import wraps
import timeit
from mwt import mwt

@mwt(timeout=60*10)
def get_admin_ids(bot, chat_id):
    """Returns a list of admin IDs for a given chat. Results are cached for 1 hour."""
    return [admin.user.id for admin in bot.get_chat_administrators(chat_id)]

class MWT(object): 
    """Memoize With Timeout"""
    _caches = {}
    _timeouts = {}

    def __init__(self, timeout=2):
        self.timeout = timeout

    def collect(self):
        """Clear cache of results which have timed out"""
        t = time.time()

        for func in self._caches:
            cache = {}

            for key in self._caches[func]:
                if (t - self._caches[func][key][1]) < self._timeouts[func]:
                    cache[key] = self._caches[func][key]

            self._caches[func] = cache

    def __call__(self, f):
        cache = self._caches[f] = {}
        self._timeouts[f] = self.timeout

        @wraps(f)
        def func(*args, **kwargs):
            kw = sorted(kwargs.items())
            key = (args, tuple(kw))
            t = time.time()

            try:
                v = cache[key]
                print("cache")

                if (t - v[1]) > self.timeout:
                    raise KeyError

            except KeyError:
                print("new")
                v = cache[key] = f(*args,**kwargs), t

            return v[0]

        def clear_cache():
            self._caches[f].clear()

        func.clear_cache = clear_cache

        return func
