"""bioresearch/quality/audit.py — 链式哈希审计追踪（JSONL，确定性）。

每次执行的关键事件以 JSONL 追加写入；每条记录携带 ``prev_hash`` 与
``chain_hash``，形成不可篡改的哈希链（篡改任一历史行的 payload 都会使后续
所有 ``chain_hash`` 失配）。支持跨会话续链：初始化时若文件已存在，则从末行
读取上一 ``chain_hash`` 作为 ``prev_hash``。

线程安全：写入受实例级 ``threading.Lock`` 保护。
"""

from __future__ import annotations

import hashlib
import json
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

__all__ = ["AuditTrail", "_ZERO_HASH"]

_ZERO_HASH = "0" * 64


class AuditTrail:
    """链式哈希审计追踪器。"""

    def __init__(self, path) -> None:
        """初始化。

        Args:
            path: 审计日志文件路径（父目录自动创建）。
        """
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._prev_hash = self._seed_prev_hash()

    def _seed_prev_hash(self) -> str:
        """从已有日志末行续链；无文件或解析失败则返回全零哈希。"""
        if self.path.exists():
            try:
                last = self.path.read_text(encoding="utf-8").strip().splitlines()[-1]
                rec = json.loads(last)
                return rec.get("chain_hash", _ZERO_HASH)
            except Exception:
                return _ZERO_HASH
        return _ZERO_HASH

    def log(self, event: str, **fields: Any) -> Dict[str, Any]:
        """写入一条审计记录并返回该记录。

        Args:
            event: 事件名（如 ``"STAGE_START"`` / ``"ASSERTION_CHECK"`` / ``"TOOL_CALL"``）。
            **fields: 附加字段（必须是 JSON 可序列化类型）。

        Returns:
            完整记录字典（含 ``timestamp`` / ``chain_hash`` / ``prev_hash``）。
        """
        ts = datetime.now(timezone.utc).isoformat()
        record: Dict[str, Any] = {"timestamp": ts, "event": event, **fields}
        payload = json.dumps(record, sort_keys=True, ensure_ascii=False)
        chain = hashlib.sha256(
            (self._prev_hash + "|" + payload).encode("utf-8")
        ).hexdigest()
        record["chain_hash"] = chain
        record["prev_hash"] = self._prev_hash
        line = json.dumps(record, ensure_ascii=False)
        with self._lock:
            with self.path.open("a", encoding="utf-8") as fh:
                fh.write(line + "\n")
            self._prev_hash = chain
        return record

    def session_summary(self) -> Dict[str, Any]:
        """汇总当前日志：记录数、事件类型列表、末链哈希。"""
        n = 0
        events: List[str] = []
        if self.path.exists():
            for line in self.path.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                n += 1
                try:
                    events.append(json.loads(line).get("event", "?"))
                except Exception:
                    pass
        return {"records": n, "events": events, "last_chain_hash": self._prev_hash}
