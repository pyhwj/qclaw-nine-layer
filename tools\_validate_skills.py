import yaml, os

base = r'D:\openclaw\.openclaw\workspace\skills'
skills = ['skill-pydantic-model','skill-api-fastapi','skill-system-design','skill-python-project','skill-workflow-patterns','skill-db-migration']

ok = 0
for s in skills:
    p = os.path.join(base, s, 'SKILL.md')
    text = open(p, encoding='utf-8').read()
    if not text.startswith('---'):
        print(f'FAIL {s}: no frontmatter')
        continue
    fm = text.split('---', 2)[1]
    data = yaml.safe_load(fm)
    desc = data['description'][:60]
    print(f'OK {s}: {data["name"]} | {desc}')
    ok += 1
print(f'\n{ok}/{len(skills)} validated')