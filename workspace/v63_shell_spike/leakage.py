from __future__ import annotations
LEAK_BASE = {"1M":1064, "1p5M":1094, "2M":1104}
def leak_for(source, stage):
    m = {"1M":184, "1p5M":190, "2M":192}[source]
    if stage=="base":
        return 5*m+5*16+64
    elif stage=="delta8":
        return 5*(m+8)+80+64
    elif stage=="delta16":
        return 5*(m+16)+80+64
    else:
        raise ValueError(stage)
def test_leak_single_tag():
    for src in ["1M","1p5M","2M"]:
        b = leak_for(src,"base")
        s1 = leak_for(src,"delta8")
        s2 = leak_for(src,"delta16")
        assert s1-b==40 and s2-s1==40 and s2-b==80
        m = {"1M":184, "1p5M":190, "2M":192}[src]
        assert b == 5*m+80+64
    print("leak single tag PASS")
