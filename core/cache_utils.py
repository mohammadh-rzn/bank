# core/cache_utils.py
from django.core.cache import cache
from django.conf import settings

def user_caches_add(user_id,cache_key):
    if cache.get(user_id) is None:
        cache.set(user_id, [cache_key], settings.USER_CACHE_TIMEOUT)
    else:
        new_cache =cache.get(user_id)
        new_cache.append(cache_key)
        cache.set(user_id, new_cache, settings.USER_CACHE_TIMEOUT)

def make_cache_key(*parts):
    """Create consistent cache keys"""
    return "_".join(str(part) for part in parts)

def cache_user_balance(user_id, balance_data):
    cache_key = make_cache_key("user", "balance", user_id)
    cache.set(cache_key, balance_data, settings.BALANCE_CACHE_TIMEOUT)
    user_caches_add(user_id, cache_key)

def get_cached_user_balance(user_id):
    cache_key = make_cache_key("user", "balance", user_id)
    return cache.get(cache_key)

def invalidate_user_balance(user_id):
    cache_key = make_cache_key("user", "balance", user_id)
    cache.delete(cache_key)

def cache_user_transactions(user_id, page, page_size, data):
    cache_key = make_cache_key("user", "transactions", user_id, page, page_size)
    cache.set(cache_key, data, settings.TRANSACTIONS_CACHE_TIMEOUT)
    user_caches_add(user_id, cache_key)
    

def get_cached_user_transactions(user_id, page, page_size):
    cache_key = make_cache_key("user", "transactions", user_id, page, page_size)
    return cache.get(cache_key)


def get_cached_user_transactions(user_id, page, page_size):
    cache_key = make_cache_key("user", "transactions", user_id, page, page_size)
    return cache.get(cache_key)

def invalidate_user_caches(user_id):
    to_be_removed =cache.get(user_id)
    if to_be_removed is not None:
        for cache_key in to_be_removed:
            cache.delete(cache_key)
    cache.delete(user_id)
    # Invalidate both balance and transactions caches
    