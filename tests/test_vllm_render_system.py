"""vllm_generate.render_templated: an empty system message is a system message, and
a template that ignores it is refused, not mislabelled. Real tokenizers, offline."""
import pytest

from malignment.generate import DEFAULT
from malignment.vllm_generate import SystemIgnored, render_templated


def tok(m):
    transformers = pytest.importorskip("transformers")
    try:
        return transformers.AutoTokenizer.from_pretrained(m, local_files_only=True)
    except Exception:
        pytest.skip("%s not in the local HF cache" % m)


STEM = "She knelt down in front of him and began to suck his"


def test_empty_system_removes_the_default_persona():
    t = tok("Qwen/Qwen2.5-0.5B-Instruct")
    d = render_templated(t, STEM, DEFAULT, True, "Hi.")
    e = render_templated(t, STEM, "", True, "Hi.")
    assert "You are Qwen" in d and "You are Qwen" not in e
    assert e.count("<|im_start|>system") == 1          # an empty system turn, present


def test_ignored_empty_system_is_refused():
    t = tok("meta-llama/Llama-3.1-8B-Instruct")
    render_templated(t, STEM, DEFAULT, True, "Hi.")
    with pytest.raises(SystemIgnored):
        render_templated(t, STEM, "", True, "Hi.")


def test_refused_system_role_raises():
    t = tok("google/gemma-2-9b-it")
    with pytest.raises(Exception):
        render_templated(t, STEM, "", True, "Hi.")


def test_prefill_puts_hi_in_the_user_turn_and_leaves_the_stem_out():
    t = tok("Qwen/Qwen2.5-0.5B-Instruct")
    e = render_templated(t, STEM, "", True, "Hi.")
    assert "Hi." in e and STEM not in e and e.rstrip().endswith("assistant")


def test_thinking_off_by_the_vendor_switch():
    t = tok("Qwen/Qwen3-8B")
    on = render_templated(t, STEM, "", True, "Hi.")
    off = render_templated(t, STEM, "", True, "Hi.", {"enable_thinking": False})
    assert "<think>" not in on and off.endswith("<think>\n\n</think>\n\n")


def test_thinking_off_by_prefix_where_the_template_has_no_switch():
    t = tok("microsoft/phi-4-reasoning")
    off = render_templated(t, STEM, DEFAULT, False, "Hi.", {"enable_thinking": False}, "<think>\n\n</think>\n\n")
    assert off.endswith("<|im_start|>assistant<|im_sep|><think>\n\n</think>\n\n")


def test_hf_render_takes_the_thinking_switch():
    """generate.render (the local HF path) carries template_kwargs like vllm_generate."""
    from types import SimpleNamespace
    from malignment.generate import render
    t = tok("Qwen/Qwen3-8B")
    ld = SimpleNamespace(tok=t)
    on, _ = render(ld, "Q: Who are you?\nA:", system="", prefill=True, user_msg="Hi.")
    off, ok = render(ld, "Q: Who are you?\nA:", system="", prefill=True, user_msg="Hi.",
                     template_kwargs={"enable_thinking": False})
    assert "<think>" not in on and "<think>\n\n</think>\n\nQ: Who are you?\nA:" in off and ok
