# tests/integration/test_end_to_end_trace.py
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "HEALTHY"
    assert data["service"] == "crypto-investigation-copilot"

def test_vertical_slice_api_flow():
    # 1. Create Case
    case_payload = {
        "title": "Operation Integration Test",
        "investigator": "Test Officer",
        "suspect_wallet": "0x71C83e20e8F468a3E282241F8C936f4521487439",
        "chain": "ETH",
        "priority": "HIGH"
    }
    c_res = client.post("/api/cases", json=case_payload)
    assert c_res.status_code == 200
    case_data = c_res.json()
    case_id = case_data["case_id"]

    # 2. Start Trace
    t_res = client.post(f"/api/cases/{case_id}/trace")
    assert t_res.status_code == 200
    assert t_res.json()["status"] == "COMPLETED"

    # 3. Retrieve Graph
    g_res = client.get(f"/api/cases/{case_id}/graph")
    assert g_res.status_code == 200
    g_data = g_res.json()
    assert g_data["total_nodes"] > 0
    assert g_data["total_edges"] > 0

    # 4. Retrieve Attribution
    a_res = client.get(f"/api/cases/{case_id}/attribution")
    assert a_res.status_code == 200
    a_data = a_res.json()
    assert a_data["top_candidate"] is not None
    assert a_data["top_candidate"]["entity_name"] == "Binance"

    # 5. Retrieve Explanation
    e_res = client.get(f"/api/cases/{case_id}/attribution/explanation")
    assert e_res.status_code == 200
    assert len(e_res.json()["evidence_factors"]) > 0

    # 6. Retrieve Counterfactual
    cf_res = client.get(f"/api/cases/{case_id}/attribution/counterfactual")
    assert cf_res.status_code == 200
    assert len(cf_res.json()["counterfactual_simulations"]) > 0

    # 7. Generate Forensic Report
    r_res = client.post(f"/api/cases/{case_id}/report")
    assert r_res.status_code == 200
    assert "report_hash" in r_res.json()

    # 8. Generate Lawful Action Packet
    act_res = client.post(f"/api/cases/{case_id}/action-packet")
    assert act_res.status_code == 200
    act_data = act_res.json()
    assert act_data["attributed_vasp"] == "Binance"
    assert "SECTION 91 CRPC" in act_data["preservation_notice_draft"].upper()
