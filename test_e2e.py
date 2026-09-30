import json
from core.repair_engine import RepairEngine, RepairState

engine = RepairEngine()

print("Executing Flush DNS Cache...")
result = engine.execute_repair("flush_dns")

print("Execute Result:")
print(json.dumps(result, indent=2))

if result["state"] == RepairState.EXECUTED:
    print("Verifying...")
    is_verified = engine.verify_repair("flush_dns")
    print(f"Verified: {is_verified}")
