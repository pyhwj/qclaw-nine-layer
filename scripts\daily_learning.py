#!/usr/bin/env python3
"""
daily_learning.py — KernelGOD 九环日常集成
==========================================
每次任务执行后调用 record_task()，自动积累因果边/共现数据。
"""
import json, os, time
from pathlib import Path
from datetime import datetime, timezone

WORKSPACE = Path(r"D:\openclaw\.openclaw\workspace")
DATA_DIR = WORKSPACE / "skills" / "self-improving-agent" / "sagent" / "data"
MEMORY_DIR = WORKSPACE.parent / "memory"  # D:\openclaw\.openclaw\memory

def _load_json(path: Path):
    if path.exists():
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def _save_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def record_task(task_text: str, skills_used: list, success: bool = True):
    """记录一次任务执行"""
    now = datetime.now(timezone.utc).isoformat()
    t = time.strftime("%Y-%m-%d %H:%M:%S")

    # 1. co_occurrence
    cooccur = _load_json(DATA_DIR / "co_occurrence.json")
    for i, a in enumerate(skills_used):
        for b in skills_used[i+1:]:
            key = f"{a}-{b}" if a < b else f"{b}-{a}"
            if isinstance(cooccur, dict):
                cooccur[key] = cooccur.get(key, 0) + 1
            else:
                cooccur = {key: 1}
    _save_json(DATA_DIR / "co_occurrence.json", cooccur)

    # 2. causal_edges
    causal = _load_json(DATA_DIR / "causal_edges.json")
    if success and len(skills_used) >= 2:
        src = skills_used[0]
        for tgt in skills_used[1:]:
            if isinstance(causal, dict):
                if src not in causal: causal[src] = {}
                causal[src][tgt] = causal[src].get(tgt, 0.5) + 0.1
            else:
                causal = {src: {tgt: 0.52}}
    _save_json(DATA_DIR / "causal_edges.json", causal)

    # 3. memory 记录
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    mem_file = MEMORY_DIR / f"{time.strftime('%Y-%m-%d')}.md"
    entry = f"\n### {t}\n- 任务: {task_text[:120]}\n- 技能: {', '.join(skills_used)}\n- 结果: {'成功' if success else '失败'}\n"
    with open(mem_file, 'a', encoding='utf-8') as f:
        f.write(entry)

    # 4. 触发九层流水线（pipeline_tick）
    try:
        import subprocess, sys
        pipeline_script = str(WORKSPACE / "skills" / "self-improving-agent" / "evolution" / "pipeline_tick.py")
        skill_str = ",".join(skills_used)
        subprocess.Popen(
            [sys.executable, pipeline_script, "--task", task_text[:100], "--skills", skill_str, "--ok", str(success).lower()],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            creationflags=subprocess.DETACHED_PROCESS,
        )
    except Exception as e:
        pass  # pipeline 是后台任务，不影响主流程

    # 为了兼容旧格式，只返回原有字段
    return {"cooccur": len(cooccur), "causal": len(causal), "saved": t}

def daily_summary() -> dict:
    """今日统计"""
    today = time.strftime("%Y-%m-%d")
    cooccur = _load_json(DATA_DIR / "co_occurrence.json")
    causal = _load_json(DATA_DIR / "causal_edges.json")
    mem_file = MEMORY_DIR / f"{today}.md"
    events = 0
    if mem_file.exists():
        events = mem_file.read_text(encoding='utf-8').count("### ")
    return {
        "date": today,
        "cooccur_edges": len(cooccur) if isinstance(cooccur, dict) else 0,
        "causal_edges": len(causal) if isinstance(causal, dict) else 0,
        "memory_events": events
    }


def _ensure_all_skills(data_dir):
    """确保所有真实技能都有初始因果边"""
    import re
    all_skills = []
    for sd in sorted((data_dir.parent.parent.parent.parent / "skills").iterdir()):
        if not sd.is_dir() or sd.name.startswith("__") or sd.name.startswith("."): continue
        if re.match(r"^(api-client|agent|skill|mcp|test)[-_\d]", sd.name, re.I): continue
        sk = sd / "SKILL.md"
        if sk.exists() and sk.stat().st_size > 500:
            py_files = list((sd / "scripts").glob("*.py")) if (sd / "scripts").exists() else []
            if py_files: all_skills.append(sd.name)
    
    causal = _load_json(data_dir / "causal_edges.json")
    for s in all_skills:
        if s not in causal or not causal[s]:
            if not isinstance(causal, dict): causal = {}
            if s not in causal: causal[s] = {}
            for t in all_skills:
                if s != t and t not in causal[s]:
                    causal[s][t] = 0.3  # 初始低权重
    _save_json(data_dir / "causal_edges.json", causal)
    return len(all_skills)

if __name__ == "__main__":
    # 测试
    r = record_task("测试日常集成", ["reality-perception", "introspection"], True)
    print(record_task("测试任务2", ["execution-sandbox", "orchestrator"], True))
    print(daily_summary())
