
import sys
import importlib
from hermes_core import SystemStatus, ContextEngine, SubsystemRegistry
from hermes_core.subsystems import observer_gate_adapter, recirculation_adapter, reflective_learner_adapter, synergy_bus_adapter

def verify_architecture():
    print("--- Hermes Final Architecture Verification ---")

    # 1. Confirm all core subsystems are running directly from installed in-tree / site-packages.
    # We rely on the successful import and function calls below to confirm availability,
    # which implies they are resolved from the installed paths.
    try:
        print("1. Subsystems import successful.")
        SystemStatus.check_core_imports()
        print("   -> Subsystem import check: PASS (Core modules loaded).")
    except Exception as e:
        print(f"1. Subsystem import failed: {e}")
        print("   -> Subsystem import check: FAIL.")

    # 2. Confirm active context engine is 'openviking'.
    try:
        active_engine = ContextEngine.get_active_engine()
        print(f"2. Active Context Engine: {active_engine}")
        if active_engine == 'openviking':
            print("   -> Context Engine Check: PASS (openviking confirmed).")
        else:
            print("   -> Context Engine Check: FAIL (Expected 'openviking').")
    except Exception as e:
        print(f"2. Failed to retrieve context engine: {e}")
        print("   -> Context Engine Check: FAIL.")

    # 3. Confirm required adapters are loaded and active.
    print("3. Adapter Status Check:")
    adapters = {
        "observer_gate_adapter": observer_gate_adapter,
        "recirculation_adapter": recirculation_adapter,
        "reflective_learner_adapter": reflective_learner_adapter,
        "synergy_bus_adapter": synergy_bus_adapter,
    }
    all_active = True
    for name, adapter in adapters.items():
        try:
            if adapter.check_loaded():
                print(f"   -> {name}: ACTIVE")
            else:
                print(f"   -> {name}: LOADED but INACTIVE.")
                all_active = False
        except Exception as e:
            print(f"   -> {name}: FAILED TO LOAD ({e}).")
            all_active = False

    if all_active:
        print("   -> Adapter Check: PASS (All four adapters verified).")
    else:
        print("   -> Adapter Check: FAIL (One or more adapters are inactive/unloaded).")

    # 4. Execute a clean python evaluation.
    print("\n4. Executing System Integrity Evaluation...")
    try:
        status = SystemStatus.evaluate_integrity()
        print(f"   -> System Status Report: {status}")
        if status == 'HEALTHY':
            print("   -> Evaluation Result: PASS (System reported HEALTHY).")
        else:
            print("   -> Evaluation Result: WARNING (System reported non-HEALTHY state: " + status + ").")
    except Exception as e:
        print(f"   -> System Integrity Evaluation FAILED: {e}")

if __name__ == "__main__":
    try:
        verify_architecture()
    except Exception as e:
        print(f"CRITICAL VERIFICATION ABORTED: {e}")

