from collections.abc import Iterable
from typing import Any, Self

import aiosqlite

from bot.core.codenames.constants import Paths


class Database:
    _instance: Self
    _db: aiosqlite.Connection

    def __new__(cls, *args, **kwargs):
        """Access the :class:`Database` singleton.

        **WARNING**: ``await Database.create()`` should be called once previously

        :return: Database object
        """
        return cls._instance

    @classmethod
    async def create(cls) -> None:
        """Creates a :class:`aiosqlite.Connection` to the database to make it accessible as a singleton.

        :return: None
        """
        db = await aiosqlite.connect(Paths.db)

        await db.execute(
            "CREATE TABLE IF NOT EXISTS players "
            "(id int primary key, date text,"
            "games int, games_cap int, wins int, wins_cap int)"
        )
        await db.commit()

        cls._db = db
        cls._instance = super().__new__(cls)

    @classmethod
    async def close(cls) -> None:
        """Closes the connection to the database.

        :return: None
        """
        await cls._db.close()

    async def fetch(
        self,
        sql: str,
        parameters: Iterable[Any] | None = None,
        *,
        fetchall: bool = False,
    ) -> tuple[Any] | None:
        """Executes the given SQL query and returns the result.

        :param sql: SQL query to execute
        :param parameters: Parameters for the SQL query
        :param fetchall: Whether the function should return a single row or all rows
        :return: Results as a tuple
        """
        cursor = await self._db.execute(sql, parameters)
        res = await cursor.fetchall() if fetchall else await cursor.fetchone()
        await cursor.close()

        return tuple(res) if res else (tuple() if fetchall else None)

    async def exec_and_commit(self, sql: str, parameters: Iterable[Any] | None = None) -> None:
        """Executes the given SQL statement with changes to the database and commits them.

        :param sql: SQL statement to execute
        :param parameters: Parameters to the sql statement
        :return: None
        """
        await self._db.execute(sql, parameters)
        await self._db.commit()

    async def increase_stats(self, player_id: int, stats: Iterable[str]) -> None:
        """Increases the given stats by 1 for the given player, then commits the changes to the database.

        :param player_id: Player id
        :param stats: Stats to increase
        :return: None
        """
        if not (
            current_stats := await self.fetch(
                f"SELECT {', '.join(stats)} FROM players WHERE id = ?", (player_id,)
            )
        ):  # should not normally happen
            await self.exec_and_commit(
                "INSERT INTO players VALUES (?, strftime('%d/%m/%Y','now'), ?, ?, ?, ?, ?, ?)",
                (player_id, "", "en", 0, 0, 0, 0),
            )

        await self.exec_and_commit(
            f"UPDATE players SET {' = ?, '.join(stats)} = ? WHERE id = ?",
            (*map(lambda stat: stat + 1, current_stats), player_id),  # type: ignore
        )
