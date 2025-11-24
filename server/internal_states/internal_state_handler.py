from typing import List, Optional
import aiosqlite
from models.models import StoredInternalState
from utils.utils import singleton


@singleton
class InternalStateHandler:
    def __init__(self, path: str = "internal_state.db"):
        self.path = path
        self._initialized = False

    async def _init(self):
        if self._initialized:
            return
        async with aiosqlite.connect(self.path) as db:
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS internal_state (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
                """
            )
            await db.commit()
        self._initialized = True

    async def set(self, state: StoredInternalState):
        await self._init()
        value = state.model_dump_json()
        async with aiosqlite.connect(self.path) as db:
            await db.execute(
                """
                INSERT INTO internal_state (key, value)
                VALUES (?, ?)
                ON CONFLICT(key) DO UPDATE SET value=excluded.value
                """,
                (state.name, value),
            )
            await db.commit()

    async def get(self, name: str) -> Optional[StoredInternalState]:
        await self._init()
        async with aiosqlite.connect(self.path) as db:
            cursor = await db.execute(
                "SELECT value FROM internal_state WHERE key=?", (name,)
            )
            row = await cursor.fetchone()
        if row is None:
            return None
        return StoredInternalState.model_validate_json(row[0])

    async def delete(self, key: str):
        await self._init()
        async with aiosqlite.connect(self.path) as db:
            await db.execute("DELETE FROM internal_state WHERE key=?", (key,))
            await db.commit()

    async def list_keys(self):
        await self._init()
        async with aiosqlite.connect(self.path) as db:
            cursor = await db.execute("SELECT key FROM internal_state")
            rows = await cursor.fetchall()
        return [r[0] for r in rows]

    async def bulk_set(self, states: List[StoredInternalState]):
        """Set multiple StoredInternalState objects at once."""
        await self._init()
        async with aiosqlite.connect(self.path) as db:
            async with db.execute("BEGIN"):
                for state in states:
                    value = state.model_dump_json()
                    await db.execute(
                        """
                        INSERT INTO internal_state (key, value)
                        VALUES (?, ?)
                        ON CONFLICT(key) DO UPDATE SET value=excluded.value
                        """,
                        (state.name, value),
                    )
                await db.commit()
