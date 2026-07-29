import sqlite3
from contextlib import closing
from pathlib import Path

from .models import ExamLabel, iso_now


SCHEMA = """
CREATE TABLE IF NOT EXISTS labels (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    exam_number TEXT NOT NULL,
    patient_name TEXT NOT NULL,
    city TEXT NOT NULL,
    district TEXT NOT NULL,
    birth_date TEXT NOT NULL,
    exam_date TEXT NOT NULL,
    source_file TEXT,
    source_page INTEGER,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(patient_name, birth_date, exam_date)
);
"""


SORTS = {
    "created_desc": "id DESC",
    "exam_date_asc": "substr(exam_date, 7, 4) || substr(exam_date, 4, 2) || substr(exam_date, 1, 2) ASC, CAST(exam_number AS INTEGER) ASC",
    "exam_date_desc": "substr(exam_date, 7, 4) || substr(exam_date, 4, 2) || substr(exam_date, 1, 2) DESC, CAST(exam_number AS INTEGER) DESC",
    "exam_number_asc": "CAST(exam_number AS INTEGER) ASC, exam_number ASC",
    "exam_number_desc": "CAST(exam_number AS INTEGER) DESC, exam_number DESC",
}


class Database:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.init()

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn

    def init(self) -> None:
        with closing(self.connect()) as conn:
            conn.executescript(SCHEMA)
            conn.commit()

    def insert_labels(self, labels: list[ExamLabel], source_file: str) -> dict[str, int]:
        inserted = 0
        duplicated = 0
        now = iso_now()
        with closing(self.connect()) as conn:
            for label in labels:
                try:
                    conn.execute(
                        """
                        INSERT INTO labels (
                            exam_number, patient_name, city, district, birth_date, exam_date,
                            source_file, source_page, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            label.exam_number,
                            label.patient_name,
                            label.city,
                            label.district,
                            label.birth_date,
                            label.exam_date,
                            source_file,
                            label.source_page,
                            now,
                            now,
                        ),
                    )
                    inserted += 1
                except sqlite3.IntegrityError:
                    duplicated += 1
            conn.commit()
        return {"inserted": inserted, "duplicated": duplicated, "parsed": len(labels)}

    def list_labels(self, sort: str = "created_desc") -> list[dict]:
        order_by = SORTS.get(sort, SORTS["created_desc"])
        with closing(self.connect()) as conn:
            rows = conn.execute(f"SELECT * FROM labels ORDER BY {order_by}").fetchall()
        return [dict(row) for row in rows]

    def update_label(self, label_id: int, payload: dict) -> dict:
        allowed = ["exam_number", "patient_name", "city", "district", "birth_date", "exam_date"]
        values = {key: payload[key].strip() for key in allowed if key in payload}
        if not values:
            raise ValueError("Nenhum campo para atualizar.")
        values["updated_at"] = iso_now()
        set_clause = ", ".join(f"{key} = ?" for key in values)
        params = list(values.values()) + [label_id]
        with closing(self.connect()) as conn:
            try:
                conn.execute(f"UPDATE labels SET {set_clause} WHERE id = ?", params)
            except sqlite3.IntegrityError as exc:
                raise ValueError("Ja existe uma etiqueta com mesmo paciente, nascimento e realizacao.") from exc
            conn.commit()
            row = conn.execute("SELECT * FROM labels WHERE id = ?", (label_id,)).fetchone()
        if row is None:
            raise ValueError("Etiqueta não encontrada.")
        return dict(row)

    def get_labels(self, ids: list[int]) -> list[dict]:
        if not ids:
            return []
        placeholders = ",".join("?" for _ in ids)
        order_cases = " ".join(f"WHEN ? THEN {index}" for index, _ in enumerate(ids))
        with closing(self.connect()) as conn:
            rows = conn.execute(
                f"SELECT * FROM labels WHERE id IN ({placeholders}) ORDER BY CASE id {order_cases} END",
                ids + ids,
            ).fetchall()
        return [dict(row) for row in rows]

    def delete_labels(self, ids: list[int]) -> int:
        if not ids:
            return 0
        placeholders = ",".join("?" for _ in ids)
        with closing(self.connect()) as conn:
            cursor = conn.execute(f"DELETE FROM labels WHERE id IN ({placeholders})", ids)
            conn.commit()
        return cursor.rowcount
