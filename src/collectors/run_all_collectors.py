import logging 
import os 
import sys 

sys .path .insert (0 ,os .path .join (os .path .dirname (__file__ ),"..",".."))

from src .collectors .appstore_collector import collect_all as collect_reviews 
from src .collectors .trends_collector import collect_all as collect_trends 
from src .collectors .spatial_collector import collect_all as collect_spatial 
from src .collectors .official_collector import collect_all as collect_official 
from src .database .db_manager import DatabaseManager 

logger =logging .getLogger (__name__ )

def run_all_collectors ():
    logging .basicConfig (
    level =logging .INFO ,
    format ="%(asctime)s | %(levelname)s | %(message)s",
    datefmt ="%H:%M:%S"
    )

    logger .info ("="*70 )
    logger .info ("Platform Pulse - Starting data collection from all sources")
    logger .info ("="*70 )

    db =DatabaseManager ()
    results ={}

    logger .info ("[1/5] Collecting app reviews...")
    try :
        reviews_df =collect_reviews ()
        if not reviews_df .empty :
            records =reviews_df .to_dict ("records")
            count =db .insert_reviews (records )
            db .log_quality ("app_reviews",len (records ),count )
            results ["reviews"]=count 
            logger .info ("App reviews: %d records",count )
        else :
            results ["reviews"]=0 
            logger .warning ("No reviews collected")
    except Exception as e :
        logger .error ("Review collection failed: %s",e )
        results ["reviews"]=0 

    logger .info ("[2/5] Collecting search trends...")
    try :
        trends_df =collect_trends ()
        if not trends_df .empty :
            records =trends_df .to_dict ("records")
            count =db .insert_trends (records )
            db .log_quality ("search_trends",len (records ),count )
            results ["trends"]=count 
            logger .info ("Search trends: %d records",count )
        else :
            results ["trends"]=0 
            logger .warning ("No trends collected")
    except Exception as e :
        logger .error ("Trend collection failed: %s",e )
        results ["trends"]=0 

    logger .info ("[3/5] Collecting spatial data...")
    try :
        spatial_df =collect_spatial ()
        if not spatial_df .empty :
            records =spatial_df .to_dict ("records")
            count =db .insert_spatial (records )
            db .log_quality ("spatial_data",len (records ),count )
            results ["spatial"]=count 
            logger .info ("Spatial data: %d records",count )
        else :
            results ["spatial"]=0 
            logger .warning ("No spatial data collected")
    except Exception as e :
        logger .error ("Spatial data collection failed: %s",e )
        results ["spatial"]=0 

    logger .info ("[4/5] Collecting official data...")
    try :
        official_df =collect_official ()
        if not official_df .empty :
            records =official_df .to_dict ("records")
            count =db .insert_official_stats (records )
            db .log_quality ("official_stats",len (records ),count )
            results ["official"]=count 
            logger .info ("Official data: %d records",count )
        else :
            results ["official"]=0 
            logger .warning ("No official data collected")
    except Exception as e :
        logger .error ("Official data collection failed: %s",e )
        results ["official"]=0 

    logger .info ("[5/5] Collecting social data...")
    try :
        from src .collectors .social_collector import run_social_collector 
        social_df =run_social_collector ()
        if not social_df .empty :
            results ["social"]=len (social_df )
            logger .info ("Social data: %d records",len (social_df ))
        else :
            results ["social"]=0 
            logger .warning ("No social data collected — credentials may be missing")
    except Exception as e :
        logger .error ("Social collection failed: %s",e )
        results ["social"]=0 

    logger .info ("="*70 )
    logger .info ("Data collection summary:")
    for k ,v in results .items ():
        logger .info ("  %s: %d records",k ,v )
    total =sum (results .values ())
    logger .info ("  Total: %d records",total )
    logger .info ("="*70 )

    counts =db .get_table_counts ()
    logger .info ("Database status:")
    for table ,count in counts .items ():
        logger .info ("  %s: %d records",table ,count )

    return results 

if __name__ =="__main__":
    run_all_collectors ()
