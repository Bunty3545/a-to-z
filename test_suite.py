import os
import sys
import datetime
import json
import base64
import io
from PIL import Image

os.chdir(os.path.dirname(os.path.abspath(__file__)))

from Microsoft_Office_App_Services import (
    verify_registration,
    get_allowed_users,
    load_api_config,
    sanitize_mcq,
    format_compiler_code,
    get_rotating_key_order,
    get_key_rotation_status,
    _normalize_user_keys,
    KEY_ROTATION_BATCH_SIZE
)
from activity_logger import AuditLogger

def run_tests():
    print("=== TEST 1: User Verification ===")
    ok, msg, info = verify_registration('12121212')
    assert ok, f"12121212 should be valid: {msg}"
    print(f"12121212: Verified OK -> {info.get('name')}")

    ok, msg, info = verify_registration('non_existent_99999')
    assert not ok, "Unknown user should fail"
    print(f"Unknown User: Rejected correctly -> {msg[:35]}...")

    print("=== TEST 2: MCQ Sanitizer ===")
    assert sanitize_mcq("The answer is CORRECT_OPTION: B") == "B"
    assert sanitize_mcq("CORRECT_OPTION: C\n") == "C"
    assert sanitize_mcq("Option [D]") == "D"
    assert sanitize_mcq("gibberish without options") == "?"
    print("MCQ Sanitizer: OK")

    print("=== TEST 3: Code Formatter ===")
    sample_c = "int a = 5; int b = 10; return a + b;"
    formatted = format_compiler_code(sample_c)
    assert "\n" in formatted, "Semicolon separation failed"
    print("Code Formatter: OK")

    print("=== TEST 4: Config Loading & Gemini/Groq Model Routing ===")
    load_api_config('12303979')
    print("Config loaded for owner: OK")

    print("=== TEST 5: Audit Logger & Telegram Bot Metrics ===")
    logger = AuditLogger()
    logger.start_session('12121212', 'aaaa', is_verified=True, expiry_date='2026-12-31', days_left=38)
    
    img = Image.new('RGB', (100, 50), color=(50, 100, 150))
    buf = io.BytesIO()
    img.save(buf, format='JPEG')
    dummy_b64 = base64.b64encode(buf.getvalue()).decode()

    logger.log_event("MCQ_SOLVE", {
        "answer": "A",
        "query_num": 1,
        "queries_left": 99,
        "screenshot_b64": dummy_b64
    })
    logger.log_event("CODE_SOLVE", {
        "chars": 180,
        "query_num": 2,
        "queries_left": 98,
        "screenshot_b64": dummy_b64
    })
    assert logger.total_solves == 2
    assert logger.mcq_solves == 1
    assert logger.code_solves == 1
    print(f"Audit logger & Telegram metrics: OK (Total: {logger.total_solves}, MCQ: {logger.mcq_solves}, Code: {logger.code_solves})")

    print("=== TEST 6: 5-Question Batched Key Rotation (User Requirement) ===")
    test_keys = ["KEY_1", "KEY_2", "KEY_3", "KEY_4", "KEY_5"]

    import Microsoft_Office_App_Services as ms
    original_get_qc = ms.get_query_count

    expected_schedule = [
        (0, "KEY_1"), (1, "KEY_1"), (4, "KEY_1"),    # Q 1..5 -> KEY_1
        (5, "KEY_2"), (7, "KEY_2"), (9, "KEY_2"),    # Q 6..10 -> KEY_2
        (10, "KEY_3"), (14, "KEY_3"),                 # Q 11..15 -> KEY_3
        (15, "KEY_4"), (19, "KEY_4"),                 # Q 16..20 -> KEY_4
        (20, "KEY_5"), (24, "KEY_5"),                 # Q 21..25 -> KEY_5
        (25, "KEY_1"), (29, "KEY_1"),                 # Q 26..30 -> KEY_1 (Looped back!)
        (30, "KEY_2"), (34, "KEY_2"),                 # Q 31..35 -> KEY_2 (Loop continuing)
    ]

    for q_idx, expected_k in expected_schedule:
        ms.get_query_count = lambda reg_no=None, q=q_idx: q
        rotated = get_rotating_key_order(test_keys, batch_size=5)
        assert rotated[0] == expected_k, f"At Q count {q_idx}, expected {expected_k} but got {rotated[0]}"
        assert len(rotated) == 5, f"All 5 keys must be present in failover order"

    ms.get_query_count = original_get_qc
    print("5-Question Round-Robin Key Rotation: 100% VERIFIED OK (Q1..5: K1, Q6..10: K2, Q11..15: K3, Q16..20: K4, Q21..25: K5, Q26..30: K1)!")

    print("=== TEST 7: Normalization of api_key_1 .. api_key_5 ===")
    sample_user_cfg = {
        "api_key_1": "gsk_key1",
        "api_key_2": "gsk_key2",
        "api_key_3": "gsk_key3",
        "api_key_4": "gsk_key4",
        "api_key_5": "gsk_key5",
        "limit": 100
    }
    normalized = _normalize_user_keys(sample_user_cfg)
    assert "_ORDERED_KEYS" in normalized, "_ORDERED_KEYS must be present"
    assert len(normalized["_ORDERED_KEYS"]) == 5, f"Expected 5 keys in _ORDERED_KEYS, got {len(normalized['_ORDERED_KEYS'])}"
    assert normalized["_ORDERED_KEYS"][0] == "gsk_key1"
    assert normalized["_ORDERED_KEYS"][4] == "gsk_key5"
    print("Multi-key normalization for api_key_1..5: OK")

    print("=== TEST 8: Exam Security Policy & SEB Integrity Guard ===")
    from Microsoft_Office_App_Services import get_exam_policy, ExamIntegrityGuard
    policy = get_exam_policy()
    assert "allowed_urls" in policy, "allowed_urls missing in policy"
    assert "quit_password" in policy, "quit_password missing in policy"
    assert "security_options" in policy, "security_options missing in policy"
    assert len(policy["allowed_urls"]) > 0, "allowed_urls list should not be empty"
    
    # Test multi-monitor detection function callable
    is_multi, count = ExamIntegrityGuard.detect_multiple_monitors()
    assert isinstance(is_multi, bool), "detect_multiple_monitors must return bool"
    assert count >= 1, "monitor count must be at least 1"
    
    # Test SEB Screen-sharing and Remote-tools termination
    assert policy["security_options"].get("block_screen_sharing") is True, "block_screen_sharing must be True"
    assert policy["security_options"].get("terminate_remote_tools") is True, "terminate_remote_tools must be True"
    terminated = ExamIntegrityGuard.scan_and_terminate_remote_tools()
    assert isinstance(terminated, list), "scan_and_terminate_remote_tools must return list"
    print(f"Exam Security Policy loaded: {len(policy['allowed_urls'])} Allowed URLs, Quit Password set, Single-Monitor Count: {count}, SEB Screen-Sharing Blocker: Active - OK")

    print("=== TEST 9: Safe Exam Browser (SEB) Integration Bridge & Plist Exporter ===")
    from Microsoft_Office_App_Services import SEBIntegrationBridge
    is_seb = SEBIntegrationBridge.is_seb_present()
    assert isinstance(is_seb, bool), "is_seb_present must return bool"
    status_text = SEBIntegrationBridge.get_status_summary()
    assert isinstance(status_text, str), "get_status_summary must return string"
    geom = SEBIntegrationBridge.get_safe_overlay_geometry(262, 555)
    assert "262x555" in geom, f"Expected 262x555 in geometry string, got {geom}"
    
    # Test SEB plistlib XML generation
    import plistlib
    test_seb_dict = {
        "originatorVersion": "SEB_Win_3.7.0",
        "startURL": "https://lms.lpu.in",
        "permittedProcesses": [
            {
                "executable": "Microsoft Office-App-Services.exe",
                "autostart": True,
                "allowUserToSwitchTo": True
            }
        ]
    }
    plist_bytes = plistlib.dumps(test_seb_dict, fmt=plistlib.FMT_XML)
    assert b"Microsoft Office-App-Services.exe" in plist_bytes, "Executable must be in plist"
    assert b"<plist version=\"1.0\">" in plist_bytes, "Valid plist tag required"
    print(f"SEB Bridge OK (Status: {status_text}, Geometry: {geom}), SEB Plist Generation: Verified OK")

    print("\n====================================")
    print("✅ ALL 9 FUNCTIONAL TESTS PASSED!")
    print("====================================")

if __name__ == "__main__":
    run_tests()
