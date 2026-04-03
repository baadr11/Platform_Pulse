import logging 
import os 
import sys 

sys .path .insert (0 ,os .path .dirname (__file__ ))

logging .basicConfig (
level =logging .INFO ,
format ="%(asctime)s | %(levelname)s | %(message)s",
datefmt ="%H:%M:%S",
)

logger =logging .getLogger (__name__ )

def run_sentiment ():
    try :
        from src .models .sentiment_marbert import analyze_reviews_sentiment 
        logger .info ("Running Arabic sentiment analysis")
        result =analyze_reviews_sentiment ()
        logger .info ("Sentiment analysis complete: %d records",len (result ))
    except Exception as e :
        logger .error ("Sentiment analysis failed: %s",e )

def run_spatial ():
    try :
        from src .models .spatial_dbscan import run_spatial_analysis 
        logger .info ("Running spatial DBSCAN clustering")
        run_spatial_analysis ()
        logger .info ("Spatial analysis complete")
    except Exception as e :
        logger .error ("Spatial analysis failed: %s",e )

def run_anomaly ():
    try :
        from src .models .anomaly_detection import run_anomaly_detection 
        logger .info ("Running anomaly detection")
        run_anomaly_detection ()
        logger .info ("Anomaly detection complete")
    except Exception as e :
        logger .error ("Anomaly detection failed: %s",e )

def run_composite ():
    try :
        from src .models .composite_index import compute_composite_index ,compute_gap_analysis 
        logger .info ("Computing composite index")
        index_df =compute_composite_index ()
        logger .info ("Composite index complete: %d rows",len (index_df ))
        logger .info ("Computing gap analysis")
        gap_df =compute_gap_analysis ()
        logger .info ("Gap analysis complete: %d rows",len (gap_df ))
    except Exception as e :
        logger .error ("Composite index / gap analysis failed: %s",e )

def run_forecast ():
    try :
        from src .models .prophet_forecast import run_prophet_forecast 
        logger .info ("Running Prophet forecast")
        result =run_prophet_forecast ()
        if result .get ("success"):
            logger .info ("Prophet forecast complete")
        else :
            logger .warning ("Prophet forecast returned non-success: %s",result .get ("error"))
    except Exception as e :
        logger .error ("Prophet forecast failed: %s",e )

if __name__ =="__main__":
    logger .info ("="*60 )
    logger .info ("Platform Pulse model pipeline starting")
    logger .info ("="*60 )

    run_sentiment ()
    run_spatial ()
    run_anomaly ()
    run_composite ()
    run_forecast ()

    logger .info ("="*60 )
    logger .info ("All models complete")
    logger .info ("="*60 )
