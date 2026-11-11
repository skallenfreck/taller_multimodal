# Taller multimodal

Taller sobre periféricos y accesorios tecnológicos cotidianos. Se ejecuta por consola desde la raíz del repositorio.

## Preparación

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Edita el archivo `.env` de la raíz y asigna tu clave de Groq a `GROQ_API_KEY`. Las otras variables seleccionan los modelos:

- `VISION_MODEL`: `qwen/qwen3.8-27b`
- `TRANSCRIPTION_MODEL`: `whisper-large-v3-turbo`
- `ANSWER_MODEL`: `openai/gpt-oss-20b`

No subas `.env` ni compartas su clave. `.env` está excluido en `.gitignore`.

## Ejercicios

Las cinco imágenes están en `taller_multimodal/imagenes/` y los cuatro audios en `taller_multimodal/audios/`.

```powershell
# Preguntar sobre una imagen
python -m taller_multimodal.vision pregunta taller_multimodal/imagenes/componente_mouse.jpg "Describe el mouse y sus botones visibles"

# Extraer cinco campos de tres imágenes y calcular coincidencia exacta
python -m taller_multimodal.vision extraer taller_multimodal/imagenes/componente_mouse.jpg taller_multimodal/imagenes/componente_teclado.jpg taller_multimodal/imagenes/componente_usb.jpg
python -m taller_multimodal.vision precision

# Comparar varias imágenes o provocar el límite de más de tres por solicitud
python -m taller_multimodal.vision comparar taller_multimodal/imagenes/componente_mouse.jpg taller_multimodal/imagenes/componente_teclado.jpg taller_multimodal/imagenes/componente_usb.jpg
python -m taller_multimodal.vision error

# Procesar todos los audios o solo un archivo
python -m taller_multimodal.audio
python -m taller_multimodal.audio audio_03_persona_b_ruido.m4a
```

La extracción usa `taller_multimodal/valores_reales.json`. Copia la plantilla `.example` y completa los valores observados antes de ejecutar `precision`. Los resultados se guardan en `taller_multimodal/resultados/`.

## Límites considerados

La visión admite hasta tres imágenes por solicitud; las fotos se reducen a 1600 px al enviarlas. Los audios usados son M4A y deben durar entre 10 y 30 segundos. Respeta también los límites vigentes de tamaño y consumo de Groq.
