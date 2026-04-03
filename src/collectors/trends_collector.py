import logging 
import os 
import time 
try :
    from tenacity import retry ,stop_after_attempt ,wait_exponential ,retry_if_exception_type ,before_sleep_log 
except ImportError :
    def retry (*a ,**kw ):return lambda f :f 
    def stop_after_attempt (n ):return None 
    def wait_exponential (**kw ):return None 
    def retry_if_exception_type (*a ):return None 
    def before_sleep_log (*a ):return None 
import requests 
from typing import List ,Dict ,Any 

import pandas as pd 
import yaml 

from src .collectors .retry_utils import safe_scrape 

logger =logging .getLogger (__name__ )

SAMPLE_PATH =os .path .join ("data","sample","sample_trends.csv")
RAW_PATH =os .path .join ("data","raw","trends_raw.csv")

@retry (
stop =stop_after_attempt (4 ),
wait =wait_exponential (multiplier =1 ,min =3 ,max =60 ),
retry =retry_if_exception_type ((requests .HTTPError ,ConnectionError ,TimeoutError ,Exception )),
before_sleep =before_sleep_log (logger ,logging .WARNING ),
)
def _fetch_trends_with_backoff (pytrends ,batch ,timeframe ,geo ):
    pytrends .build_payload (batch ,cat =0 ,timeframe =timeframe ,geo =geo )
    return pytrends .interest_over_time ()

def load_config ():
    config_path =os .path .join ("config","settings.yaml")
    try :
        with open (config_path ,"r",encoding ="utf-8")as f :
            return yaml .safe_load (f )
    except Exception as e :
        logger .warning ("Failed to load settings: %s",e )
        return None 

def load_sample_data ()->pd .DataFrame :
    logger .warning ("Using sample data - live collection failed")
    try :
        df =pd .read_csv (SAMPLE_PATH ,encoding ="utf-8")
        logger .info ("Loaded %d trend records from sample data",len (df ))
        return df 
    except Exception as e :
        logger .error ("Failed to load sample data: %s",e )
        return pd .DataFrame ()

def collect_all ()->pd .DataFrame :
    logger .info ("="*60 )
    logger .info ("Starting search trends collection")
    logger .info ("="*60 )

    config =load_config ()
    all_trends =[]

    if config :
        try :
            from pytrends .request import TrendReq 
            trends_config =config .get ("trends",{})
            geo =trends_config .get ("geo","SA")
            timeframe =trends_config .get ("timeframe","today 12-m")
            keywords =trends_config .get ("keywords_ar",[])+trends_config .get ("keywords_en",[])
            pytrends =TrendReq (hl ="ar",tz =180 )

            for i in range (0 ,len (keywords ),5 ):
                batch =keywords [i :i +5 ]
                try :
                    data =_fetch_trends_with_backoff (pytrends ,batch ,timeframe ,geo )
                    if not data .empty :
                        data =data .drop (columns =["isPartial"],errors ="ignore")
                        for keyword in batch :
                            if keyword in data .columns :
                                for date ,value in data [keyword ].items ():
                                    all_trends .append ({
                                    "keyword":keyword ,
                                    "date":date .strftime ("%Y-%m-%d"),
                                    "region":geo ,
                                    "interest_value":float (value ),
                                    })
                    time .sleep (3 )
                except Exception as e :
                    logger .warning ("Trends batch failed: %s",e )
                    continue 
        except ImportError :
            logger .error ("pytrends not installed")
        except Exception as e :
            logger .warning ("Trends collection failed: %s",e )

    if not all_trends :
        df =load_sample_data ()
    else :
        df =pd .DataFrame (all_trends )

    if not df .empty :
        os .makedirs (os .path .dirname (RAW_PATH ),exist_ok =True )
        df .to_csv (RAW_PATH ,index =False ,encoding ="utf-8-sig")

    return df 

if __name__ =="__main__":
    logging .basicConfig (level =logging .INFO ,format ="%(asctime)s | %(levelname)s | %(message)s")
    result =collect_all ()
    print (f"\nTotal trend records: {len (result )}")
