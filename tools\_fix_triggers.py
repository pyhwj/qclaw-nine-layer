import json

reg_path = r'D:\openclaw\.openclaw\workspace\skills\self-improving-agent\evolution\skill-registry.json'
with open(reg_path, 'r', encoding='utf-8') as f:
    reg = json.load(f)

# Fix trigger types for new skills + add proper trigger strings
trigger_map = {
    'skill-pydantic-model': 'Data validation, model definition, or serialization with Pydantic needed',
    'skill-api-fastapi': 'Create REST API, FastAPI scaffold, or OpenAPI endpoint needed',
    'skill-system-design': 'System architecture design, scalability planning, or distributed system patterns',
    'skill-python-project': 'Python project setup, pyproject.toml, linting, or packaging configuration',
    'skill-workflow-patterns': 'Multi-step workflow, task pipeline, retry logic, or DAG orchestration needed',
    'skill-db-migration': 'Database migration, schema evolution, ORM model, or Alembic versioning needed',
}
fixed = 0
for s in reg['skills']:
    if s['id'] in trigger_map:
        s['trigger'] = trigger_map[s['id']]
        print(f'Fixed trigger: {s["id"]}')
        fixed += 1

with open(reg_path, 'w', encoding='utf-8') as f:
    json.dump(reg, f, ensure_ascii=False, indent=2)
print(f'Done: {fixed} triggers fixed')