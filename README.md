# Curriculum Vitae - Alejandro Ortiz Perdomo

CV profesional bilingüe (español/inglés) como AI Engineer & Machine Learning Engineer, construido con HTML + Tailwind CSS.

## Estructura del proyecto

```text
├── CV_español.html     # CV en español
├── CV_english.html     # CV en inglés
├── CV_español.pdf      # PDF generado desde el HTML español
├── CV_english.pdf      # PDF generado desde el HTML inglés
├── main.py             # Entry point del proyecto
├── pyproject.toml      # Configuración del proyecto (uv)
└── README.md
```

## Tecnologías utilizadas

- **HTML5 + Tailwind CSS** (via CDN) para el diseño y maquetación
- **Font Awesome 6** para iconografía
- **Playwright** para generación de PDFs desde la terminal
- **html2pdf.js** como opción alternativa de descarga PDF desde el navegador
- **Gemini API** para funcionalidades de IA integradas (Elevator Pitch, Entrevista Técnica, Carta de Presentación, Gap Analysis)

## Generación de PDFs con Playwright

### Requisitos

```bash
npm install -g playwright
npx playwright install chromium
```

### Comandos para generar los PDFs

```bash
# CV en español
npx playwright pdf CV_español.html CV_español.pdf

# CV en inglés
npx playwright pdf CV_english.html CV_english.pdf
```

Si los archivos HTML usan rutas relativas o CDN que requieren red, se puede usar la ruta completa con `file://`:

```bash
npx playwright pdf file://$(pwd)/CV_español.html CV_español.pdf
npx playwright pdf file://$(pwd)/CV_english.html CV_english.pdf
```

### Opciones útiles

```bash
# Especificar formato de papel
npx playwright pdf --paper-format A4 CV_español.html CV_español.pdf

# Esperar a que carguen las fuentes/CDN (timeout en ms)
npx playwright pdf --wait-for-timeout 3000 CV_español.html CV_español.pdf
```

## Alternativa: PDF desde el navegador

Cada CV incluye un botón flotante "Guardar PDF" / "Save PDF" que usa la librería html2pdf.js para descargar directamente desde el navegador.

## AI Career Suite

Ambos CVs incluyen un modal interactivo con herramientas de IA (requiere API key de Gemini configurada en el código):

- **Elevator Pitch** - Genera un discurso profesional de 30 segundos
- **Entrevista Técnica** - Preguntas técnicas basadas en el perfil
- **Carta de Presentación** - Personalizada por empresa y cargo
- **Gap Analysis** - Comparativa del perfil contra un rol objetivo
