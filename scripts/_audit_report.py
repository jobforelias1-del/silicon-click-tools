from collections import defaultdict

from sc_produce.spec import load_structure, load_arrangement
from sc_produce.audit import audit_arrangement

s = load_structure("projects/pression_archivee/structure.yml")
a = load_arrangement("projects/pression_archivee/arrangement.yml")
rep = audit_arrangement(s, a)

out = []
out.append(f"total_cells={rep.total_cells}  ok_cells={rep.ok_cells}  "
           f"errors={len(rep.errors)}  warnings={len(rep.warnings)}  gate_ok={rep.ok}")

bykind = defaultdict(int)
for f in rep.findings:
    bykind[(f.severity, f.kind)] += 1
out.append("\nfindings by (severity, kind):")
for k, n in sorted(bykind.items()):
    out.append(f"  {k[0]:7} {k[1]:20} {n}")

audio = defaultdict(set)
for f in rep.errors:
    if f.kind == "audio_holds_midi":
        audio[f.track].add(f.scene)
out.append("\naudio_holds_midi errors grouped by track:")
for t, scs in sorted(audio.items()):
    out.append(f"  {t:14} x{len(scs)}  {sorted(scs)}")

out.append("\nsample finding messages (first of each kind):")
seen = set()
for f in rep.findings:
    if f.kind not in seen:
        seen.add(f.kind)
        out.append(f"  [{f.severity}/{f.kind}] {f.message}")

open("scripts/_audit_out.txt", "w").write("\n".join(out))
print("ok")
