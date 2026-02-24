# Curriculum Vitae - Alejandro Ortiz Perdomo

CV profesional bilingüe (español/inglés) como AI Engineer & Machine Learning Engineer, construido con HTML + Tailwind CSS y generado desde una fuente de datos única. Incluye sistema de carta de presentación reutilizable.

## Estructura del proyecto

```text
├── data/
│   ├── cv.json              # Fuente única de datos del CV (editar aquí)
│   └── cover_letter.json    # Datos de la carta de presentación (editar por empresa)
├── templates/
│   ├── cv.html              # Plantilla Jinja2 para CVs
│   └── cover_letter.html    # Plantilla Jinja2 para carta de presentación
├── build.py                 # Script de generación HTML + PDF
├── Makefile                 # Atajos de comandos (make build, make carta, etc.)
├── CV_español.html          # HTML generado (no editar directamente)
├── CV_english.html          # HTML generado (no editar directamente)
├── CV_español.pdf           # PDF generado
├── CV_english.pdf           # PDF generado
├── Carta_Presentacion.html  # HTML generado (no editar directamente)
├── Carta_Presentacion.pdf   # PDF generado
├── .env.example             # Plantilla para variables de entorno
├── pyproject.toml           # Configuración del proyecto (uv)
└── README.md
```

## Cómo actualizar el CV

1. Editar `data/cv.json` con los cambios deseados
2. Ejecutar el build:

```bash
make
```

Esto genera automáticamente los 4 archivos: 2 HTMLs + 2 PDFs.

### Setup inicial (primera vez)

```bash
make setup
```

### Comandos disponibles

```bash
make              # Build HTML + PDF (ambos idiomas del CV)
make html         # Solo generar HTMLs (sin PDFs)
make es           # Solo español (HTML + PDF)
make en           # Solo inglés (HTML + PDF)
make carta        # Generar carta de presentación (HTML + PDF)
make clean        # Eliminar archivos generados
make open-es      # Generar HTML y abrir CV español en navegador
make open-en      # Generar HTML y abrir CV inglés en navegador
make open-carta   # Generar y abrir carta de presentación en navegador
make help         # Mostrar todos los comandos
```

También se puede usar `build.py` directamente para combinar flags:

```bash
uv run python build.py es --html-only
uv run python build.py carta --html-only
```

## Carta de Presentación

Sistema reutilizable para generar cartas de presentación personalizadas por empresa:

1. Editar `data/cover_letter.json` con los datos de la empresa objetivo (empresa, cargo, contenido)
2. Ejecutar `make carta`
3. Se generan `Carta_Presentacion.html` + `Carta_Presentacion.pdf`

Los datos personales (nombre, contacto, título) se toman automáticamente de `data/cv.json`.

## Tecnologías utilizadas

- **Jinja2** para templating desde una fuente de datos única (`data/cv.json`)
- **Playwright (Python)** para generación automática de PDFs
- **HTML5 + Tailwind CSS** (via CDN) para el diseño y maquetación
- **Font Awesome 6** para iconografía
- **html2pdf.js** como opción alternativa de descarga PDF desde el navegador
- **Gemini API** para funcionalidades de IA integradas (Elevator Pitch, Entrevista Técnica, Carta de Presentación, Gap Analysis)

## Alternativa: PDF desde el navegador

Cada CV incluye un botón flotante "Guardar PDF" / "Save PDF" que usa la librería html2pdf.js para descargar directamente desde el navegador.

## AI Career Suite

Ambos CVs incluyen un modal interactivo con herramientas de IA (requiere API key de Gemini):

- **Elevator Pitch** - Genera un discurso profesional de 30 segundos
- **Entrevista Técnica** - Preguntas técnicas basadas en el perfil
- **Carta de Presentación** - Personalizada por empresa y cargo
- **Gap Analysis** - Comparativa del perfil contra un rol objetivo

Para configurar la API key, crear un archivo `.env` en la raíz del proyecto:

```
GEMINI_API_KEY=tu_api_key_aquí
```
