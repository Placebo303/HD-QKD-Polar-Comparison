from __future__ import annotations
import inspect
import numpy as np
import pytest
from comparison_bench.src.comparison_bench.formal_ir import nonbinary_v4_ir as v4
from comparison_bench.src.comparison_bench.formal_ir import nonbinary_v3 as v3
from comparison_bench.src.comparison_bench.formal_ir.nonbinary_field import GF2mField
from comparison_bench.src.comparison_bench.formal_ir.nonbinary_qspa import nonbinary_syndrome

def test_reconstructs_v3_identity_and_public_only_core():
    cb,mats=v4.codebook()
    assert cb["canonical_schema"]=="NBLDPC3" and cb["q"]==1024
    assert not any(x in name.lower() for name in inspect.signature(v4.start).parameters for x in ("alice","truth","callback"))
    syn=nonbinary_syndrome(mats[32],(0,)*64,GF2mField.create(1024))
    started=v4.start("nbldpc_v4_ir_warm",(0,)*64,syn,cb,p=.20,stage_runner=lambda state,mats,stage:{"status":"syndrome_consistent","iterations":1,"decoded_symbols":state.bob})
    state,result,matrices=started
    assert result["status"]=="syndrome_consistent"
    with pytest.raises(TypeError,match="not serializable"): state.__getstate__()

def test_warm_uses_complete_product_and_restart_drops_old_messages():
    cb,mats=v4.codebook(); syn=nonbinary_syndrome(mats[32],(0,)*64,GF2mField.create(1024))
    fake=lambda state,mats,stage:{"status":"decode_failed","iterations":1}
    warm,_,_=v4.start("nbldpc_v4_ir_warm",(0,)*64,syn,cb,p=.20,stage_runner=fake)
    old=next(iter(warm.messages)); warm.messages[old]=np.full(1024,1/1024); extended=v4.extend(warm,(0,)*8,mats,mode="warm")
    assert extended.active_checks==40 and old in extended.messages
    restart,_,_=v4.start("nbldpc_v4_ir_restart",(0,)*64,syn,cb,p=.20,stage_runner=fake)
    old_value=next(iter(restart.messages)); restart.messages[old_value]=np.zeros(1024); reset=v4.extend(restart,(0,)*8,mats,mode="restart")
    assert reset.active_checks==40 and np.allclose(reset.messages[old_value],1/1024)
    assert isinstance(v4.extend(reset,(0,)*8,mats,mode="restart"),dict)

def test_control_is_exact_v3_l075_on_same_nonzero_public_input():
    cb,mats=v4.codebook(); rng=np.random.default_rng(202607559999)
    bob=tuple(int(x) for x in rng.integers(0,1024,64)); decoded=tuple(int(x) for x in rng.integers(0,1024,64))
    syn=nonbinary_syndrome(mats[32],decoded,GF2mField.create(1024))
    legacy=v3.decode_nbldpc_v3("nbldpc_formal_v3_layered_l075",bob,syn,cb,mats,check_count=32,p=.20,max_iter=12)
    state,got,_=v4.start("nbldpc_v4_control",bob,syn,cb,p=.20)
    # Same public inputs and cap must agree in status, decoded word and work.
    assert got["status"]==legacy["status"] and got["iterations"]==legacy["iterations"]
    assert got.get("decoded_symbols")==legacy.get("decoded_symbols")

def test_extension_rejects_wrong_prefix_and_prohibited_policy():
    cb,mats=v4.codebook(); syn=nonbinary_syndrome(mats[32],(0,)*64,GF2mField.create(1024))
    state,_,_=v4.start("nbldpc_v4_ir_warm",(0,)*64,syn,cb,p=.20,stage_runner=lambda *_:{"status":"decode_failed","iterations":1})
    assert v4.extend(state,(0,)*7,mats,mode="warm")["status"]=="invalid_input"
    assert v4.extend(state,(0,)*8,mats,mode="restart")["status"]=="invalid_input"
