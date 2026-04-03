import logging 
import os 
import sys 

import pandas as pd 
import numpy as np 

sys .path .insert (0 ,os .path .join (os .path .dirname (__file__ ),"..",".."))

logger =logging .getLogger (__name__ )

def prepare_time_series (reviews_path :str =None ,trends_path :str =None )->pd .DataFrame :
    data_frames =[]

    for path in [
    reviews_path ,
    os .path .join ("data","processed","reviews_normalized.csv"),
    os .path .join ("data","processed","reviews_cleaned.csv"),
    os .path .join ("data","raw","reviews_raw.csv"),
    os .path .join ("data","sample","sample_reviews.csv"),
    ]:
        if path and os .path .exists (path ):
            try :
                df =pd .read_csv (path ,encoding ="utf-8-sig")
                df ["date"]=pd .to_datetime (df ["date"],errors ="coerce")
                df =df .dropna (subset =["date"])
                daily =df .groupby (pd .Grouper (key ="date",freq ="W")).size ().reset_index (name ="y")
                daily .columns =["ds","y"]
                data_frames .append (daily )
                logger .info ("Review data loaded: %d points",len (daily ))
            except Exception as e :
                logger .warning ("Failed to load %s: %s",path ,e )
            break 

    for path in [
    trends_path ,
    os .path .join ("data","processed","trends_cleaned.csv"),
    os .path .join ("data","raw","trends_raw.csv"),
    os .path .join ("data","sample","sample_trends.csv"),
    ]:
        if path and os .path .exists (path ):
            try :
                df =pd .read_csv (path ,encoding ="utf-8-sig")
                df ["date"]=pd .to_datetime (df ["date"],errors ="coerce")
                df =df .dropna (subset =["date"])
                if "interest_value"in df .columns :
                    monthly =df .groupby (pd .Grouper (key ="date",freq ="W"))["interest_value"].mean ().reset_index ()
                    monthly .columns =["ds","y"]
                    data_frames .append (monthly )
                    logger .info ("Trends data loaded: %d points",len (monthly ))
            except Exception as e :
                logger .warning ("Failed to load %s: %s",path ,e )
            break 

    if not data_frames :
        logger .warning ("No data available - generating synthetic time series")
        dates =pd .date_range (start ="2025-04-01",periods =52 ,freq ="W")
        np .random .seed (42 )
        values =50 +np .cumsum (np .random .randn (52 )*3 )+np .sin (np .arange (52 )*2 *np .pi /12 )*10 
        values =np .clip (values ,10 ,100 )
        return pd .DataFrame ({"ds":dates ,"y":values })

    combined =data_frames [0 ]
    for df in data_frames [1 :]:
        combined =pd .merge (combined ,df ,on ="ds",how ="outer",suffixes =("","_trend"))
        if "y_trend"in combined .columns :
            combined ["y"]=combined [["y","y_trend"]].mean (axis =1 )
            combined =combined .drop (columns =["y_trend"])

    combined =combined .sort_values ("ds").reset_index (drop =True )
    combined ["y"]=combined ["y"].ffill ().bfill ()
    return combined 

def add_saudi_seasonality (model ):
    try :
        model .add_seasonality (name ="islamic_calendar",period =354.37 ,fourier_order =5 )
        logger .info ("Saudi Islamic calendar seasonality added")
    except Exception as e :
        logger .warning ("Failed to add seasonality: %s",e )
    return model 

def validate_prophet_model (model ,horizon ="30 days",period ="90 days",initial ="180 days")->dict :
    try :
        from prophet .diagnostics import cross_validation ,performance_metrics 
        df_cv =cross_validation (model ,initial =initial ,period =period ,horizon =horizon ,parallel ="processes")
        metrics =performance_metrics (df_cv )
        result ={
        "mape":round (float (metrics ["mape"].mean ()*100 ),2 ),
        "rmse":round (float (metrics ["rmse"].mean ()),4 ),
        "coverage":round (float (metrics ["coverage"].mean ()*100 ),1 ),
        }
        logger .info ("Prophet validation — MAPE: %s%%  RMSE: %s  Coverage: %s%%",
        result ["mape"],result ["rmse"],result ["coverage"])
        return result 
    except Exception as e :
        logger .warning ("Prophet validation failed: %s",e )
        return {}

