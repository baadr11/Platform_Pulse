import logging 
import os 
import sys 

import pandas as pd 
import numpy as np 

sys .path .insert (0 ,os .path .join (os .path .dirname (__file__ ),"..",".."))

logger =logging .getLogger (__name__ )

def load_data_for_anomaly ()->dict :
    data ={}
    for path in [
    os .path .join ("data","processed","reviews_normalized.csv"),
    os .path .join ("data","processed","reviews_cleaned.csv"),
    os .path .join ("data","sample","sample_reviews.csv"),
    ]:
        if os .path .exists (path ):
            try :
                df =pd .read_csv (path ,encoding ="utf-8-sig")
                df ["date"]=pd .to_datetime (df ["date"],errors ="coerce")
                df =df .dropna (subset =["date"])
                daily =df .groupby ([pd .Grouper (key ="date",freq ="W"),"app_name"]).size ().reset_index (name ="count")
                data ["reviews"]=daily 
            except Exception as e :
                logger .warning ("Failed to load reviews: %s",e )
            break 

    for path in [
    os .path .join ("data","processed","trends_cleaned.csv"),
    os .path .join ("data","sample","sample_trends.csv"),
    ]:
        if os .path .exists (path ):
            try :
                df =pd .read_csv (path ,encoding ="utf-8-sig")
                data ["trends"]=df 
            except Exception as e :
                logger .warning ("Failed to load trends: %s",e )
            break 

    return data 

def detect_anomalies_isolation_forest (df :pd .DataFrame ,value_column :str ,
contamination :float =0.1 ,
random_state :int =42 )->pd .DataFrame :
    if df .empty or value_column not in df .columns :
        return df 

    try :
        from sklearn .ensemble import IsolationForest 
    except ImportError :
        logger .error ("scikit-learn not installed")
        return detect_anomalies_simple (df ,value_column )

    df =df .copy ()
    values =df [[value_column ]].fillna (0 ).values 

    if len (values )<5 :
        logger .warning ("Insufficient data - using simple detection")
        return detect_anomalies_simple (df ,value_column )

    model =IsolationForest (contamination =contamination ,random_state =random_state ,n_estimators =100 )
    predictions =model .fit_predict (values )
    scores =model .decision_function (values )

    df ["is_anomaly"]=predictions ==-1 
    df ["anomaly_score"]=scores 
    return df 

def detect_anomalies_simple (df :pd .DataFrame ,value_column :str )->pd .DataFrame :
    df =df .copy ()
    values =pd .to_numeric (df [value_column ],errors ="coerce")
    mean_val =values .mean ()
    std_val =values .std ()

    if std_val ==0 :
        df ["is_anomaly"]=False 
        df ["anomaly_score"]=0 
        return df 

    z_scores =(values -mean_val )/std_val 
    df ["is_anomaly"]=z_scores .abs ()>2 
    df ["anomaly_score"]=-z_scores .abs ()
    return df 

def generate_alerts (anomalies_df :pd .DataFrame ,source :str )->list :
    alerts =[]
    if anomalies_df .empty or "is_anomaly"not in anomalies_df .columns :
        return alerts 
    for _ ,row in anomalies_df [anomalies_df ["is_anomaly"]].iterrows ():
        alert ={"source":source ,"date":str (row .get ("date","")),"details":{}}
        if "app_name"in row :alert ["details"]["app"]=row ["app_name"]
        if "count"in row :alert ["details"]["value"]=float (row ["count"])
        if "anomaly_score"in row :alert ["details"]["score"]=float (row ["anomaly_score"])
        alerts .append (alert )
    return alerts 

def run_anomaly_detection ()->dict :
    logger .info ("="*60 )
    logger .info ("Starting anomaly detection")
    logger .info ("="*60 )

    data =load_data_for_anomaly ()
    all_alerts =[]

    if "reviews"in data and not data ["reviews"].empty :
        try :
            result =detect_anomalies_isolation_forest (data ["reviews"],"count")
            alerts =generate_alerts (result ,"reviews")
            all_alerts .extend (alerts )
            output_path =os .path .join ("data","processed","anomalies_reviews.csv")
            os .makedirs (os .path .dirname (output_path ),exist_ok =True )
            result .to_csv (output_path ,index =False ,encoding ="utf-8-sig")
        except Exception as e :
            logger .error ("Reviews anomaly detection failed: %s",e )

    if "trends"in data and not data ["trends"].empty :
        try :
            result =detect_anomalies_isolation_forest (data ["trends"],"interest_value")
            alerts =generate_alerts (result ,"trends")
            all_alerts .extend (alerts )
            output_path =os .path .join ("data","processed","anomalies_trends.csv")
            os .makedirs (os .path .dirname (output_path ),exist_ok =True )
            result .to_csv (output_path ,index =False ,encoding ="utf-8-sig")
        except Exception as e :
            logger .error ("Trends anomaly detection failed: %s",e )

    if all_alerts :
        alerts_df =pd .DataFrame (all_alerts )
        alerts_path =os .path .join ("data","processed","anomaly_alerts.csv")
        os .makedirs (os .path .dirname (alerts_path ),exist_ok =True )
        alerts_df .to_csv (alerts_path ,index =False ,encoding ="utf-8-sig")

    return {"total_alerts":len (all_alerts ),"alerts":all_alerts }

if __name__ =="__main__":
    logging .basicConfig (level =logging .INFO ,format ="%(asctime)s | %(levelname)s | %(message)s")
    result =run_anomaly_detection ()
    print (f"\nTotal alerts: {result ['total_alerts']}")
