# Curriculum Vitae - Alejandro Ortiz Perdomo

CV profesional bilingüe (español/inglés) como AI Engineer & Machine Learning Engineer, construido con HTML + Tailwind CSS y generado desde una fuente de datos única. Incluye sistema de carta de presentación reutilizable y portfolio web publicado en GitHub Pages.

## Estructura del proyecto

```text
├── data/
│   ├── cv.json              # Fuente única de datos del CV (editar aquí)
│   └── cover_letter.json    # Datos de la carta de presentación (editar por empresa)
├── templates/
│   ├── cv.html              # Plantilla Jinja2 para CVs
│   ├── cover_letter.html    # Plantilla Jinja2 para carta de presentación
│   ├── portfolio_base.html  # Plantilla base del portfolio (nav + footer)
│   ├── portfolio_index.html # Plantilla página principal
│   ├── portfolio_projects.html # Plantilla página de proyectos
│   └── portfolio_contact.html  # Plantilla página de contacto (Formspree)
├── docs/                    # Portfolio para GitHub Pages (generado)
│   ├── index.html           # Página principal
│   ├── projects.html        # Proyectos
│   ├── contact.html         # Contacto con formulario Formspree
│   ├── profile.jpg          # Foto de perfil
│   ├── CV_español.html      # Copia del CV español
│   ├── CV_english.html      # Copia del CV inglés
│   └── .nojekyll            # Evita procesamiento Jekyll
├── build.py                 # Script de generación HTML + PDF + portfolio
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
make portfolio    # Generar portfolio en docs/ (GitHub Pages)
make clean        # Eliminar archivos generados
make open-es      # Generar HTML y abrir CV español en navegador
make open-en      # Generar HTML y abrir CV inglés en navegador
make open-carta   # Generar y abrir carta de presentación en navegador
make open-portfolio # Generar y abrir portfolio en navegador
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

## Portfolio (GitHub Pages)

El proyecto incluye un portfolio web publicado en GitHub Pages desde la carpeta `docs/`.

**URL:** https://alejortizp.github.io/curriculum_HV/

### Generar el portfolio

```bash
make html         # Primero generar los CVs HTML
make portfolio    # Generar portfolio + copiar CVs a docs/
```

El portfolio lee datos de `cv.json`, así que se mantiene sincronizado con el CV. Incluye:
- Página principal con perfil, habilidades y estadísticas
- Página de proyectos iterada desde `cv.projects`
- Página de contacto con formulario funcional (Formspree)
- Descarga de CV en español e inglés

### Configurar formulario de contacto

1. Crear cuenta en [formspree.io](https://formspree.io) y crear un formulario
2. Copiar el ID (ej: `xpzvqkdl`) y ponerlo en `data/cv.json` → `personal.formspree_id`
3. Ejecutar `make portfolio`

### Configurar GitHub Pages

En el repositorio de GitHub:
1. Ir a **Settings → Pages**
2. En **Source** seleccionar **Deploy from a branch**
3. En **Branch** seleccionar `main` y carpeta `/docs`
4. Guardar — el sitio estará disponible en minutos

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
