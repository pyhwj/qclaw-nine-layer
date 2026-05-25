import json

reg_path = r'D:\openclaw\.openclaw\workspace\skills\self-improving-agent\evolution\skill-registry.json'
with open(reg_path, 'r', encoding='utf-8') as f:
    reg = json.load(f)

print("=== OLD skills (first 3) ===")
for s in reg['skills'][:3]:
    t = s.get('trigger', '')
    print(f"  id={s['id']}, trigger type={type(t).__name__}, value={repr(t)[:120]}")

print("\n=== NEW skills (last 6) ===")
for s in reg['skills'][-6:]:
    t = s.get('trigger', '')
    print(f"  id={s['id']}, trigger type={type(t).__name__}, value={repr(t)[:120]}")