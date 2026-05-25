import json

reg_path = r'D:\openclaw\.openclaw\workspace\skills\self-improving-agent\evolution\skill-registry.json'
with open(reg_path, 'r', encoding='utf-8') as f:
    reg = json.load(f)

new_skills = [
    {
        "name": "skill-pydantic-model",
        "status": "stable",
        "domain": "data-modeling",
        "source": "github:pydantic/pydantic",
        "stars": 20000,
        "tags": ["pydantic", "validation", "data-model", "serialization", "settings"]
    },
    {
        "name": "skill-api-fastapi",
        "status": "stable",
        "domain": "api-development",
        "source": "github:tiangolo/fastapi",
        "stars": 75000,
        "tags": ["fastapi", "rest-api", "scaffold", "async", "openapi"]
    },
    {
        "name": "skill-system-design",
        "status": "stable",
        "domain": "architecture",
        "source": "github:donnemartin/system-design-primer",
        "stars": 280000,
        "tags": ["system-design", "scalability", "architecture", "distributed-systems", "interview"]
    },
    {
        "name": "skill-python-project",
        "status": "stable",
        "domain": "dev-tooling",
        "source": "github:psf/black+astral-sh/ruff+python-poetry/poetry",
        "stars": 88000,
        "tags": ["python", "project-scaffold", "linting", "formatting", "packaging"]
    },
    {
        "name": "skill-workflow-patterns",
        "status": "stable",
        "domain": "orchestration",
        "source": "github:PrefectHQ/prefect",
        "stars": 16000,
        "tags": ["workflow", "pipeline", "retry", "dag", "task-orchestration"]
    },
    {
        "name": "skill-db-migration",
        "status": "stable",
        "domain": "database",
        "source": "github:sqlalchemy/sqlalchemy",
        "stars": 9000,
        "tags": ["sqlalchemy", "alembic", "migration", "orm", "database"]
    }
]

# Add new skills
for ns in new_skills:
    reg['skills'].append(ns)
    reg['total'] = reg.get('total', 0) + 1

# Update status counts
stable = sum(1 for s in reg['skills'] if s['status'] == 'stable')
beta = sum(1 for s in reg['skills'] if s['status'] == 'beta')
failed = sum(1 for s in reg['skills'] if s['status'] == 'failed')
reg['summary'] = {'stable': stable, 'beta': beta, 'failed': failed, 'total': len(reg['skills'])}

with open(reg_path, 'w', encoding='utf-8') as f:
    json.dump(reg, f, ensure_ascii=False, indent=2)

print(f'Registry: {len(reg["skills"])} skills ({stable} stable, {beta} beta, {failed} failed)')
for ns in new_skills:
    print(f'  + {ns["name"]} ({ns["domain"]}) ← {ns["source"]}')