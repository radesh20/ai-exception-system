import os, sys, json
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from store import get_store

POLICIES = [
    {"category":"payment_mismatch","action_type":"three_way_match_recheck","action_params":{},"success_rate":0.89,"avg_resolution_time":30,"sample_size":45},
    {"category":"quantity_mismatch","action_type":"adjust_quantity","action_params":{},"success_rate":0.92,"avg_resolution_time":15,"sample_size":60},
    {"category":"invoice_mismatch","action_type":"request_invoice_correction","action_params":{},"success_rate":0.78,"avg_resolution_time":120,"sample_size":38},
    {"category":"goods_receipt_mismatch","action_type":"reverse_and_repost_gr","action_params":{},"success_rate":0.85,"avg_resolution_time":45,"sample_size":32},
    {"category":"tax_code_change","action_type":"update_tax_code","action_params":{},"success_rate":0.95,"avg_resolution_time":10,"sample_size":50},
    {"category":"novel_exception","action_type":"escalate_to_human","action_params":{},"success_rate":1.0,"avg_resolution_time":240,"sample_size":15},
]

HISTORICAL = [
    {"id":f"h{i:03d}","case_id":f"PO-2023-{i:04d}","exception_type":t,"actual_path":p,"deviation_point":d,"financial_exposure":f,"recommended_action":a,"was_approved":True}
    for i,(t,p,d,f,a) in enumerate([
        ("payment_mismatch",["PO Created","GR Posted","Invoice Received","Payment Blocked"],"Payment Blocked",82000,"three_way_match_recheck"),
        ("payment_mismatch",["PO Created","GR Posted","Invoice Received","Payment Blocked"],"Payment Blocked",91000,"three_way_match_recheck"),
        ("payment_mismatch",["PO Created","Invoice Received","GR Posted","Payment Blocked"],"Invoice Received",77000,"three_way_match_recheck"),
        ("payment_mismatch",["PO Created","GR Posted","Invoice Received","Payment Blocked"],"Payment Blocked",95000,"three_way_match_recheck"),
        ("payment_mismatch",["PO Created","GR Posted","Invoice Received","Payment Blocked","Manual Review"],"Payment Blocked",88000,"three_way_match_recheck"),
        ("payment_mismatch",["PO Created","GR Posted","Invoice Received","Payment Blocked"],"Payment Blocked",79000,"three_way_match_recheck"),
        ("quantity_mismatch",["PO Created","GR Posted","Quantity Discrepancy","Invoice Received"],"Quantity Discrepancy",12000,"adjust_quantity"),
        ("quantity_mismatch",["PO Created","GR Posted","Quantity Discrepancy","Manual Count"],"Quantity Discrepancy",8500,"adjust_quantity"),
        ("quantity_mismatch",["PO Created","GR Posted","Quantity Discrepancy"],"Quantity Discrepancy",15000,"adjust_quantity"),
        ("quantity_mismatch",["PO Created","GR Posted","Quantity Discrepancy","Invoice Received"],"Quantity Discrepancy",11000,"adjust_quantity"),
        ("quantity_mismatch",["PO Created","GR Posted","Quantity Discrepancy"],"Quantity Discrepancy",9800,"adjust_quantity"),
        ("invoice_mismatch",["PO Created","GR Posted","Invoice Received","Invoice Mismatch"],"Invoice Mismatch",45000,"request_invoice_correction"),
        ("invoice_mismatch",["PO Created","GR Posted","Invoice Received","Invoice Mismatch","Vendor Contacted"],"Invoice Mismatch",52000,"request_invoice_correction"),
        ("goods_receipt_mismatch",["PO Created","GR Posted","GR Mismatch","Invoice Received"],"GR Mismatch",27000,"reverse_and_repost_gr"),
        ("goods_receipt_mismatch",["PO Created","GR Posted","GR Mismatch"],"GR Mismatch",33000,"reverse_and_repost_gr"),
        ("tax_code_change",["PO Created","GR Posted","Invoice Received","Tax Code Changed"],"Tax Code Changed",5000,"update_tax_code"),
        ("tax_code_change",["PO Created","Invoice Received","Tax Code Changed"],"Tax Code Changed",7200,"update_tax_code"),
    ], 1)
]

def seed():
    store = get_store()
    print("🌱 Seeding...")
    for p in POLICIES: store.save_policy(p)
    print(f"  ✅ {len(POLICIES)} policies")
    for c in HISTORICAL: store.save_historical_case(c)
    print(f"  ✅ {len(HISTORICAL)} historical cases")
    print("✅ Done!")

if __name__ == "__main__":
    seed()