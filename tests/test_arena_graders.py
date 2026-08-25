#!/usr/bin/env python3
"""
Regression tests for the Edge Agent Arena graders (Cluster 09).
Validates the three fairness harness fixes:
  1. py_state grader (AB-01) — pass on correct solution, fail on wrong content
  2. _strip_reasoning_tags — removes <think>/<thought> blocks for reasoning models
  3. _extract_first_number — comma/currency tolerant

Run: python3 tests/test_arena_graders.py   (no GPU / no server needed)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import tests.arena_runner as AR  # noqa: E402
from tests.arena_runner import (  # noqa: E402
    _extract_first_number,
    _norm,
    _strip_fences,
    _strip_reasoning_tags,
    grade_task,
    load_tasks,
)
from tests.human_repeatability_eval import extract_code_block  # noqa: E402

# 0. tasks.json sanity: all 27 task ids unique, all grader types handled
all_tasks = [t for b in load_tasks()["benchmarks"] for t in b["tasks"]]
ids = [t["id"] for t in all_tasks]
assert len(ids) == len(set(ids)) == 27, f"task ids must be 27 unique, got {len(ids)}/{len(set(ids))}"
handled = {"bash_stdout", "bash_state", "py_import", "py_state", "py_stdout",
           "json_tool_call", "json_tool_call_array", "numeric", "exact_string"}
gtypes = {t["grader"]["type"] for t in all_tasks}
assert gtypes <= handled, f"unhandled grader types: {gtypes - handled}"
print(f"OK tasks.json: {len(ids)} unique task ids, {len(gtypes)} grader types handled")

# 1. think-strip
assert _strip_reasoning_tags("<think> blah </think> 255.255.255.192") == "255.255.255.192"
assert _strip_reasoning_tags("<thought>x</thought>def f(): pass") == "def f(): pass"
assert _strip_reasoning_tags("<think> </think> 255.255.255.192") == "255.255.255.192"
# stray unclosed tag: tag stripped, content preserved (no over-aggressive nuking)
assert _strip_reasoning_tags("<think>unclosed") == "unclosed"
print("OK think-strip")

# 2. comma/dollar numeric
assert _extract_first_number("1,476.00") == 1476.0
assert _extract_first_number("$1,240") == 1240.0
assert _extract_first_number(" 12.8 ") == 12.8
print("OK numeric extraction")

# 2b. fence stripping (follow-up-13): a ```text VALUE``` wrap is noise, not
#     content — AL-02 failed 4 attempts on exactly this shape.
al02 = [t for b in load_tasks()["benchmarks"] for t in b["tasks"] if t["id"] == "AL-02"][0]
assert _norm(_strip_fences("```text 255.255.255.192```")) == "255.255.255.192"
assert _norm(_strip_fences("```text\n255.255.255.192\n```")) == "255.255.255.192"
assert _norm(_strip_fences("255.255.255.192")) == "255.255.255.192"
# unclosed fences must keep the value (reviewer f14: a greedy [^\n]* ate it)
assert _norm(_strip_fences("```text 255.255.255.192")) == "255.255.255.192"
assert _norm(_strip_fences("```text\n255.255.255.192")) == "255.255.255.192"
p_fence, n_fence = grade_task(al02, "```text 255.255.255.192```")
print("AL-02 fenced ->", p_fence, n_fence)
assert p_fence, f"fenced AL-02 answer should pass after fence-strip: {n_fence}"
print("OK fence-strip")

# 2c. numeric fence-strip (S14-5): the numeric grader extracts the FIRST
#     number, so a bare ```text VALUE``` fence is already tolerated — but a
#     fence LANG-TAG with embedded digits (e.g. ```c99) would be grabbed as
#     the answer's first number (99). Stripping removes the marker; the
#     number inside the fence is what gets graded.
al03 = [t for b in load_tasks()["benchmarks"] for t in b["tasks"] if t["id"] == "AL-03"][0]
assert al03["grader"]["type"] == "numeric"
p_num, n_num = grade_task(al03, "```text\n1140.96\n```")
print("AL-03 fenced numeric ->", p_num, n_num)
assert p_num, f"fenced numeric answer should pass: {n_num}"
p_num2, n_num2 = grade_task(al03, "```c99\n1140.96\n```")
print("AL-03 c99-tag numeric ->", p_num2, n_num2)
assert p_num2, \
    f"digit-tagged fence must grade the value inside (was first-number 99): {n_num2}"
assert _extract_first_number(_strip_fences("```c99\n1140.96\n```")) == 1140.96
print("OK numeric fence-strip")

# 2d. py_stdout numeric path (DH-02): a program that PRINTS a fenced value
#     with a digit-ful lang tag must still grade the number inside the fence.
dh02 = [t for b in load_tasks()["benchmarks"] for t in b["tasks"] if t["id"] == "DH-02"][0]
assert dh02["grader"]["type"] == "py_stdout" and dh02["grader"]["mode"] == "numeric"
# a program that PRINTS an inline-fenced value with a digit-ful lang tag
# (```c99 70.0```) must still grade the number inside the fence. chr(96)
# is the backtick, so the raw answer has NO backticks that extract_code_block
# would mistake for a code fence around the script itself.
p_dh, n_dh = grade_task(dh02, "print(chr(96) * 3 + 'c99 70.0' + chr(96) * 3)")
print("DH-02 fenced stdout numeric ->", p_dh, n_dh)
assert p_dh, f"fenced stdout value must grade the number inside: {n_dh}"
print("OK py_stdout numeric fence-strip")

# 2e. TRUNCATED-OPEN-FENCE fallback (f31, RUN30 DH-02 code-truncation
#     class): a verbose script cut mid-fence (max_tokens hit — the closing
#     ``` never arrives) previously fell through to the raw-text fallback,
#     which wrote the LONE OPENING ```python marker into script.py → bogus
#     SyntaxError on line 1 that hid the real defect. extract_code_block must
#     now drop the lone opening fence so the PARTIAL code is what runs.
# truncated fenced answer: opening ```python + partial code, NO closing fence
_trunc = "```python\nimport csv\nrows = [float(r['revenue']) for r in csv.DictReader(open('sales_ts.csv'))]\n"
_code = extract_code_block(_trunc, "python")
assert _code.startswith("import csv"), f"lone opening fence must be dropped: {_code!r}"
assert "```" not in _code, f"no backticks may leak into the script: {_code!r}"
# bare (no fence at all) fallback unchanged — the common pass shape:
# strip-only, no backtick/prose mangling (extract_code_block has always
# stripped the extracted content — f32 corrected the two trailing-\n
# expectations below that could never hold)
assert extract_code_block("import csv\nprint(1)\n", "python") == "import csv\nprint(1)"
# closed fences unchanged: content extracted, stripped
assert extract_code_block("```python\nimport csv\nprint(1)\n```", "python") == "import csv\nprint(1)"
# bash truncated fence handled too
assert extract_code_block("```bash\nfor f in img_*.jpg; do\necho $f", "bash").startswith("for f in")
# and the REAL DH-02 grader on a truncated fenced answer now reports the
# REAL incomplete-code error (not the bogus line-1 fence SyntaxError)
p_tr, n_tr = grade_task(dh02, _trunc)
print("DH-02 truncated-fence ->", p_tr, n_tr)
assert not p_tr and "```python" not in n_tr, \
    f"truncated fence must NOT leak into the run note: {n_tr}"
print("OK truncated-open-fence fallback")

# 3. py_state grader (AB-01): correct solution must PASS
ab = [t for b in load_tasks()["benchmarks"] for t in b["tasks"] if t["id"] == "AB-01"][0]
good_code = (
    "import csv\n"
    'with open("tasks.csv") as f:\n'
    "    rows = list(csv.DictReader(f))\n"
    'with open("done.txt", "w") as f:\n'
    "    for r in rows:\n"
    '        if r["status"] == "done":\n'
    '            f.write(r["name"] + "\\n")\n'
)
passed, note = grade_task(ab, good_code)
print("AB-01 good ->", passed, note)
assert passed, f"good solution should pass: {note}"

# 4. py_state grader: wrong content must FAIL
bad_code = (
    "import csv\n"
    'with open("tasks.csv") as f:\n'
    "    rows = list(csv.DictReader(f))\n"
    'with open("done.txt", "w") as f:\n'
    "    for r in rows:\n"
    '        f.write("x\\n")\n'
)
passed2, note2 = grade_task(ab, bad_code)
print("AB-01 bad  ->", passed2, note2)
assert not passed2, "wrong solution should fail"

# 3b. py_stdout lines_set (AB-03): the note must carry BOTH got= and exp= so
#     the adaptive loop can self-correct (follow-up-11: a bare got=[...] with
#     no target left the 3B blind to the missing leading slash + POST /api).
ab03 = [t for b in load_tasks()["benchmarks"] for t in b["tasks"] if t["id"] == "AB-03"][0]
bad_lines = (
    "import re\n"
    "from collections import Counter\n"
    "c = Counter()\n"
    "for ln in open('access.log'):\n"
    "    m = re.search(r'\"GET /([^ ]*) HTTP', ln)\n"
    "    if m: c[m.group(1)] += 1\n"
    "print('\\n'.join(p for p, _ in c.most_common(3)))\n"
)
pab, nab = grade_task(ab03, bad_lines)
print("AB-03 bad  ->", pab, nab)
assert not pab, "GET-only regex missing POST /api + leading slash should fail"
assert "exp=" in nab and "/api" in nab, f"note must expose the target set: {nab}"
assert "got=" in nab, f"note must expose the produced set: {nab}"
good_lines = (
    "import re\n"
    "from collections import Counter\n"
    "c = Counter()\n"
    "for ln in open('access.log'):\n"
    "    m = re.search(r'\"([A-Z]+) (/[^ ]*) HTTP', ln)\n"
    "    if m: c[m.group(2)] += 1\n"
    "print('\\n'.join(p for p, _ in c.most_common(3)))\n"
)
pab2, nab2 = grade_task(ab03, good_lines)
print("AB-03 good ->", pab2, nab2)
assert pab2, f"all-methods regex with leading slash should pass: {nab2}"

# 5. think-wrapped correct AL-02 must now PASS (mirror real flow: strip then grade)
al02 = [t for b in load_tasks()["benchmarks"] for t in b["tasks"] if t["id"] == "AL-02"][0]
p3, n3 = grade_task(al02, _strip_reasoning_tags("<think> </think> 255.255.255.192"))
print("AL-02 think-wrapped ->", p3, n3)
assert p3, f"AL-02 think-wrapped should pass now: {n3}"

# 6. --self-analyse promoted to DEFAULT (Session 9 follow-up): DEFAULT_SYSTEM
#    stays the frozen base; SELF_ANALYSE_DIRECTIVE is appended BY DEFAULT and
#    only --no-self-analyse (self_analyse=False) removes it — the directive
#    must actually reach the system_instruction sent to the server.
assert "mentally run the artifact" not in AR.DEFAULT_SYSTEM, \
    "base prompt must stay frozen (directive lives in SELF_ANALYSE_DIRECTIVE)"
assert "fixtures, imports, exact output, numeric tolerance" in AR.SELF_ANALYSE_DIRECTIVE

_captured = {}
_orig_query = AR.query_completion
_orig_start, _orig_stop = AR.start_server, AR.stop_server
_orig_vram = AR.measure_gpu_vram


def _fake_query(server_url, prompt_text, system_instruction=None, **kw):
    _captured["sys"] = system_instruction
    return "255.255.255.192", 1.0, 1.0

AR.query_completion = _fake_query
AR.start_server = lambda cfg: (object(), cfg.get("benchmark_env", {}).get("port", 8089))
AR.stop_server = lambda *a, **k: None
AR.measure_gpu_vram = lambda: 0
_mini_cfg = {
    "id": "cluster2", "key": "02-x", "title": "t", "builder_model": "m",
    "benchmark_env": {"port": 8090, "context_length": 4096},
}
try:
    # default (no kwarg) → directive ON
    AR.evaluate_cluster(_mini_cfg, [{"name": "Agents' Last Exam", "tasks": [al02]}],
                        max_tokens_per_bench=1)
    assert _captured["sys"].startswith(AR.DEFAULT_SYSTEM), "base contract must be preserved"
    assert AR.SELF_ANALYSE_DIRECTIVE in _captured["sys"], \
        "directive must be ON by default"
    # explicit opt-out (--no-self-analyse)
    AR.evaluate_cluster(_mini_cfg, [{"name": "Agents' Last Exam", "tasks": [al02]}],
                        max_tokens_per_bench=1, self_analyse=False)
    assert AR.SELF_ANALYSE_DIRECTIVE not in _captured["sys"], \
        "no directive with self_analyse=False (--no-self-analyse)"
    # explicit on still works (--self-analyse)
    AR.evaluate_cluster(_mini_cfg, [{"name": "Agents' Last Exam", "tasks": [al02]}],
                        max_tokens_per_bench=1, self_analyse=True)
    assert AR.SELF_ANALYSE_DIRECTIVE in _captured["sys"], \
        "directive must reach the system prompt with self_analyse=True"
finally:
    AR.query_completion = _orig_query
    AR.start_server, AR.stop_server = _orig_start, _orig_stop
    AR.measure_gpu_vram = _orig_vram

# 6b. CLI default: --self-analyse is ON unless --no-self-analyse is passed.
_parser = AR.build_parser()
assert _parser.parse_args([]).self_analyse is True, "self-analyse must default ON"
assert _parser.parse_args(["--self-analyse"]).self_analyse is True
assert _parser.parse_args(["--no-self-analyse"]).self_analyse is False
print("OK self-analyse default ON (--no-self-analyse opts out)")

print("\nALL ARENA GRADER CHECKS PASSED")
