from dataclasses import dataclass
from datetime import datetime


@dataclass
class ExamLabel:
    exam_number: str
    patient_name: str
    city: str
    district: str
    birth_date: str
    exam_date: str
    source_page: int

    @property
    def duplicate_key(self) -> tuple[str, str, str]:
        return (
            self.patient_name.strip().upper(),
            self.birth_date.strip(),
            self.exam_date.strip(),
        )


def iso_now() -> str:
    return datetime.now().isoformat(timespec="seconds")
