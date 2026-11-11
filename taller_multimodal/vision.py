"""Ejercicios de vision con la API de Groq. Ejecutar desde la raiz del repositorio."""
from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import os
from io import BytesIO
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from groq import Groq
from PIL import Image

load_dotenv()
ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "resultados"
FIELDS = ["componente", "marca_o_texto_visible", "puertos_o_conectores", "estado_visible", "uso_probable"]


def image_block(path: Path, mime_override: str | None = None) -> dict:
    # Mantiene los originales y reduce la copia enviada para respetar el limite multimodal.
    with Image.open(path) as source:
        image = source.convert("RGB")
        image.thumbnail((1600, 1600))
        buffer = BytesIO()
        image.save(buffer, format="JPEG", quality=82, optimize=True)
    mime = mime_override or "image/jpeg"
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    return {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{encoded}"}}


def ask_images(paths: list[Path], prompt: str, mime_override: str | None = None) -> str:
    client = Groq()
    content = [{"type": "text", "text": prompt}]
    content.extend(image_block(p, mime_override if len(paths) == 1 else None) for p in paths)
    answer = client.chat.completions.create(
        model=os.getenv("VISION_MODEL", "qwen/qwen3.8-27b"),
        messages=[{"role": "user", "content": content}],
        max_tokens=1200,
    )
    return answer.choices[0].message.content or ""


def parse_json_object(text: str) -> dict:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
    parsed = json.loads(cleaned)
    if not isinstance(parsed, dict):
        raise ValueError("La respuesta JSON no es un objeto.")
    return parsed


def validate_fields(data: dict) -> tuple[bool, list[str]]:
    problems = []
    for field in FIELDS:
        if field not in data:
            problems.append(f"Falta el campo obligatorio: {field}")
        elif not isinstance(data[field], str):
            problems.append(f"El campo {field} debe ser texto")
    extra = set(data) - set(FIELDS)
    if extra:
        problems.append("Campos no esperados: " + ", ".join(sorted(extra)))
    return not problems, problems


def save_result(name: str, data: dict) -> Path:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    target = OUTPUT / f"{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    target.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return target


def run_extract(paths: list[Path]) -> None:
    rows = []
    for path in paths:
        prompt = ("Analiza este componente de computador. Extrae solo un objeto JSON con estas cinco claves "
                  f"y valores de texto: {', '.join(FIELDS)}. Si un dato no se distingue, escribe 'no visible'. "
                  "No inventes marca ni especificaciones.")
        try:
            raw = ask_images([path], prompt)
            data = parse_json_object(raw)
            valid, issues = validate_fields(data)
            rows.append({"imagen": path.name, "respuesta": data, "valido": valid, "errores": issues})
            print(f"\n{path.name}: {'JSON valido' if valid else 'JSON invalido'}")
            print(json.dumps(data, ensure_ascii=False, indent=2))
            if issues:
                print("; ".join(issues))
        except Exception as exc:
            rows.append({"imagen": path.name, "valido": False, "error": str(exc)})
            print(f"\n{path.name}: no se pudo procesar: {exc}")
    target = save_result("extraccion", {"campos": FIELDS, "resultados": rows})
    print(f"\nResultados guardados en {target}")


def run_accuracy() -> None:
    truth_path = ROOT / "valores_reales.json"
    if not truth_path.exists():
        print(f"Crea {truth_path.name} comparando manualmente tres imagenes con sus valores reales.")
        return
    truth = json.loads(truth_path.read_text(encoding="utf-8"))
    predictions = sorted(OUTPUT.glob("extraccion_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not predictions:
        print("Primero ejecuta el ejercicio extraer.")
        return
    pred_rows = {r["imagen"]: r.get("respuesta", {}) for r in json.loads(predictions[0].read_text(encoding="utf-8"))["resultados"]}
    total = correct = 0
    details = []
    for image, expected in truth.items():
        predicted = pred_rows.get(image, {})
        for field in FIELDS:
            if field not in expected:
                continue
            match = str(expected[field]).strip().casefold() == str(predicted.get(field, "")).strip().casefold()
            total += 1
            correct += int(match)
            details.append({"imagen": image, "campo": field, "real": expected[field], "extraido": predicted.get(field), "acierto": match})
    percent = round(100 * correct / total, 2) if total else 0
    report = {"aciertos": correct, "campos_evaluados": total, "precision_exacta_pct": percent, "detalle": details}
    print(json.dumps(report, ensure_ascii=False, indent=2))
    print(f"Precision exacta campo por campo: {percent}%")
    save_result("precision", report)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="task", required=True)
    q = sub.add_parser("pregunta"); q.add_argument("imagen", type=Path); q.add_argument("pregunta")
    e = sub.add_parser("extraer"); e.add_argument("imagenes", nargs=3, type=Path)
    c = sub.add_parser("comparar"); c.add_argument("imagenes", nargs="+", type=Path)
    sub.add_parser("error"); sub.add_parser("precision")
    args = parser.parse_args()
    if not os.getenv("GROQ_API_KEY"):
        parser.error("Configura GROQ_API_KEY en el archivo .env")
    if args.task == "pregunta":
        print(ask_images([args.imagen], args.pregunta))
    elif args.task == "extraer":
        run_extract(args.imagenes)
    elif args.task == "comparar":
        if len(args.imagenes) not in (2, 3):
            parser.error("comparar acepta 2 o 3 imagenes")
        print(ask_images(args.imagenes, "Compara estas imagenes de componentes de computador. Describe similitudes y diferencias observables sin asumir datos no visibles."))
    elif args.task == "error":
        candidates = [p for p in sorted((ROOT / "imagenes").iterdir()) if p.is_file() and p.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}]
        if len(candidates) < 4:
            parser.error("Se necesitan cuatro imagenes para superar el limite de tres por solicitud")
        try:
            print(ask_images(candidates[:4], "Describe estas imagenes."))
        except Exception as exc:
            print(f"Error provocado por exceder el maximo de 3 imagenes: {type(exc).__name__}: {exc}")
    elif args.task == "precision":
        run_accuracy()


if __name__ == "__main__":
    main()








