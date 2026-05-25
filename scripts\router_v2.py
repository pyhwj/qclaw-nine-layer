"""
SAGENT 4.0 Router v2 — 5-Pass Scoring (inspired by coolmanns/skillgraph)

| Pass | Strategy | Weight | Source |
|------|----------|--------|--------|
| 1    | Exact alias match | 1.0 | skill-registry triggers |
| 2    | Partial keyword match | 0.8 | SequenceMatcher |
| 3    | Tag/domain match | 0.6 | skill tags |
| 4    | Pipeline match | 0.4 | pipeline keywords |
| 5    | GNN embedding | 0.3 | gnn.py (pure numpy) |

Final score = weighted average of top-3 passes.
"""

import json, os, sys
from difflib import SequenceMatcher

SAGENT_DIR = os.path.dirname(os.path.abspath(__file__))
REGISTRY = os.path.join(os.path.dirname(SAGENT_DIR), "evolution", "skill-registry.json")
GNN_WEIGHTS = os.path.join(SAGENT_DIR, "gnn_weights.npz")


class RouterV2:
    def __init__(self):
        self.skills = []
        self.aliases = {}  # phrase -> skill_id
        self.gnn = None

    def load(self):
        data = json.load(open(REGISTRY, 'r', encoding='utf-8'))
        self.skills = [s for s in data['skills'] if s.get('status') not in ('merged', 'archived')]
        
        # Build alias index from triggers + names
        self.aliases = {}
        for s in self.skills:
            sid = s['id']
            # Full trigger as alias
            trigger = (s.get('trigger', '') or '').lower()
            if trigger:
                for phrase in self._segment_keywords(trigger):
                    self.aliases[phrase] = sid
            # Name as alias
            name = (s.get('name', '') or '').lower()
            if name:
                for phrase in self._segment_keywords(name):
                    self.aliases[phrase] = sid
            # Tags as aliases
            for tag in s.get('tags', []):
                self.aliases[tag.lower()] = sid
            # Explicit aliases from registry
            for alias in s.get('aliases', []):
                self.aliases[alias.lower()] = sid
        
        print(f'[RouterV2] Loaded {len(self.skills)} skills, {len(self.aliases)} aliases')
        return self

    def _segment_keywords(self, text):
        """Extract meaningful keyword segments (strip punctuation)"""
        import re
        words = re.findall(r'[\w\u4e00-\u9fff]+', text.strip().lower())
        result = list(words)
        for i in range(len(words)-1):
            result.append(f'{words[i]} {words[i+1]}')
        return set(w for w in result if len(w) > 1)

    def _load_gnn(self):
        """Lazy-load GNN for 5th pass"""
        if self.gnn is not None:
            return self.gnn
        if not os.path.exists(GNN_WEIGHTS):
            return None
        try:
            sys.path.insert(0, SAGENT_DIR)
            from gnn import GNN
            self.gnn = GNN.load_pretrained()
            return self.gnn
        except Exception as e:
            print(f'  [GNN] Load failed: {e}')
            return None

    def route(self, task, k=3, verbose=False):
        """5-pass routing"""
        task_lower = task.lower()
        scores = {s['id']: [] for s in self.skills}  # skill_id -> [pass_scores]
        
        # Pass 1: Exact alias match (weight 1.0)
        task_words = self._segment_keywords(task_lower)
        for phrase, sid in self.aliases.items():
            if phrase in task_lower:
                scores[sid].append(1.0)
        
        for s in self.skills:
            sid = s['id']
            # Pass 2: Partial keyword match (weight 0.8)
            trigger = (s.get('trigger', '') or '').lower()
            name = (s.get('name', '') or '').lower()
            sim = SequenceMatcher(None, task_lower, f'{trigger} {name}').ratio()
            if sim > 0.1:
                scores[sid].append(sim * 0.8)
            
            # Pass 3: Tag match (weight 0.6)
            tag_matches = sum(1 for tag in s.get('tags', []) if tag.lower() in task_lower)
            if tag_matches > 0:
                scores[sid].append(0.6 * min(tag_matches / max(len(s.get('tags', [])), 1) + 0.2, 1.0))
            
            # Pass 4: Pipeline match (weight 0.4)
            pipe_text = ' '.join(s.get('pipeline', []) or []).lower()
            pipe_sim = SequenceMatcher(None, task_lower, pipe_text).ratio()
            if pipe_sim > 0.05:
                scores[sid].append(pipe_sim * 0.4)
        
        # Pass 5: GNN embedding (weight 0.3)
        gnn = self._load_gnn()
        gnn_scores = {}
        if gnn:
            try:
                kw_scores = {sid: s for sid, s, _ in gnn.keyword_route(task, k=len(self.skills))}
                max_kw = max(kw_scores.values()) if kw_scores else 1
                gnn_result = gnn.route(task, k=len(self.skills))
                gnn_scores = {sid: s for sid, s, _ in gnn_result}
                max_gn = max(gnn_scores.values()) if gnn_scores else 1
                for sid in self.skills:
                    sid_key = sid['id'] if isinstance(sid, dict) else sid
                    if sid_key in gnn_scores:
                        # Use blended: 70% keyword + 30% GNN as pass 5
                        kw = kw_scores.get(sid_key, 0) / max_kw
                        gn = gnn_scores.get(sid_key, 0) / max_gn
                        scores[sid_key].append(0.3 * (0.7 * kw + 0.3 * gn))
            except Exception as e:
                if verbose:
                    print(f'  [GNN] Route failed: {e}')
        
        # Compute final scores: average top-3 passes
        sid_list = [s['id'] for s in self.skills]
        final = {}
        for sid in sid_list:
            if scores[sid]:
                # Take top-3 passes
                top = sorted(scores[sid], reverse=True)[:3]
                final[sid] = round(sum(top) / len(top), 4)
            else:
                final[sid] = 0.0
        
        # Sort
        ranked = sorted(final.items(), key=lambda x: -x[1])
        results = [(sid, s, next(sk['name'] for sk in self.skills if sk['id'] == sid)) 
                   for sid, s in ranked[:k] if s > 0]
        
        # Decision
        if results and results[0][1] >= 0.4:
            action = 'use_skill'
        elif results and results[0][1] >= 0.2:
            action = 'suggest_merge_or_new'
        else:
            action = 'crystallize_new'
        
        # KernelGOD v8: VectorStore fallback when no match
        if not results:
            try:
                from vector_store import VectorStore
                vs = VectorStore()
                vs.init()
                vs_results = vs.search_skills(task, top_k=k)
                if vs_results:
                    results = [(r['skill_id'], max(0.25, 1 - r.get('_distance', 1.0)), r['name']) 
                               for r in vs_results]
                    action = 'use_skill_vs'
            except Exception:
                pass
        
        return {
            'task': task,
            'results': [{'id': sid, 'confidence': s, 'name': n} for sid, s, n in results],
            'action': action,
            'passes': {sid: sorted(scores[sid], reverse=True) for sid in sid_list if scores[sid]}
        }

    def show(self, task):
        r = self.route(task, verbose=True)
        print(f'\nTask: {task}')
        print(f'  Action: {r["action"]}')
        if r['results']:
            print(f'  Results:')
            for res in r['results']:
                passes = r['passes'].get(res['id'], [])
                pass_str = ' | '.join(f'P{i+1}={p:.2f}' for i, p in enumerate(passes[:5]))
                print(f'    [{res["confidence"]:.0%}] {res["name"]}')
                if passes:
                    print(f'      {pass_str}')
        else:
            print(f'  No matches — trigger crystallization')
        
        # Show GNN-only comparison if available
        gnn = self._load_gnn()
        if gnn:
            print(f'  [GNN-only comparison]')
            try:
                gn = gnn.keyword_route(task)
                if gn:
                    print(f'    Top: [{gn[0][1]:.0%}] {gn[0][2]}')
            except:
                pass


if __name__ == '__main__':
    router = RouterV2().load()
    
    tests = [
        'extract text from PDF when node.js pdfjs-dist fails',
        'DNS is blocked cannot resolve domain github.com',
        'Unicode encoding error in PowerShell terminal',
        'continue working on task from previous session',
        'GNN neural network to route agent tools',
        'PowerShell confusing curl and curl.exe',
        'user told me to use x-reader for web pages',
        'create a folder on desktop',
        'monitor stock prices',
    ]
    
    print('=== SAGENT 4.0 Router v2 (5-Pass Scoring) ===')
    correct = 0
    for t in tests:
        router.show(t)
        # Check if first result matches expectation
        r = router.route(t)
        if r['results']:
            print(f'  -> Action: {r["action"]}')
        print()
    
    print(f'\nSkills: {len(router.skills)} | Aliases: {len(router.aliases)}')
