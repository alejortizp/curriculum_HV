# Curriculum Vitae - Alejandro Ortiz Perdomo

CV profesional bilingüe (español/inglés) como AI Engineer & Machine Learning Engineer, construido con HTML + Tailwind CSS y generado desde una fuente de datos única.

## Estructura del proyecto

```text
├── data/
│   └── cv.json              # Fuente única de datos del CV (editar aquí)
├── templates/
│   └── cv.html              # Plantilla Jinja2 compartida
├── build.py                 # Script de generación HTML + PDF
├── CV_español.html          # HTML generado (no editar directamente)
├── CV_english.html          # HTML generado (no editar directamente)
├── CV_español.pdf           # PDF generado
├── CV_english.pdf           # PDF generado
├── main.py                  # Entry point del proyecto
├── pyproject.toml           # Configuración del proyecto (uv)
└── README.md
```

## Cómo actualizar el CV

1. Editar `data/cv.json` con los cambios deseados
2. Ejecutar el build:

```bash
uv run python build.py
```

Esto genera automáticamente los 4 archivos: 2 HTMLs + 2 PDFs.

### Setup inicial (primera vez)

```bash
uv sync
uv run playwright install chromium
```

### Opciones del build

```bash
# Solo generar HTMLs (sin PDFs)
uv run python build.py --html-only

# Generar solo un idioma
uv run python build.py es
uv run python build.py en
```

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
