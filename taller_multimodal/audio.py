"""Transcribe audios del taller con Whisper y envía cada transcripción al LLM."""
from __future__ import annotations

import argparse
import json
import os
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from groq import Groq

load_dotenv()
ROOT = Path(__file__).resolve().parent
AUDIO_DIR = ROOT / "audios"
OUTPUT = ROOT / "resultados"
SUPPORTED = {".wav", ".mp3", ".m4a", ".ogg", ".webm"}
MAX_BYTES = 25 * 1024 * 1024


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archivo", nargs="?", help="Nombre de un audio para procesar solo ese archivo")
    args = parser.parse_args()
    if not os.getenv("GROQ_API_KEY"):
        raise SystemExit("Configura GROQ_API_KEY en el archivo .env")
    files = sorted(p for p in AUDIO_DIR.iterdir() if p.is_file() and p.suffix.lower() in SUPPORTED)
    if args.archivo:
        files = [p for p in files if p.name == Path(args.archivo).name]
        if not files:
            raise SystemExit(f"No se encontro {args.archivo} dentro de {AUDIO_DIR}")
    if not files:
        raise SystemExit(f"Agrega audios wav/mp3/m4a/ogg/webm a {AUDIO_DIR}")
    client = Groq()
    records = []
    for path in files:
        if path.stat().st_size > MAX_BYTES:
            print(f"{path.name}: excede 25 MB; se omite.")
            continue
        try:
            with path.open("rb") as audio_file:
                transcript = client.audio.transcriptions.create(
                    file=(path.name, audio_file.read()),
                    model=os.getenv("TRANSCRIPTION_MODEL", "whisper-large-v3-turbo"),
                    language="es",
                    response_format="json",
                ).text
            answer = client.chat.completions.create(
                model=os.getenv("ANSWER_MODEL", "openai/gpt-oss-20b"),
                messages=[
                    {"role": "system", "content": "Eres un asistente educativo sobre componentes de computador. Responde en español, aclara incertidumbre y no inventes información."},
                    {"role": "user", "content": transcript},
                ],
                max_tokens=800,
            ).choices[0].message.content or ""
            record = {"archivo": path.name, "transcripcion": transcript, "respuesta": answer}
            records.append(record)
            print(f"\nAudio: {path.name}\nTranscripcion: {transcript}\nRespuesta: {answer}")
        except Exception as exc:
            print(f"{path.name}: error de API: {type(exc).__name__}: {exc}")
            records.append({"archivo": path.name, "error": str(exc)})
    OUTPUT.mkdir(parents=True, exist_ok=True)
    target = OUTPUT / f"audio_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    target.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nResultados guardados en {target}")


if __name__ == "__main__":
    main()

