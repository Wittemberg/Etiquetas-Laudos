import re
from pathlib import Path

import pdfplumber

from .models import ExamLabel


FIELD_PATTERNS = {
    "exam_number": re.compile(r"Nº do exame:\s*(\S+)"),
    "patient_name": re.compile(r"PACIENTE.*?\n(?:Cartão SUS:.*?\n)?Nome:\s*(.*?)\s+Idade:", re.S),
    "birth_date": re.compile(r"Data do nascimento:\s*(\d{2}/\d{2}/\d{4})"),
    "address": re.compile(r"Endereço:\s*(.*?)\s+Bairro:", re.S),
    "district": re.compile(r"Bairro:\s*(.*?)\nMunicípio:", re.S),
    "city": re.compile(r"\nMunicípio:\s*(.*?)\s+UF:"),
    "exam_date": re.compile(r"Data da realização:\s*(\d{2}/\d{2}/\d{4})"),
}


def _match(pattern: re.Pattern[str], text: str) -> str:
    match = pattern.search(text)
    return " ".join(match.group(1).split()) if match else ""


def parse_pdf(path: str | Path) -> list[ExamLabel]:
    labels: list[ExamLabel] = []
    with pdfplumber.open(str(path)) as pdf:
        for page_number, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""
            address = _match(FIELD_PATTERNS["address"], text)
            district = _match(FIELD_PATTERNS["district"], text)
            print_district = address if district.strip().upper() == "ZONA RURAL" and address else district

            label = ExamLabel(
                exam_number=_match(FIELD_PATTERNS["exam_number"], text),
                patient_name=_match(FIELD_PATTERNS["patient_name"], text),
                city=_match(FIELD_PATTERNS["city"], text),
                district=print_district,
                birth_date=_match(FIELD_PATTERNS["birth_date"], text),
                exam_date=_match(FIELD_PATTERNS["exam_date"], text),
                source_page=page_number,
            )
            if all([label.exam_number, label.patient_name, label.city, label.district, label.birth_date, label.exam_date]):
                labels.append(label)
    return labels
