import pytest
import json
from app.analytics.lake.manager import DataLakeManager, DataLayer
from app.analytics.lake.warehouse import AnalyticsWarehouse, FactRecord
from app.analytics.engines.kpi import KPIEngine
from app.analytics.engines.advanced import AdvancedAnalyticsEngine
from app.analytics.engines.fraud import FraudAnalyticsEngine
from app.analytics.engines.prediction import PredictionEngine
from app.analytics.bi.dashboard import DashboardEngine
from app.analytics.bi.reports import ReportEngine
from app.analytics.bi.quality import DataQualityEngine


# ─────────────────────────────────────────────────────
# 1. Data Lake Manager
# ─────────────────────────────────────────────────────

def test_data_lake_ingest_raw():
    DataLakeManager._clear_all()
    rec = DataLakeManager.ingest_raw("t1", "claim", {"id": "C01", "raw": "text"})
    assert rec.tenant_id == "t1"
    assert rec.layer == DataLayer.BRONZE
    assert len(DataLakeManager.query(DataLayer.BRONZE)) == 1


def test_data_lake_promote_to_silver():
    DataLakeManager._clear_all()
    bronze = DataLakeManager.ingest_raw("t1", "claim", {"id": "C01", "raw": "text"})
    silver = DataLakeManager.promote_to_silver(bronze, {"id": "C01", "clean": True})
    
    assert silver.layer == DataLayer.SILVER
    assert silver.source_type == bronze.source_type
    assert len(DataLakeManager.query(DataLayer.SILVER)) == 1


def test_data_lake_promote_to_gold():
    DataLakeManager._clear_all()
    gold = DataLakeManager.promote_to_gold("t1", "claim_stats", {"count": 1})
    assert gold.layer == DataLayer.GOLD
    assert gold.data["count"] == 1


def test_data_lake_query_filters():
    DataLakeManager._clear_all()
    DataLakeManager.ingest_raw("t1", "claim", {})
    DataLakeManager.ingest_raw("t2", "document", {})
    DataLakeManager.ingest_raw("t2", "claim", {})
    
    assert len(DataLakeManager.query(DataLayer.BRONZE, tenant_id="t2")) == 2
    assert len(DataLakeManager.query(DataLayer.BRONZE, source_type="claim")) == 2
    assert len(DataLakeManager.query(DataLayer.BRONZE, tenant_id="t2", source_type="document")) == 1


# ─────────────────────────────────────────────────────
# 2. Analytics Warehouse
# ─────────────────────────────────────────────────────

def test_warehouse_insert_and_query_aggregate():
    AnalyticsWarehouse._clear_all()
    
    f1 = FactRecord(tenant_id="t1", fact_type="claims", dimensions={"region": "EU"}, measures={"total_claims": 10})
    f2 = FactRecord(tenant_id="t1", fact_type="claims", dimensions={"region": "US"}, measures={"total_claims": 5})
    f3 = FactRecord(tenant_id="t2", fact_type="claims", dimensions={"region": "EU"}, measures={"total_claims": 20})
    
    AnalyticsWarehouse.insert_fact(f1)
    AnalyticsWarehouse.insert_fact(f2)
    AnalyticsWarehouse.insert_fact(f3)
    
    agg_all = AnalyticsWarehouse.query_aggregate("t1", "claims")
    assert agg_all["total_claims"] == 15
    
    agg_filtered = AnalyticsWarehouse.query_aggregate("t1", "claims", {"region": "EU"})
    assert agg_filtered["total_claims"] == 10


def test_warehouse_get_raw_facts():
    AnalyticsWarehouse._clear_all()
    f = FactRecord(tenant_id="t1", fact_type="claims")
    AnalyticsWarehouse.insert_fact(f)
    
    facts = AnalyticsWarehouse.get_raw_facts("t1", "claims")
    assert len(facts) == 1
    assert facts[0].id == f.id


# ─────────────────────────────────────────────────────
# 3. KPI Engine
# ─────────────────────────────────────────────────────

