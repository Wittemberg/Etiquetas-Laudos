import base64
import shutil
import os
import secrets
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, File, HTTPException, Query, Request, UploadFile
from fastapi.responses import FileResponse
from starlette.responses import Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .db import Database
from .generator import generate_docx, generate_pdf
from .parser import parse_pdf


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = BASE_DIR / "uploads"
OUTPUT_DIR = BASE_DIR / "outputs"

db = Database(os.getenv("ETIQUETAS_DB_PATH", str(DATA_DIR / "etiquetas.sqlite3")))
app = FastAPI(title="Etiquetas de Laudos")


@app.middleware("http")
async def optional_basic_auth(request: Request, call_next):
    password = os.getenv("ETIQUETAS_PASSWORD", "")
    if not password:
        return await call_next(request)

    auth = request.headers.get("authorization", "")
    expected = "Basic " + base64.b64encode(f"admin:{password}".encode()).decode()
    if not secrets.compare_digest(auth, expected):
        return Response(
            "Autenticacao requerida.",
            status_code=401,
            headers={"WWW-Authenticate": 'Basic realm="Etiquetas de Laudos"'},
        )
    return await call_next(request)


class LabelUpdate(BaseModel):
    exam_number: str
    patient_name: str
    city: str
    district: str
    birth_date: str
    exam_date: str


class PrintRequest(BaseModel):
    ids: list[int]


class DeleteRequest(BaseModel):
    ids: list[int]


@app.post("/api/import")
async def import_pdf(file: UploadFile = File(...)):
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Envie um arquivo PDF.")

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    target = UPLOAD_DIR / f"{uuid4()}-{Path(file.filename).name}"
    with target.open("wb") as handle:
        shutil.copyfileobj(file.file, handle)

    labels = parse_pdf(target)
    result = db.insert_labels(labels, file.filename)
    return result


@app.get("/api/labels")
def list_labels(sort: str = Query("created_desc")):
    return db.list_labels(sort)


@app.put("/api/labels/{label_id}")
def update_label(label_id: int, payload: LabelUpdate):
    try:
        return db.update_label(label_id, payload.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.delete("/api/labels")
def delete_labels(payload: DeleteRequest):
    deleted = db.delete_labels(payload.ids)
    return {"deleted": deleted}


@app.post("/api/print/pdf")
def print_pdf(payload: PrintRequest):
    labels = db.get_labels(payload.ids)
    if not labels:
        raise HTTPException(status_code=400, detail="Selecione pelo menos uma etiqueta.")
    output = generate_pdf(labels, OUTPUT_DIR / "etiquetas.pdf")
    return FileResponse(output, media_type="application/pdf", filename="etiquetas.pdf")


@app.post("/api/print/docx")
def print_docx(payload: PrintRequest):
    labels = db.get_labels(payload.ids)
    if not labels:
        raise HTTPException(status_code=400, detail="Selecione pelo menos uma etiqueta.")
    output = generate_docx(labels, OUTPUT_DIR / "etiquetas.docx")
    return FileResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename="etiquetas.docx",
    )


app.mount("/", StaticFiles(directory=BASE_DIR / "static", html=True), name="static")
