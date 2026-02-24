# Curriculum Vitae - Alejandro Ortiz Perdomo

CV profesional bilingüe (español/inglés) como AI Engineer & Machine Learning Engineer, construido con HTML + Tailwind CSS y generado desde una fuente de datos única. Incluye sistema de carta de presentación reutilizable y portfolio web publicado en GitHub Pages.

## Estructura del proyecto

```text
├── data/
│   ├── cv.json                  # Fuente única de datos del CV (editar aquí)
│   ├── cover_letter.json        # Datos de la carta de presentación (editar por empresa)
│   └── cover_letter_template.json # Plantilla vacía para nuevas cartas
├── templates/
│   ├── cv.html                  # Plantilla Jinja2 para CVs
│   ├── cover_letter.html        # Plantilla Jinja2 para carta de presentación (bilingüe)
│   ├── portfolio_base.html      # Plantilla base del portfolio (nav, footer, SEO, analytics)
│   ├── portfolio_index.html     # Plantilla página principal (hero, skills, about)
│   ├── portfolio_projects.html  # Plantilla proyectos (iterados desde cv.json)
│   └── portfolio_contact.html   # Plantilla contacto (formulario Formspree)
├── static/
│   ├── styles.css               # CSS compartido (layout A4, print, prose)
│   ├── ai-suite.js              # JS compartido (PDF, modal IA, Gemini API)
│   └── profile.jpg              # Foto de perfil (fuente canónica)
├── docs/                        # GitHub Pages (generado, no editar)
│   ├── index.html               # Página principal del portfolio
│   ├── projects.html            # Proyectos (desde cv.projects)
│   ├── contact.html             # Contacto con formulario Formspree
│   ├── CV_español.html          # CV español (generado directamente aquí)
│   ├── CV_english.html          # CV inglés (generado directamente aquí)
│   ├── static/                  # Copia de assets para los CVs
│   ├── profile.jpg              # Foto de perfil (copiada desde static/)
│   └── .nojekyll                # Evita procesamiento Jekyll
├── build.py                     # Script de generación HTML + PDF + portfolio
├── Makefile                     # Atajos de comandos
├── CV_español.pdf               # PDF generado
├── CV_english.pdf               # PDF generado
├── Carta_Presentacion.html      # Carta ES generada (no editar)
├── Carta_Presentacion.pdf       # PDF generado
├── Cover_Letter.html            # Carta EN generada (no editar)
├── Cover_Letter.pdf             # PDF generado
├── .env.example                 # Plantilla para variables de entorno
├── pyproject.toml               # Configuración del proyecto (uv)
└── README.md
```

## Cómo actualizar el CV

1. Editar `data/cv.json` con los cambios deseados
2. Ejecutar el build:

```bash
make
```

Esto genera automáticamente los CVs (HTML + PDF) y regenera el portfolio en `docs/`.

### Setup inicial (primera vez)

```bash
make setup
```

### Comandos disponibles

```bash
make              # Build todo: CVs (HTML + PDF) + portfolio en docs/
make build        # Solo CVs (HTML + PDF, ambos idiomas)
make html         # Solo generar HTMLs (sin PDFs)
make es           # Solo español (HTML + PDF)
make en           # Solo inglés (HTML + PDF)
make carta        # Carta de presentación (HTML + PDF, ambos idiomas)
make carta-es     # Carta solo en español
make carta-en     # Carta solo en inglés
make portfolio    # Generar portfolio en docs/ (GitHub Pages)
make clean        # Eliminar archivos generados
make open-es      # Generar HTML y abrir CV español en navegador
make open-en      # Generar HTML y abrir CV inglés en navegador
make open-carta   # Generar y abrir carta (ES) en navegador
make open-carta-en # Generar y abrir carta (EN) en navegador
make open-portfolio # Generar y abrir portfolio en navegador
make help         # Mostrar todos los comandos
```

### Perfiles customizables

El CV soporta variantes del perfil profesional para adaptarse al rol al que aplicas:

```bash
make es                        # Perfil por defecto (general)
make es PROFILE=ai-engineer    # Enfocado en GenAI/RAG/Agentes
make en PROFILE=ml-engineer    # Enfocado en ML predictivo
make build PROFILE=mlops       # Enfocado en CI/CD/deployment
```

Las variantes se definen en `data/cv.json` → `profiles`. Para agregar una nueva, añadir una clave con su texto `{"es": "...", "en": "..."}`.

También se puede usar `build.py` directamente para combinar flags:

```bash
uv run python build.py es --html-only
uv run python build.py carta --html-only
uv run python build.py en --html-only --profile ai-engineer
```

## Carta de Presentación

Sistema reutilizable y bilingüe para generar cartas de presentación personalizadas por empresa:

1. Copiar `data/cover_letter_template.json` a `data/cover_letter.json`
2. Llenar los campos de la empresa objetivo (empresa, cargo, contenido en ES y EN)
3. Ejecutar `make carta` (genera ambos idiomas) o `make carta-es` / `make carta-en`
4. Se generan `Carta_Presentacion.html` + `Cover_Letter.html` (+ PDFs)

Todos los campos soportan i18n con `{"es": "...", "en": "..."}`. Los datos personales (nombre, contacto, título, portfolio) se toman automáticamente de `data/cv.json`.

## Portfolio (GitHub Pages)

El proyecto incluye un portfolio web publicado en GitHub Pages desde la carpeta `docs/`.

**URL:** https://alejortizp.github.io/curriculum_HV/

### Generar el portfolio

```bash
make              # Genera todo: CVs + PDFs + portfolio
make portfolio    # Solo regenerar portfolio (requiere CVs HTML existentes)
```

El portfolio lee datos de `cv.json`, así que se mantiene sincronizado con el CV. Al agregar o editar proyectos, experiencia o datos personales en `cv.json`, el portfolio se actualiza automáticamente con `make`. Incluye:

- Página principal con perfil, habilidades y estadísticas
- Página de proyectos generada dinámicamente desde `cv.projects`
- Página de contacto con formulario funcional (Formspree)
- Descarga de CV bilingüe (dropdown español/inglés)
- Menú móvil responsive
- Meta tags SEO (Open Graph, Twitter Cards)
- Google Analytics (opcional)

### Configurar formulario de contacto

1. Crear cuenta en [formspree.io](https://formspree.io) y crear un formulario
2. Copiar el ID (ej: `xpzvqkdl`) y ponerlo en `data/cv.json` → `personal.formspree_id`
3. Ejecutar `make portfolio`

### Configurar Google Analytics (opcional)

1. Crear una propiedad en [analytics.google.com](https://analytics.google.com)
2. Copiar el Measurement ID (`G-XXXXXXXXXX`) y ponerlo en `data/cv.json` → `personal.google_analytics_id`
3. Ejecutar `make portfolio` — el script se inyecta solo si el ID tiene valor

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
- **Formspree** para formulario de contacto funcional (AJAX, sin backend)
- **Google Analytics** integración opcional para monitoreo de visitas
- **Material Symbols** para iconografía del portfolio
- **Space Grotesk** como fuente del portfolio

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