def setup_kpi_facts():
    AnalyticsWarehouse._clear_all()
    AnalyticsWarehouse.insert_fact(FactRecord(tenant_id="kpi", fact_type="claims", measures={"total_claims": 100, "automated_claims": 65, "total_processing_time_sec": 500}))
    AnalyticsWarehouse.insert_fact(FactRecord(tenant_id="kpi", fact_type="ocr", measures={"total_fields": 1000, "correct_fields": 950}))
    AnalyticsWarehouse.insert_fact(FactRecord(tenant_id="kpi", fact_type="fraud_alerts", measures={"confirmed_frauds": 5}))


def test_kpi_automation_rate():
    setup_kpi_facts()
    assert KPIEngine.calculate_automation_rate("kpi") == 65.0


def test_kpi_automation_rate_zero():
    AnalyticsWarehouse._clear_all()
    assert KPIEngine.calculate_automation_rate("empty") == 0.0


def test_kpi_avg_processing_time():
    setup_kpi_facts()
    assert KPIEngine.calculate_average_processing_time("kpi") == 5.0


def test_kpi_ocr_accuracy():
    setup_kpi_facts()
    assert KPIEngine.calculate_ocr_accuracy("kpi") == 95.0


def test_kpi_fraud_rate():
    setup_kpi_facts()
    assert KPIEngine.calculate_fraud_rate("kpi") == 5.0


# ─────────────────────────────────────────────────────
# 4. Advanced Analytics Engine
# ─────────────────────────────────────────────────────

def test_advanced_anomalies_detection():
    AnalyticsWarehouse._clear_all()
    # Create 10 normal facts
    for _ in range(10):
        AnalyticsWarehouse.insert_fact(FactRecord(tenant_id="t1", fact_type="metric", measures={"val": 10}))
    # Create 1 anomaly fact
    AnalyticsWarehouse.insert_fact(FactRecord(tenant_id="t1", fact_type="metric", measures={"val": 100}))
    
    anomalies = AdvancedAnalyticsEngine.detect_anomalies("t1", "metric", "val")
    assert len(anomalies) == 1
    assert anomalies[0]["value"] == 100


def test_advanced_anomalies_no_facts():
    AnalyticsWarehouse._clear_all()
    assert AdvancedAnalyticsEngine.detect_anomalies("t1", "metric", "val") == []


def test_advanced_trends_up():
    AnalyticsWarehouse._clear_all()
    AnalyticsWarehouse.insert_fact(FactRecord(tenant_id="t1", fact_type="metric", measures={"val": 10}))
    AnalyticsWarehouse.insert_fact(FactRecord(tenant_id="t1", fact_type="metric", measures={"val": 20}))
    
    trend = AdvancedAnalyticsEngine.analyze_trends("t1", "metric", "val")
    assert trend["trend"] == "up"
    assert trend["change_pct"] == 100.0


def test_advanced_trends_down():
    AnalyticsWarehouse._clear_all()
    AnalyticsWarehouse.insert_fact(FactRecord(tenant_id="t1", fact_type="metric", measures={"val": 20}))
    AnalyticsWarehouse.insert_fact(FactRecord(tenant_id="t1", fact_type="metric", measures={"val": 10}))
    
    trend = AdvancedAnalyticsEngine.analyze_trends("t1", "metric", "val")
    assert trend["trend"] == "down"
    assert trend["change_pct"] == -50.0


def test_advanced_trends_zero_base():
    AnalyticsWarehouse._clear_all()
    AnalyticsWarehouse.insert_fact(FactRecord(tenant_id="t1", fact_type="metric", measures={"val": 0}))
    AnalyticsWarehouse.insert_fact(FactRecord(tenant_id="t1", fact_type="metric", measures={"val": 10}))
    
    trend = AdvancedAnalyticsEngine.analyze_trends("t1", "metric", "val")
    assert trend["trend"] == "up"
    assert trend["change_pct"] == 100.0


# ─────────────────────────────────────────────────────
# 5. Fraud Analytics Engine
# ─────────────────────────────────────────────────────

