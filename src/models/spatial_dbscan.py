import logging 
import os 
import sys 

import pandas as pd 
import numpy as np 

sys .path .insert (0 ,os .path .join (os .path .dirname (__file__ ),"..",".."))

logger =logging .getLogger (__name__ )

def load_spatial_data ()->pd .DataFrame :
    paths =[
    os .path .join ("data","processed","spatial_normalized.csv"),
    os .path .join ("data","raw","spatial_raw.csv"),
    os .path .join ("data","sample","sample_spatial.csv"),
    ]
    for path in paths :
        if os .path .exists (path ):
            try :
                df =pd .read_csv (path ,encoding ="utf-8-sig")
                logger .info ("Loaded spatial records from %s",path )
                return df 
            except Exception as e :
                logger .warning ("Failed to load %s: %s",path ,e )
    logger .error ("No spatial data found")
    return pd .DataFrame ()

def run_dbscan_clustering (df :pd .DataFrame ,eps :float =2.0 ,
min_samples :int =2 )->pd .DataFrame :
    if df .empty :
        return df 

    required_cols =["latitude","longitude","activity_score"]
    for col in required_cols :
        if col not in df .columns :
            logger .error ("Required column missing: %s",col )
            return df 

    try :
        from sklearn .cluster import DBSCAN 
        from sklearn .preprocessing import StandardScaler 
    except ImportError :
        logger .error ("scikit-learn not installed")
        return assign_labels_simple (df )

    features =df [["latitude","longitude","activity_score"]].copy ().fillna (0 )

    scaler =StandardScaler ()
    features_scaled =scaler .fit_transform (features )

    dbscan =DBSCAN (eps =eps ,min_samples =min_samples ,metric ="euclidean")
    labels =dbscan .fit_predict (features_scaled )

    df =df .copy ()
    df ["cluster_id"]=labels 

    cluster_means ={}
    for cluster_id in set (labels ):
        if cluster_id ==-1 :
            continue 
        mask =labels ==cluster_id 
        cluster_means [cluster_id ]=df .loc [mask ,"activity_score"].mean ()

    def label_cluster (row ):
        cid =row ["cluster_id"]
        score =row .get ("activity_score",0 )
        if cid ==-1 :
            if score >=60 :
                return "نشاط_عالي"
            elif score >=35 :
                return "نشاط_متوسط"
            else :
                return "نشاط_منخفض"
        mean_score =cluster_means .get (cid ,0 )
        if mean_score >=60 :
            return "نشاط_عالي"
        elif mean_score >=35 :
            return "نشاط_متوسط"
        else :
            return "نشاط_منخفض"

    df ["cluster_label"]=df .apply (label_cluster ,axis =1 )

    n_clusters =len (set (labels )-{-1 })
    n_noise =(labels ==-1 ).sum ()
    logger .info ("DBSCAN: %d clusters, %d noise points",n_clusters ,n_noise )
    return df 

def assign_labels_simple (df :pd .DataFrame )->pd .DataFrame :
    if df .empty or "activity_score"not in df .columns :
        return df 

    df =df .copy ()

    def simple_label (score ):
        if score >=60 :
            return "نشاط_عالي"
        elif score >=35 :
            return "نشاط_متوسط"
        else :
            return "نشاط_منخفض"

    df ["cluster_label"]=df ["activity_score"].apply (simple_label )
    df ["cluster_id"]=-1 
    return df 

def run_spatial_analysis ()->pd .DataFrame :
    logger .info ("="*60 )
    logger .info ("Starting spatial analysis")
    logger .info ("="*60 )

    df =load_spatial_data ()
    if df .empty :
        return df 

    result =run_dbscan_clustering (df )

    output_path =os .path .join ("data","processed","spatial_clustered.csv")
    os .makedirs (os .path .dirname (output_path ),exist_ok =True )
    result .to_csv (output_path ,index =False ,encoding ="utf-8-sig")
    logger .info ("Saved results: %s",output_path )
    return result 

if __name__ =="__main__":
    logging .basicConfig (level =logging .INFO ,format ="%(asctime)s | %(levelname)s | %(message)s")
    result =run_spatial_analysis ()
    print (f"\nTotal cities classified: {len (result )}")
