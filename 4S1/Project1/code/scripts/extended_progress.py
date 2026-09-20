"""Read progress counters only; never evaluate masks or alter experiments."""
import json
from pathlib import Path
R=Path('/home/osta/lisa-eval/code/results');F=R/'training_free_extended_20260915';T=R/'extended_test_20260915';D=R/'extended_dev_20260915'
def lines(p): return len(p.read_text().splitlines()) if p.exists() else 0
counts={'LISA':lines(F/'p1_rows.jsonl'),'Qwen_LISA':lines(T/'qwen_lisa.jsonl'),'Qwen_presence':lines(T/'qwen_presence.jsonl')}
ready=(R/'extended_public_20260915.tar.gz').exists() and (R/'extended_records_20260915.tar.gz').exists() and 'FINALIZATION_COMPLETE' in ((D/'delivery_finalize.log').read_text() if (D/'delivery_finalize.log').exists() else '')
print(json.dumps({'counts':counts,'total':180,'ready':ready,'runner_active':Path('/proc/214902').exists(),'finalizer_active':Path('/proc/216257').exists()}))