def run_prophet_forecast (forecast_periods :int =90 ,confidence_intervals :list =None )->dict :
    if confidence_intervals is None :
        confidence_intervals =[0.80 ,0.95 ]

    logger .info ("="*60 )
    logger .info ("Starting Prophet time series forecasting")
    logger .info ("="*60 )

    ts_data =prepare_time_series ()

    if len (ts_data )<4 :
        logger .error ("Insufficient data for forecast (less than 4 points)")
        return {"success":False ,"error":"Insufficient data"}

    results ={}

    try :
        from prophet import Prophet 

        for ci in confidence_intervals :
            logger .info ("Forecasting with %.0f%% confidence interval...",ci *100 )

            model =Prophet (
            interval_width =ci ,
            seasonality_mode ="multiplicative",
            daily_seasonality =False ,
            weekly_seasonality =True ,
            yearly_seasonality =True ,
            )
            model =add_saudi_seasonality (model )
            model .fit (ts_data )

            if len (ts_data )>=14 :
                validation_metrics =validate_prophet_model (model )
                results ["validation_metrics"]=validation_metrics 

                if validation_metrics :
                    metrics_output_path =os .path .join ("data","processed","forecast_metrics.json")
                    os .makedirs (os .path .dirname (metrics_output_path ),exist_ok =True )
                    import json 
                    with open (metrics_output_path ,"w",encoding ="utf-8")as mf :
                        json .dump (validation_metrics ,mf ,ensure_ascii =False ,indent =2 )
                    logger .info ("Forecast validation metrics saved to %s",metrics_output_path )
            else :
                logger .info ("Skipping cross-validation — insufficient data points (<14)")

            future =model .make_future_dataframe (periods =forecast_periods ,freq ="D")
            forecast =model .predict (future )
            results [f"ci_{int (ci *100 )}"]=forecast [["ds","yhat","yhat_lower","yhat_upper"]]

        full_forecast =results .get (f"ci_{int (confidence_intervals [0 ]*100 )}")
        if full_forecast is not None :
            output_path =os .path .join ("data","processed","forecast_results.csv")
            os .makedirs (os .path .dirname (output_path ),exist_ok =True )
            full_forecast .to_csv (output_path ,index =False )
            logger .info ("Forecast results saved: %s",output_path )

        return {"success":True ,"forecasts":results ,"historical":ts_data ,"periods":forecast_periods }

    except ImportError :
        logger .warning ("Prophet not installed - using simple forecast")
        return run_simple_forecast (ts_data ,forecast_periods )
    except Exception as e :
        logger .error ("Prophet error: %s",e )
        return run_simple_forecast (ts_data ,forecast_periods )

def run_simple_forecast (ts_data :pd .DataFrame ,periods :int =90 )->dict :
    logger .info ("Using simple linear forecast fallback...")

    last_values =ts_data ["y"].tail (4 ).values 
    trend =np .mean (np .diff (last_values ))if len (last_values )>1 else 0 
    last_value =ts_data ["y"].iloc [-1 ]
    last_date =pd .to_datetime (ts_data ["ds"].iloc [-1 ])

    future_dates =pd .date_range (start =last_date +pd .Timedelta (days =1 ),periods =periods ,freq ="D")
    predictions =[last_value +trend *i for i in range (1 ,periods +1 )]
    std =np .std (last_values )if len (last_values )>1 else last_value *0.1 

    forecast_df =pd .DataFrame ({
    "ds":future_dates ,
    "yhat":predictions ,
    "yhat_lower":[p -1.96 *std for p in predictions ],
    "yhat_upper":[p +1.96 *std for p in predictions ],
    })

    output_path =os .path .join ("data","processed","forecast_results.csv")
    os .makedirs (os .path .dirname (output_path ),exist_ok =True )
    forecast_df .to_csv (output_path ,index =False )
    logger .info ("Simple forecast completed: %d days",periods )

    return {"success":True ,"forecasts":{"ci_80":forecast_df },"historical":ts_data ,
    "periods":periods ,"method":"linear_fallback"}

if __name__ =="__main__":
    logging .basicConfig (level =logging .INFO ,format ="%(asctime)s | %(levelname)s | %(message)s")
    result =run_prophet_forecast ()
    if result ["success"]:
        print (f"\nForecast completed successfully ({result ['periods']} days)")
    else :
        print (f"\nForecast failed: {result .get ('error','Unknown error')}")
