"""certreq.grand: Entscheidungsregel ohne LLM."""
from certreq import grand


def test_verdict_needs_gain_beyond_noise_without_loss_elsewhere():
    rows = [{"variant": "Standard", "dev": 0.70, "r175": 0.62}, {"variant": "A", "dev": 0.74, "r175": 0.615},
            {"variant": "B", "dev": 0.80, "r175": 0.58}, {"variant": "C", "dev": 0.71, "r175": 0.63}]
    out = grand.verdict(rows, lambda r, b: r[b], ["dev", "r175"], "Standard")
    assert len(out) == 1 and out[0].startswith("BESSER: A")  # B verliert auf r175, C nur Streuung


def test_variants_cover_opposites():
    names = [n for n, *_ in grand.select_variants()] + [n for n, *_ in grand.extract_variants()]
    assert sum(n.startswith("Gegenteil") for n in names) >= 4
