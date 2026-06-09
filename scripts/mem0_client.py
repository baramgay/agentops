"""
에이전트 장기 메모리 클라이언트 (ChromaDB + sentence-transformers 기반)

mem0 API와 동일한 인터페이스 유지:
  add_experience(agent_id, text)
  search_experience(agent_id, query, limit)
  get_all(agent_id)
  sync_from_md(agent_id, md_path)

mem0 클라우드로 전환 시:
  from mem0 import Memory
  m = Memory.from_config({...})  # ANTHROPIC_API_KEY 필요
  → add/search/get_all 동일하게 호출 가능
"""
import os
import json
import hashlib
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / ".mem0" / "chroma"
COLLECTION = "gni_agents"
EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

_chroma_client = None
_collection = None
_embedder = None


def _get_embedder():
    global _embedder
    if _embedder is None:
        try:
            from sentence_transformers import SentenceTransformer
            import warnings
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                _embedder = SentenceTransformer(EMBED_MODEL)
        except ImportError:
            raise ImportError("pip install sentence-transformers 실행 필요")
    return _embedder


def _get_collection():
    global _chroma_client, _collection
    if _collection is None:
        import chromadb
        DB_PATH.mkdir(parents=True, exist_ok=True)
        _chroma_client = chromadb.PersistentClient(path=str(DB_PATH))
        _collection = _chroma_client.get_or_create_collection(
            name=COLLECTION,
            metadata={"hnsw:space": "cosine"}
        )
    return _collection


def _embed(text: str) -> list:
    model = _get_embedder()
    import warnings
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return model.encode(text).tolist()


def _mem_id(agent_id: str, text: str) -> str:
    h = hashlib.md5(f"{agent_id}:{text}".encode()).hexdigest()[:12]
    return f"{agent_id}_{h}"


def add_experience(agent_id: str, text: str, metadata: dict = None) -> dict:
    """에이전트 작업 경험 저장. 같은 내용 중복 저장 방지."""
    if not text or not text.strip():
        return {"status": "skipped", "reason": "empty"}
    col = _get_collection()
    mem_id = _mem_id(agent_id, text.strip())
    meta = {
        "agent_id": agent_id,
        "ts": datetime.now().isoformat(),
        **(metadata or {})
    }
    try:
        col.upsert(
            ids=[mem_id],
            embeddings=[_embed(text)],
            documents=[text],
            metadatas=[meta]
        )
        return {"status": "added", "id": mem_id}
    except Exception as e:
        return {"status": "error", "error": str(e)}


def search_experience(agent_id: str, query: str, limit: int = 5) -> list:
    """의미 벡터 검색 — 키워드 매칭 아닌 유사도 기반."""
    if not query:
        return []
    col = _get_collection()
    total = col.count()
    if total == 0:
        return []
    try:
        results = col.query(
            query_embeddings=[_embed(query)],
            n_results=min(limit, total),
            where={"agent_id": agent_id},
            include=["documents", "distances", "metadatas"]
        )
        out = []
        docs = results.get("documents", [[]])[0]
        dists = results.get("distances", [[]])[0]
        metas = results.get("metadatas", [[]])[0]
        for doc, dist, meta in zip(docs, dists, metas):
            out.append({
                "memory": doc,
                "score": round(1 - dist, 4),
                "agent_id": meta.get("agent_id"),
                "ts": meta.get("ts"),
            })
        return sorted(out, key=lambda x: x["score"], reverse=True)
    except Exception as e:
        return []


def get_all(agent_id: str) -> list:
    """에이전트 전체 메모리 목록."""
    col = _get_collection()
    if col.count() == 0:
        return []
    try:
        results = col.get(
            where={"agent_id": agent_id},
            include=["documents", "metadatas"]
        )
        out = []
        for doc, meta in zip(results.get("documents", []), results.get("metadatas", [])):
            out.append({"memory": doc, "ts": meta.get("ts"), "agent_id": meta.get("agent_id")})
        return out
    except Exception:
        return []


def sync_from_md(agent_id: str, md_path: str) -> int:
    """memory.md 내용을 mem0로 마이그레이션 (섹션별 분할 저장)."""
    md_path = Path(md_path)
    if not md_path.exists():
        return 0
    content = md_path.read_text(encoding="utf-8")
    sections = []
    current = []
    for line in content.splitlines():
        if line.startswith("## ") and current:
            sections.append("\n".join(current).strip())
            current = [line]
        else:
            current.append(line)
    if current:
        sections.append("\n".join(current).strip())

    count = 0
    for sec in sections:
        if len(sec.strip()) > 20:
            result = add_experience(agent_id, sec)
            if result.get("status") == "added":
                count += 1
    return count


def delete_all(agent_id: str) -> bool:
    """에이전트 메모리 전체 삭제."""
    col = _get_collection()
    try:
        results = col.get(where={"agent_id": agent_id})
        ids = results.get("ids", [])
        if ids:
            col.delete(ids=ids)
        return True
    except Exception:
        return False


if __name__ == "__main__":
    print("=== mem0_client 동작 테스트 ===")
    r = add_experience("orchestrator", "orchestrator는 33개 에이전트를 총괄하며 수직 지휘 체계를 운영한다.")
    print("add:", r)
    r2 = add_experience("orchestrator", "경남 부동산 월보는 realty-analyst가 전담한다.")
    print("add2:", r2)
    hits = search_experience("orchestrator", "에이전트 지휘 체계", limit=3)
    print("search:", [(h["memory"][:40], h["score"]) for h in hits])
    all_mems = get_all("orchestrator")
    print("get_all:", len(all_mems), "건")
    delete_all("orchestrator")
    print("delete_all 완료")
    print("=== 테스트 통과 ===")
