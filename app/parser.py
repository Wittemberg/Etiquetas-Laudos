import re
from pathlib import Path

import pdfplumber

from .models import ExamLabel


FIELD_PATTERNS = {
    "exam_number": re.compile(r"N. do exame:\s*(\S+)"),
    "health_unit_city": re.compile(
        r"Data da solicita..o:\s*\d{2}/\d{2}/\d{4}\s+UF:\s*\S+\s+Munic.pio:\s*(.*?)\n",
        re.S,
    ),
    "patient_name": re.compile(r"PACIENTE.*?\n(?:Cart.o SUS:.*?\n)?Nome:\s*(.*?)\s+Idade:", re.S),
    "birth_date": re.compile(r"Data do nascimento:\s*(\d{2}/\d{2}/\d{4})"),
    "address": re.compile(r"Endere.o:\s*(.*?)\s+Bairro:", re.S),
    "district": re.compile(r"Bairro:\s*(.*?)\nMunic.pio:", re.S),
    "city": re.compile(r"\nMunic.pio:\s*(.*?)\s+UF:"),
    "exam_date": re.compile(r"Data da realiza..o:\s*(\d{2}/\d{2}/\d{4})"),
}


def _match(pattern: re.Pattern[str], text: str) -> str:
    match = pattern.search(text)
    return " ".join(match.group(1).split()) if match else ""


def _label_location(health_unit_city: str, patient_city: str, district: str, address: str) -> tuple[str, str]:
    if health_unit_city and patient_city and health_unit_city.upper() != patient_city.upper():
        return health_unit_city, ""
    if district.upper() == "ZONA RURAL" and address:
        return patient_city, address
    return patient_city, district


def parse_pdf(path: str | Path) -> list[ExamLabel]:
    labels: list[ExamLabel] = []
    with pdfplumber.open(str(path)) as pdf:
        for page_number, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""
            health_unit_city = _match(FIELD_PATTERNS["health_unit_city"], text)
            patient_city = _match(FIELD_PATTERNS["city"], text)
            address = _match(FIELD_PATTERNS["address"], text)
            district = _match(FIELD_PATTERNS["district"], text)
            print_city, print_district = _label_location(health_unit_city, patient_city, district, address)

            label = ExamLabel(
                exam_number=_match(FIELD_PATTERNS["exam_number"], text),
                patient_name=_match(FIELD_PATTERNS["patient_name"], text),
                city=print_city,
                district=print_district,
                birth_date=_match(FIELD_PATTERNS["birth_date"], text),
                exam_date=_match(FIELD_PATTERNS["exam_date"], text),
                source_page=page_number,
            )
            if all([label.exam_number, label.patient_name, label.city, label.birth_date, label.exam_date]):
                labels.append(label)
    return labels
