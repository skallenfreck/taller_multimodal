# Taller multimodal: visión y audio

Taller de análisis de periféricos y accesorios tecnológicos cotidianos. Se ejecuta por consola y usa Groq para visión, transcripción y generación de respuestas.

## Preparación

1. Cree un entorno e instale dependencias:

   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   python -m pip install -r requirements.txt
   ```

2. Copie `.env.example` como `.env` y agregue su `GROQ_API_KEY`.
3. Coloque cinco imágenes en `taller_multimodal/imagenes/` y cuatro grabaciones reales en `taller_multimodal/audios/`. Use al menos dos voces distintas y una grabación con ruido de fondo. Formatos de audio: WAV, MP3, M4A, OGG o WEBM; máximo 25 MB por archivo.

## Ejercicios de visión

```powershell
python -m taller_multimodal.vision pregunta taller_multimodal/imagenes/componente_mouse.jpg "Describe el mouse y sus botones visibles"
python -m taller_multimodal.vision extraer taller_multimodal/imagenes/componente_mouse.jpg taller_multimodal/imagenes/componente_teclado.jpg taller_multimodal/imagenes/componente_usb.jpg
python -m taller_multimodal.vision precision
python -m taller_multimodal.vision comparar taller_multimodal/imagenes/componente_mouse.jpg taller_multimodal/imagenes/componente_teclado.jpg
python -m taller_multimodal.vision error
```

`extraer` solicita cinco campos y valida que el JSON contenga las claves y los tipos esperados. Para medir aciertos, copie `taller_multimodal/valores_reales.json.example` a `taller_multimodal/valores_reales.json`, registre manualmente los valores observables de las tres imágenes y ejecute primero `extraer` y luego `precision`. La precisión reportada usa coincidencia exacta sin distinguir mayúsculas. `comparar` acepta dos o tres imágenes relacionadas. `error` envía cuatro imágenes para superar el límite de tres por solicitud y muestra el error devuelto por el servicio.

## Ejercicio de audio

Guarde los cuatro audios en `taller_multimodal/audios/` y ejecute `python -m taller_multimodal.audio`. El programa transcribe cada audio con Whisper, envía la transcripción al modelo de respuesta y guarda los resultados en `taller_multimodal/resultados/`.

## Claves

`.env.example` documenta los modelos. `.env` está excluido de Git. No publique claves ni datos personales en audios. Las solicitudes pueden consumir cuota y están sujetas a los límites vigentes de Groq.

Las fotos originales se conservan; el script reduce una copia a 1600 px antes de enviarla, para limitar el tamaño de la solicitud.

