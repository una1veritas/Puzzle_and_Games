'''
Created on 2026/01/26

@author: sin
'''

# sqlite_int_set.py
import sqlite3
from typing import Iterable, Iterator, List #, Optional


class SQLite3IntSet:
    """
    A small wrapper that uses SQLite to store a set of integers.
    Backed by a single table with an INTEGER PRIMARY KEY column so
    inserts are idempotent via INSERT OR IGNORE.
    """

    def __init__(self, path: str = ":memory:", table: str = "iset", optimize_for_bulk: bool = True):
        """
        path: sqlite file path or ":memory:" for in-memory DB.
        table: name of the table storing integers.
        optimize_for_bulk: if True, set PRAGMAs helpful for bulk loading.
        """
        self.path = path
        self.table = table
        self.conn = sqlite3.connect(self.path, isolation_level=None)  # autocommit off unless BEGIN executed
        self.conn.execute("PRAGMA foreign_keys = ON")
        if optimize_for_bulk:
            # Safe defaults while keeping decent speed for many integers
            self.conn.execute("PRAGMA synchronous = NORMAL")
            self.conn.execute("PRAGMA journal_mode = WAL")
        self._create_table()

    def _create_table(self) -> None:
        sql = f"CREATE TABLE IF NOT EXISTS {self.table} (value INTEGER PRIMARY KEY)"
        self.conn.execute(sql)

    def add(self, value: int) -> None:
        """Add a single integer (idempotent)."""
        sql = f"INSERT OR IGNORE INTO {self.table} (value) VALUES (?)"
        self.conn.execute(sql, (int(value),))

    def update(self, values: Iterable[int], chunk: int = 1000) -> None:
        """
        Add many integers. Uses chunked executemany to avoid huge SQL params.
        Wrap in a transaction for speed.
        """
        sql = f"INSERT OR IGNORE INTO {self.table} (value) VALUES (?)"
        cur = self.conn.cursor()
        cur.execute("BEGIN")
        try:
            batch: List[tuple] = []
            for v in values:
                batch.append((int(v),))
                if len(batch) >= chunk:
                    cur.executemany(sql, batch)
                    batch.clear()
            if batch:
                cur.executemany(sql, batch)
            cur.execute("COMMIT")
        except Exception:
            cur.execute("ROLLBACK")
            raise

    def remove(self, value: int) -> None:
        """Remove value; raise KeyError if not present."""
        sql = f"DELETE FROM {self.table} WHERE value = ?"
        cur = self.conn.execute(sql, (int(value),))
        if cur.rowcount == 0:
            raise KeyError(value)

    def discard(self, value: int) -> None:
        """Remove value if present; do nothing otherwise."""
        sql = f"DELETE FROM {self.table} WHERE value = ?"
        self.conn.execute(sql, (int(value),))

    def __contains__(self, value: int) -> bool:
        sql = f"SELECT 1 FROM {self.table} WHERE value = ? LIMIT 1"
        cur = self.conn.execute(sql, (int(value),))
        return cur.fetchone() is not None

    def __len__(self) -> int:
        sql = f"SELECT COUNT(*) FROM {self.table}"
        cur = self.conn.execute(sql)
        return cur.fetchone()[0]

    def __iter__(self) -> Iterator[int]:
        sql = f"SELECT value FROM {self.table} ORDER BY value"
        for (value,) in self.conn.execute(sql):
            yield int(value)

    def pop(self) -> int:
        """
        Remove and return an arbitrary element (smallest by ORDER BY here).
        Raise KeyError if empty.
        """
        cur = self.conn.execute(f"SELECT value FROM {self.table} ORDER BY value LIMIT 1")
        row = cur.fetchone()
        if row is None:
            raise KeyError("pop from an empty SQLite3IntSet")
        v = int(row[0])
        self.conn.execute(f"DELETE FROM {self.table} WHERE value = ?", (v,))
        return v

    def clear(self) -> None:
        self.conn.execute(f"DELETE FROM {self.table}")

    def intersection_with_iterable(self, values: Iterable[int], chunk: int = 1000) -> List[int]:
        """
        Return list of values that exist both in this set and in the given iterable.
        Uses chunked IN (...) queries for the Python iterable case.
        """
        result: List[int] = []
        buf: List[int] = []
        for v in values:
            buf.append(int(v))
            if len(buf) >= chunk:
                result.extend(self._select_in(buf))
                buf.clear()
        if buf:
            result.extend(self._select_in(buf))
        return result

    def _select_in(self, vals: List[int]) -> List[int]:
        if not vals:
            return []
        placeholders = ",".join("?" for _ in vals)
        sql = f"SELECT value FROM {self.table} WHERE value IN ({placeholders})"
        return [row[0] for row in self.conn.execute(sql, vals)]

    def close(self) -> None:
        self.conn.close()

    # Context manager support
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()


if __name__ == "__main__":
    # Quick demo
    #with SQLite3IntSet(":memory:") as s:
    with SQLite3IntSet("/Volumes/Media_SSD/intset.db") as s:
        s.add(1)
        s.update(range(2, 100))
        print("len:", len(s))          # len: 9
        print("contains 5:", 5 in s)   # True
        print("first three:", list(iter(s))[:3])
        s.discard(3)
        try:
            print('trying remove(9)')
            s.remove(9)
        except KeyError:
            print("9 not present")
        print("intersection with [4, 5, 100]:", s.intersection_with_iterable([4, 5, 100]))
        print("popped:", s.pop())
        print("len after pop:", len(s))
        print(list(s))