def test_fraud_heatmap():
    AnalyticsWarehouse._clear_all()
    AnalyticsWarehouse.insert_fact(FactRecord(tenant_id="t1", fact_type="fraud_alerts", dimensions={"region": "FR"}))
    AnalyticsWarehouse.insert_fact(FactRecord(tenant_id="t1", fact_type="fraud_alerts", dimensions={"region": "FR"}))
    AnalyticsWarehouse.insert_fact(FactRecord(tenant_id="t1", fact_type="fraud_alerts", dimensions={"region": "BE"}))
    
    hm = FraudAnalyticsEngine.generate_fraud_heatmap("t1")
    assert hm["FR"] == 66.67
    assert hm["BE"] == 33.33


def test_fraud_heatmap_empty():
    AnalyticsWarehouse._clear_all()
    assert FraudAnalyticsEngine.generate_fraud_heatmap("t1") == {}


def test_fraud_network():
    AnalyticsWarehouse._clear_all()
    # 3 claims on same bank account = network
    AnalyticsWarehouse.insert_fact(FactRecord(tenant_id="t1", fact_type="fraud_alerts", dimensions={"bank_account": "IBAN_123"}))
    AnalyticsWarehouse.insert_fact(FactRecord(tenant_id="t1", fact_type="fraud_alerts", dimensions={"bank_account": "IBAN_123"}))
    AnalyticsWarehouse.insert_fact(FactRecord(tenant_id="t1", fact_type="fraud_alerts", dimensions={"bank_account": "IBAN_123"}))
    # 1 claim on another = no network
    AnalyticsWarehouse.insert_fact(FactRecord(tenant_id="t1", fact_type="fraud_alerts", dimensions={"bank_account": "IBAN_999"}))
    
    nets = FraudAnalyticsEngine.detect_fraud_network("t1")
    assert len(nets) == 1
    assert nets[0]["bank_account"] == "IBAN_123"
    assert len(nets[0]["claims"]) == 3


# ─────────────────────────────────────────────────────
# 6. Prediction Engine
# ─────────────────────────────────────────────────────

def test_prediction_volume():
    AnalyticsWarehouse._clear_all()
    for _ in range(100):
        AnalyticsWarehouse.insert_fact(FactRecord(tenant_id="t1", fact_type="claims"))
        
    pred = PredictionEngine.forecast_volume("t1")
    assert pred["forecast"] == 105
    assert pred["confidence"] == 0.85


def test_prediction_volume_empty():
    AnalyticsWarehouse._clear_all()
    pred = PredictionEngine.forecast_volume("t1")
    assert pred["forecast"] == 0


def test_prediction_llm_costs():
    AnalyticsWarehouse._clear_all()
    AnalyticsWarehouse.insert_fact(FactRecord(tenant_id="t1", fact_type="llm_usage", measures={"cost": 100.0}))
    
    pred = PredictionEngine.forecast_llm_costs("t1")
    assert pred == 120.0


# ─────────────────────────────────────────────────────
# 7. Dashboard Engine
# ─────────────────────────────────────────────────────

def test_dashboard_generation():
    setup_kpi_facts()
    dash = DashboardEngine.get_executive_dashboard("kpi")
    
    assert dash["title"] == "Executive Dashboard"
    assert len(dash["widgets"]) == 4
    
    kpi_cards = [w for w in dash["widgets"] if w["type"] == "KPI_CARD"]
    assert len(kpi_cards) == 3


# ─────────────────────────────────────────────────────
# 8. Report Engine
# ─────────────────────────────────────────────────────

def test_report_json():
    res = ReportEngine.generate_report("t1", "operational", "json")
    data = json.loads(res)
    assert data["tenant"] == "t1"
    assert data["processed_claims"] == 150


def test_report_csv():
    res = ReportEngine.generate_report("t1", "operational", "csv")
    lines = res.split("\n")
    assert "tenant" in lines[0]
    assert "t1" in lines[1]


def test_report_markdown():
    res = ReportEngine.generate_report("t1", "fraud", "markdown")
    assert "# Fraud Report" in res
    assert "**tenant**: t1" in res


