import logging 

logger =logging .getLogger (__name__ )

try :
    from tenacity import (
    retry ,
    stop_after_attempt ,
    wait_exponential ,
    retry_if_exception_type ,
    before_sleep_log ,
    )
    import requests 

    @retry (
    stop =stop_after_attempt (4 ),
    wait =wait_exponential (multiplier =1 ,min =2 ,max =30 ),
    retry =retry_if_exception_type (
    (requests .HTTPError ,ConnectionError ,TimeoutError ,OSError )
    ),
    before_sleep =before_sleep_log (logger ,logging .WARNING ),
    reraise =False ,
    )
    def fetch_with_backoff (func ,*args ,**kwargs ):
        return func (*args ,**kwargs )

    TENACITY_AVAILABLE =True 
    logger .debug ("tenacity retry logic loaded successfully")

except ImportError :
    TENACITY_AVAILABLE =False 
    logger .warning ("tenacity not installed — collectors will run without retry logic.")

    def fetch_with_backoff (func ,*args ,**kwargs ):
        return func (*args ,**kwargs )

def safe_scrape (func ,*args ,fallback =None ,label :str ="",**kwargs ):
    try :
        result =fetch_with_backoff (func ,*args ,**kwargs )
        return result 
    except Exception as e :
        logger .warning (
        f"safe_scrape failed after retries{' ('+label +')'if label else ''}: {e }"
        )
        return fallback
