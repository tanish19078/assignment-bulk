"""Unit tests for PractiGen backend helper functions.

Pure Python — no Flask, no network, no API keys. Fast.
Run: pytest tests/test_utils.py -v
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

import app


# --- Bug 1: Response parsing / validation -----------------------------------
def test_extract_section_valid_tags():
    text = "[CONCEPT]\nA concept.\n[CODE]\nprint(1)\n[OUTPUT]\n1\n[CAPTION]\nHello"
    assert app.extract_section("CONCEPT", text) == "A concept."
    assert app.extract_section("CODE", text) == "print(1)"
    assert app.extract_section("CAPTION", text) == "Hello"


def test_extract_section_missing_tag_returns_none():
    text = "[CONCEPT]\nonly concept here"
    assert app.extract_section("CODE", text) is None


def test_extract_section_malformed_response():
    # LLM used markdown headers instead of [TAG]; fallback pattern should still catch CODE.
    text = "CONCEPT:\nSome theory\n\nCODE:\ndef f():\n    return 2\n\nOUTPUT:\n2\n"
    assert app.extract_section("CODE", text) is not None
    assert "def f" in app.extract_section("CODE", text)


def test_validate_response_rejects_too_short_code():
    with pytest.raises(ValueError):
        app.validate_generation_result("general", "x = 1", "A valid concept.")


def test_validate_response_accepts_valid_code():
    # Should not raise.
    app.validate_generation_result(
        "general",
        "def bubble_sort(a):\n    return sorted(a)\n",
        "Sorting concept.",
    )


def test_validate_response_os_mode_skips_code_length():
    # OS mode has no [CODE]; only concept is required.
    app.validate_generation_result("os", "", "OS theory present.")


# --- Bug 5: Language validation ---------------------------------------------
def test_validate_code_language_python_correct():
    code = "import sys\n\ndef main():\n    print('hi')\n"
    assert app.validate_code_language(code, "python") is True


def test_validate_code_language_python_wrong():
    code = "#include <stdio.h>\nint main(){ printf(\"hi\"); return 0; }"
    assert app.validate_code_language(code, "python") is False


def test_validate_code_language_c_correct():
    code = "#include <stdio.h>\nint main(){ printf(\"hi\\n\"); return 0; }"
    assert app.validate_code_language(code, "c") is True


def test_validate_code_language_java_correct():
    code = "public class Main { public static void main(String[] a){ System.out.println(1);} }"
    assert app.validate_code_language(code, "java") is True


def test_validate_code_language_unknown_skips():
    assert app.validate_code_language("fn main() {}", "rust") is True


def test_validate_code_language_empty_is_false():
    assert app.validate_code_language("", "python") is False


# --- OS mode step parsing ----------------------------------------------------
def test_parse_steps_standard_format():
    text = (
        "Step 1: List files\n$ ls -la\nOutput:\nstudent@kali:~$ ls -la\ntotal 4\n\n"
        "Step 2: Print working dir\n$ pwd\nOutput:\nstudent@kali:~$ pwd\n/home/student\n"
    )
    steps = app.parse_steps(text)
    assert len(steps) == 2
    assert steps[0]["num"] == 1
    assert "List files" in steps[0]["explanation"]
    assert "total 4" in steps[0]["output"]


def test_parse_steps_numbered_list_format():
    text = "1. Do the first thing\n$ echo a\nOutput:\na\n\n2. Do the second\n$ echo b\nOutput:\nb\n"
    steps = app.parse_steps(text)
    assert len(steps) == 2
    assert steps[1]["num"] == 2


def test_parse_steps_empty_returns_fallback():
    steps = app.parse_steps("no recognizable steps here")
    assert len(steps) == 1
    assert steps[0]["num"] == 1


def test_parse_steps_multiline_code():
    text = (
        "Step 1: Write the program\n"
        "#include <stdio.h>\nint main(){\n  printf(\"x\");\n  return 0;\n}\n"
        "Output:\nstudent@kali:~$ gcc a.c\n"
    )
    steps = app.parse_steps(text)
    assert steps[0]["command"].count("\n") >= 2


# --- Caption helpers ---------------------------------------------------------
def test_make_step_caption_known_command():
    assert app.make_step_caption("ls -la") == "Directory Listing Output"


def test_make_step_caption_program_execution():
    assert app.make_step_caption("./a.out") == "Program Execution Output"


def test_make_caption_text_strips_step_prefix():
    assert app.make_caption_text("Step 3: Check permissions") == "Check permissions"


# --- Download payload helpers -----------------------------------------------
def test_get_terminal_lines_truncates_long_output():
    text = "\n".join(str(i) for i in range(100))
    lines = app.get_terminal_lines(text, max_lines=10)
    assert any("shortened" in ln.lower() for ln in lines)
    assert len(lines) <= 12


def test_get_terminal_lines_truncates_wide_lines():
    text = "x" * 500
    lines = app.get_terminal_lines(text, max_line_chars=50)
    assert lines[0].endswith("...")
    assert len(lines[0]) <= 50


def test_count_output_units_os_steps():
    experiments = [
        {"steps": [{}, {}, {}]},
        {"steps": []},      # min 1
        {"steps": [{}, {}]},
    ]
    assert app.count_output_units(experiments) == 3 + 1 + 2


# --- Auto-detect mode (Phase 3) ---------------------------------------------
def test_auto_detect_os_mode():
    d = app.detect_mode_and_language("Explore ls, cat, grep commands in Linux")
    assert d["mode"] == "os"


def test_auto_detect_general_mode_with_language():
    d = app.detect_mode_and_language("Write a Python program for binary search")
    assert d["mode"] == "general"
    assert d["code_language"] == "python"


def test_auto_detect_shell_script_is_os():
    d = app.detect_mode_and_language("Write a shell script to calculate factorial")
    assert d["mode"] == "os"


def test_auto_detect_ambiguous_defaults_general():
    d = app.detect_mode_and_language("Implement a sorting algorithm")
    assert d["mode"] == "general"
    assert d["code_language"] is None


def test_auto_detect_java():
    d = app.detect_mode_and_language("Implement a linked list in Java")
    assert d["mode"] == "general"
    assert d["code_language"] == "java"


# --- Message builder (Bug 2 / Enh 2 / Bug 5) --------------------------------
def test_build_messages_has_system_and_user():
    msgs = app.build_messages("general", "Sort an array", "python")
    assert len(msgs) == 2
    assert msgs[0]["role"] == "system"
    assert msgs[1]["role"] == "user"


def test_build_messages_language_lock_in_system():
    msgs = app.build_messages("general", "Write a C program", "python")
    assert "python" in msgs[0]["content"].lower()


def test_build_messages_variation_seed_injected():
    msgs = app.build_messages("general", "Sort", "python", variation_seed="ab12cd")
    assert "ab12cd" in msgs[1]["content"]


def test_build_messages_no_seed_no_injection():
    msgs = app.build_messages("general", "Sort", "python")
    assert "Variation reference" not in msgs[1]["content"]