def test_report_unsupported_format():
    res = ReportEngine.generate_report("t1", "fraud", "xml")
    assert "Format xml not supported" in res


def test_data_lake_manager_clear_all():
    DataLakeManager.ingest_raw("t1", "claim", {"a": 1})
    DataLakeManager._clear_all()
    assert len(DataLakeManager.query(DataLayer.BRONZE)) == 0


def test_advanced_anomalies_empty_measure():
    AnalyticsWarehouse._clear_all()
    AnalyticsWarehouse.insert_fact(FactRecord(tenant_id="t1", fact_type="metric", measures={}))
    assert AdvancedAnalyticsEngine.detect_anomalies("t1", "metric", "val") == []


def test_advanced_trends_one_fact():
    AnalyticsWarehouse._clear_all()
    AnalyticsWarehouse.insert_fact(FactRecord(tenant_id="t1", fact_type="metric", measures={"val": 10}))
    trend = AdvancedAnalyticsEngine.analyze_trends("t1", "metric", "val")
    assert trend["trend"] == "neutral"


def test_fraud_heatmap_no_region_dimension():
    AnalyticsWarehouse._clear_all()
    AnalyticsWarehouse.insert_fact(FactRecord(tenant_id="t1", fact_type="fraud_alerts", dimensions={}))
    hm = FraudAnalyticsEngine.generate_fraud_heatmap("t1")
    assert hm["UNKNOWN"] == 100.0


def test_fraud_network_no_bank_dimension():
    AnalyticsWarehouse._clear_all()
    AnalyticsWarehouse.insert_fact(FactRecord(tenant_id="t1", fact_type="fraud_alerts", dimensions={}))
    AnalyticsWarehouse.insert_fact(FactRecord(tenant_id="t1", fact_type="fraud_alerts", dimensions={}))
    nets = FraudAnalyticsEngine.detect_fraud_network("t1")
    assert len(nets) == 0


def test_prediction_volume_small():
    AnalyticsWarehouse._clear_all()
    AnalyticsWarehouse.insert_fact(FactRecord(tenant_id="t1", fact_type="claims"))
    pred = PredictionEngine.forecast_volume("t1")
    assert pred["forecast"] == 1


def test_data_quality_missing_facts():
    AnalyticsWarehouse._clear_all()
    DataQualityEngine._clear_all()
    res = DataQualityEngine.run_checks("t_missing")
    assert res["total_records_checked"] == 0
    assert res["issues_found"] == 0
    assert res["quality_score"] == 100.0


# ─────────────────────────────────────────────────────
# 9. Data Quality Engine
# ─────────────────────────────────────────────────────

def test_data_quality_checks():
    AnalyticsWarehouse._clear_all()
    DataQualityEngine._clear_all()
    
    f1 = FactRecord(tenant_id="t1", fact_type="claims", dimensions={"ok": "yes"})
    # duplicate f1
    AnalyticsWarehouse.insert_fact(f1)
    AnalyticsWarehouse.insert_fact(f1)
    
    # f2 missing dimensions
    f2 = FactRecord(tenant_id="t1", fact_type="claims")
    AnalyticsWarehouse.insert_fact(f2)
    
    res = DataQualityEngine.run_checks("t1")
    
    assert res["total_records_checked"] == 3
    assert res["issues_found"] == 2  # 1 duplicate, 1 completeness
    
    issues = DataQualityEngine.get_issues("t1")
    assert len(issues) == 2


def test_data_quality_perfect_score():
    AnalyticsWarehouse._clear_all()
    DataQualityEngine._clear_all()
    AnalyticsWarehouse.insert_fact(FactRecord(tenant_id="t1", fact_type="claims", dimensions={"ok": "yes"}))
    
    res = DataQualityEngine.run_checks("t1")
    assert res["quality_score"] == 100.0


def test_data_quality_empty():
    AnalyticsWarehouse._clear_all()
    res = DataQualityEngine.run_checks("t1")
    assert res["quality_score"] == 100.0

# 37 tests target achieved.
