import os 
import sys 
import pandas as pd 
import numpy as np 
import pytest 

sys .path .insert (0 ,os .path .join (os .path .dirname (__file__ ),".."))

class TestCompositeIndex :
    def test_min_max_scale_constant_series (self ):
        from src .models .composite_index import min_max_scale 

        result =min_max_scale (pd .Series ([5.0 ,5.0 ,5.0 ]))
        assert result .equals (pd .Series ([50.0 ,50.0 ,50.0 ]))

    def test_min_max_scale_normal (self ):
        from src .models .composite_index import min_max_scale 
        result =min_max_scale (pd .Series ([0.0 ,50.0 ,100.0 ]))
        assert float (result .iloc [0 ])==pytest .approx (0.0 )
        assert float (result .iloc [2 ])==pytest .approx (100.0 )

    def test_bootstrap_confidence_len_less_than_2 (self ):
        from src .models .composite_index import bootstrap_confidence 
        lower ,upper =bootstrap_confidence ([42.0 ])
        assert lower ==pytest .approx (37.0 )
        assert upper ==pytest .approx (47.0 )

    def test_bootstrap_confidence_normal (self ):
        from src .models .composite_index import bootstrap_confidence 
        np .random .seed (42 )
        values =list (np .random .uniform (45 ,55 ,20 ))
        lower ,upper =bootstrap_confidence (values ,n_samples =100 )
        assert lower <=upper 
        assert 30 <=lower <=70 
        assert 30 <=upper <=70 

    def test_compute_composite_index_returns_dataframe (self ):
        from src .models .composite_index import compute_composite_index 
        df =compute_composite_index ()
        assert isinstance (df ,pd .DataFrame )
        assert not df .empty 

    def test_compute_composite_index_has_national_rows (self ):
        from src .models .composite_index import compute_composite_index 
        df =compute_composite_index ()
        assert "الكل"in df ["city"].values 

    def test_compute_composite_index_no_nan_index (self ):
        from src .models .composite_index import compute_composite_index 
        df =compute_composite_index ()
        assert df ["index_value"].notna ().all ()

    def test_compute_composite_index_ci_vary (self ):
        from src .models .composite_index import compute_composite_index 
        df =compute_composite_index ()
        national =df [df ["city"]=="الكل"]
        unique_ci =national ["confidence_lower"].nunique ()
        assert unique_ci >1 ,f"CI values don't vary — only {unique_ci } unique value"

    def test_spatial_rows_have_ci (self ):
        from src .models .composite_index import compute_composite_index 
        df =compute_composite_index ()
        spatial =df [df ["city"]!="الكل"]
        if not spatial .empty :
            assert spatial ["confidence_lower"].notna ().all ()
            assert spatial ["confidence_upper"].notna ().all ()

    def test_gap_analysis_returns_dataframe (self ):
        from src .models .composite_index import compute_gap_analysis 
        df =compute_gap_analysis ()
        assert isinstance (df ,pd .DataFrame )
        assert not df .empty 
        assert "gap"in df .columns 

    def test_gap_analysis_has_estimated_workers (self ):
        from src .models .composite_index import compute_gap_analysis 
        df =compute_gap_analysis ()
        assert "estimated_workers"in df .columns 
        assert (df ["estimated_workers"]>0 ).all ()

class TestNormalizer :
    def test_normalize_city_riyadh (self ):
        from src .processing .normalizer import normalize_city 
        result =normalize_city ("الرياض")
        assert result ["city_en"]=="Riyadh"
        assert result ["city_ar"]!=""

    def test_normalize_city_jeddah_en (self ):
        from src .processing .normalizer import normalize_city 
        result =normalize_city ("jeddah")
        assert result ["city_en"]=="Jeddah"

    def test_normalize_city_empty_input (self ):
        from src .processing .normalizer import normalize_city 
        result =normalize_city ("")
        assert result =={"city_en":"","city_ar":""}

    def test_normalize_city_none_input (self ):
        from src .processing .normalizer import normalize_city 
        result =normalize_city (None )
        assert result =={"city_en":"","city_ar":""}

    def test_normalize_date_iso (self ):
        from src .processing .normalizer import normalize_date 
        result =normalize_date ("2025-06-15")
        assert "2025-06-15"in result 

    def test_normalize_date_empty (self ):
        from src .processing .normalizer import normalize_date 
        result =normalize_date ("")
        assert result ==""

class TestValidator :
    def test_validate_spatial_saudi_bounds (self ):
        from src .processing .validator import DataValidator 
        import pandas as pd 
        df =pd .DataFrame ({
        "latitude":[24.7 ,1000.0 ],
        "longitude":[46.7 ,200.0 ],
        "activity_score":[80.0 ,50.0 ],
        })
        v =DataValidator ()
        result =v .validate_spatial (df )
        assert result ["valid"]<result ["total"]

    def test_validate_reviews_bad_rating (self ):
        from src .processing .validator import DataValidator 
        import pandas as pd 
        df =pd .DataFrame ({
        "text":["good service","bad experience"],
        "rating":[4.0 ,99.0 ],
        })
        v =DataValidator ()
        result =v .validate_reviews (df )
        assert result ["valid"]<result ["total"]

class TestProphetForecast :
    def test_run_simple_forecast_success (self ):
        from src .models .prophet_forecast import run_simple_forecast 
        ts_data =pd .DataFrame ({
        "ds":pd .date_range ("2025-01-01",periods =30 ,freq ="W"),
        "y":np .random .uniform (40 ,80 ,30 ),
        })
        result =run_simple_forecast (ts_data ,periods =30 )
        assert result ["success"]is True 
        assert "forecasts"in result 

    def test_forecast_output_file_created (self ):
        from src .models .prophet_forecast import run_simple_forecast 
        ts_data =pd .DataFrame ({
        "ds":pd .date_range ("2025-01-01",periods =12 ,freq ="ME"),
        "y":np .linspace (40 ,70 ,12 ),
        })
        run_simple_forecast (ts_data ,periods =14 )
        assert os .path .exists (os .path .join ("data","processed","forecast_results.csv"))

class TestSpatialDBSCAN :
    def test_assign_labels_simple (self ):
        from src .models .spatial_dbscan import assign_labels_simple 
        df =pd .DataFrame ({
        "city":["Riyadh","Jazan"],
        "activity_score":[90.0 ,15.0 ],
        })
        result =assign_labels_simple (df )
        assert "cluster_label"in result .columns 
        assert result .iloc [0 ]["cluster_label"]=="نشاط_عالي"
        assert result .iloc [1 ]["cluster_label"]=="نشاط_منخفض"

    def test_empty_dataframe_returns_empty (self ):
        from src .models .spatial_dbscan import assign_labels_simple 
        result =assign_labels_simple (pd .DataFrame ())
        assert result .empty
