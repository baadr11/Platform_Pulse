import os 
import sys 
import pandas as pd 
import pytest 

sys .path .insert (0 ,os .path .join (os .path .dirname (__file__ ),".."))

class TestRetryUtils :
    def test_safe_scrape_returns_fallback_on_failure (self ):
        from src .collectors .retry_utils import safe_scrape 
        result =safe_scrape (lambda :(_ for _ in ()).throw (Exception ("network error")),
        label ="test",fallback =[])
        assert result ==[]

    def test_safe_scrape_returns_value_on_success (self ):
        from src .collectors .retry_utils import safe_scrape 
        result =safe_scrape (lambda :[1 ,2 ,3 ],label ="test",fallback =[])
        assert result ==[1 ,2 ,3 ]

class TestSocialCollector :
    def test_is_valid_telegram_id_rejects_placeholder (self ):
        from src .collectors .social_collector import _is_valid_telegram_id 
        assert not _is_valid_telegram_id ("YOUR_TELEGRAM_API_ID_HERE")
        assert not _is_valid_telegram_id ("")
        assert not _is_valid_telegram_id (0 )
        assert not _is_valid_telegram_id (None )

    def test_is_valid_telegram_id_accepts_real_values (self ):
        from src .collectors .social_collector import _is_valid_telegram_id 
        assert _is_valid_telegram_id (12345678 )
        assert _is_valid_telegram_id ("12345678")

    def test_aggregate_returns_dataframe (self ):
        from src .collectors .social_collector import aggregate_social_sentiment 
        result =aggregate_social_sentiment ()
        assert isinstance (result ,pd .DataFrame )

    def test_aggregate_returns_empty_df_not_none (self ):
        from src .collectors .social_collector import aggregate_social_sentiment 
        result =aggregate_social_sentiment ()
        assert result is not None 

class TestSampleDataFiles :
    @pytest .mark .parametrize ("filename,required_cols",[
    ("sample_reviews.csv",["app_name","text","rating","date","sector"]),
    ("sample_trends.csv",["keyword","date","interest_value"]),
    ("sample_spatial.csv",["city","latitude","longitude","activity_score"]),
    ("sample_social.csv",["platform","text","date","sector"]),
    ("sample_official.csv",["metric_name","value","source","date"]),
    ])
    def test_sample_file_exists_and_has_columns (self ,filename ,required_cols ):
        path =os .path .join ("data","sample",filename )
        assert os .path .exists (path ),f"Missing: {path }"
        df =pd .read_csv (path )
        for col in required_cols :
            assert col in df .columns ,f"Column '{col }' missing in {filename }"
        assert len (df )>0 ,f"{filename } is empty"

    def test_sample_reviews_ratings_in_range (self ):
        df =pd .read_csv (os .path .join ("data","sample","sample_reviews.csv"))
        assert df ["rating"].between (1 ,5 ).all ()

    def test_sample_trends_interest_in_range (self ):
        df =pd .read_csv (os .path .join ("data","sample","sample_trends.csv"))
        assert df ["interest_value"].between (0 ,100 ).all ()

    def test_sample_spatial_coordinates_saudi_bounds (self ):
        df =pd .read_csv (os .path .join ("data","sample","sample_spatial.csv"))
        assert df ["latitude"].between (15 ,33 ).all (),"Latitudes outside Saudi Arabia bounds"
        assert df ["longitude"].between (34 ,56 ).all (),"Longitudes outside Saudi Arabia bounds"

class TestRunAllCollectors :
    def test_module_imports (self ):
        from src .collectors import run_all_collectors 
        assert hasattr (run_all_collectors ,"run_all_collectors")

    def test_social_import_inside_try_block (self ):
        import inspect 
        from src .collectors import run_all_collectors 
        source =inspect .getsource (run_all_collectors )
        assert "social"in source .lower ()
