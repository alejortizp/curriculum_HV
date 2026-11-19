# Historial de ofertas y CV derivados: diseño

- **Fecha:** 2026-11-19
- **Estado:** aprobado el 2026-11-19
- **Decisiones registradas:** [ADR-0001](../../adr/0001-historial-de-ofertas-en-archivos-json-locales.md), [ADR-0002](../../adr/0002-cv-json-inmutable-con-ajustes-validados.md)
- **Vocabulario:** [GLOSSARY.md](../../../GLOSSARY.md)

## Por qué

`make apply` adapta el CV a una oferta, pero trabaja con una sola a la vez: lee
`data/job_offer.json`, que se sobrescribe con la siguiente, y no guarda la oferta
junto al resultado. Nada compara lo que piden las ofertas con lo que muestra
`data/cv.json`.

Esta es una función nueva con un propósito propio: tomar información de las
ofertas, analizarla y mejorar con el tiempo. Su resultado es un documento
aparte. Los perfiles escritos a mano en `data/cv.json` siguen siendo los CV que
se publican y no cambian; aquí son material de partida.

Se quiere guardar cada oferta para dos usos:

1. Personalizar el CV y la carta para una oferta sin perder ni la oferta ni el
   resultado.
2. Analizar el conjunto de ofertas para ver qué se pide con más frecuencia, qué
   de eso ya muestra el CV y qué falta, y generar a partir de ese análisis un CV
   orientado a una familia de cargo.

## Objetivos

- Registrar una oferta pegando su texto, con un solo comando.
- Conservar el texto original de cada oferta sin modificarlo nunca.
- Producir un informe por familia de cargo que se pueda regenerar gratis y
  auditar: cada número sale de un conteo.
- Generar un CV derivado para una oferta o para una familia sin modificar
  `data/cv.json`.
- Impedir de forma automática que un CV derivado mencione habilidades que no
  aparecen en el CV o cifras que no están en el original.

## Fuera de alcance

- Seguimiento de aplicaciones (fechas, entrevistas, respuestas). Solo existe un
  campo `status` opcional y libre en cada oferta.
- Descargar ofertas desde una URL.
- Versión ATS de los CV derivados. Hoy `make apply` tampoco la genera; es la
  extensión más natural una vez esto funcione.
- Informe en HTML con gráficos.
- Evaluación de la calidad de la extracción con ofertas etiquetadas. Se retoma
  cuando haya unas 20 ofertas reales.
- Publicar cualquier CV derivado en `docs/`.

## Lo que haría de esto un fracaso

- Que una oferta, una empresa o un informe terminen en el repositorio público.
- Que un CV derivado afirme experiencia, habilidades o cifras que no están en
  `data/cv.json`.
- Que `data/cv.json` cambie sin que su dueño lo haya editado.

## Restricciones

- El repositorio es público y GitHub Pages sirve la carpeta `docs/`.
- `data/cv.json` es la única fuente de verdad del CV y solo se edita a mano.
- Python 3.13 con `uv`. Dependencias actuales: `jinja2`, `playwright`, `pypdf`,
  `anthropic`. Solo se agrega `pytest` como dependencia de desarrollo.
- Los PDF se generan con el Chrome del sistema, igual que hoy.
- El análisis del conjunto no usa el modelo.
- No hay ofertas previas que migrar: hoy no existen `data/job_offer.json` ni
  `applications/`.

## Enfoques considerados

**A. Archivar al aplicar.** `make apply` sigue leyendo `data/job_offer.json` y
copia la oferta al historial al terminar. Es el cambio más pequeño. Deja dos
lugares donde vive una oferta, las ofertas que no se personalizan nunca entran
al análisis, y no resuelve el análisis del conjunto.

**B. Historial como única entrada, análisis determinista y generador con
ajustes (elegido).** Toda oferta entra por el historial. El modelo interviene
en dos puntos: al extraer la estructura de una oferta y al redactar ajustes. El
análisis entre ambos es conteo. La salida es un archivo de ajustes validado que
se aplica sobre `data/cv.json` al renderizar. Cuesta rehacer la parte central de
`tailor.py`.

**C. Base de datos y modelo de punta a punta.** SQLite para el historial, el
modelo redacta el análisis leyendo todas las ofertas y escribe los cambios
directamente en `data/cv.json`. Da consultas reales y menos pasos manuales. El
análisis deja de ser repetible y auditable, el costo crece con el historial, y
la escritura automática en `data/cv.json` contradice la regla de no inventar
experiencia.

Se eligió B. Dos piezas de C quedan registradas: SQLite como deuda técnica con
señal de revisión (ADR-0001) y el modelo redactando sugerencias sobre los números
del informe como extensión posible.

## Arquitectura

```
texto de la oferta
   │  make offer-add                     modelo: una llamada por oferta
   ▼
historial de ofertas                     texto crudo + extracción, un JSON por oferta
   │  make offers-report                 sin modelo: conteo
   ▼
informe de mercado por familia           report.json + report.md
   │
   ├─ make apply OFFER=<id>       objetivo = una oferta  ─┐
   └─ make cv-market FAMILY=<f>   objetivo = un informe  ─┤
                                                          ▼
              generador (modelo) → ajustes → validador → render → HTML/PDF
```

`data/cv.json` se lee en la extracción (para el vocabulario), en el informe
(para clasificar las habilidades), en el generador y en el render. Ningún paso
lo escribe.

### Correspondencia entre el vocabulario y el código

El glosario está en español; el código del repo está en inglés.

| Término | En el código |
|---|---|
| Oferta | `offer` |
| Historial de ofertas | `offers` (módulo y carpeta) |
| Extracción | `extraction` |
| Familia de cargo | `role_family` |
| Vocabulario de habilidades | `vocabulary` |
| Habilidad cubierta | `covered` |
| Habilidad mencionada | `mentioned` |
| Vacío | `gap` |
| Término general | `general_term` |
| Cobertura | `coverage` |
| Informe de mercado | `report` |
| Objetivo | `target` |
| Ajustes | `adjustments` |
| CV derivado | `derived CV` |

## Componentes

### Historial de ofertas

Un módulo (`offers.py`) es el único código que lee o escribe archivos de
ofertas. El resto pide ofertas por su interfaz: agregar, obtener por
identificador, listar con filtros (familia, fecha) y guardar una extracción.
Migrar a SQLite debe consistir en reescribir este módulo.

- **Ubicación:** `data/offers/`, ignorada por git. La variable de entorno
  `OFFERS_DIR` la reemplaza, con la misma resolución que las claves de API
  (variable de entorno o `.env`).
- **Identificador:** `AAAA-MM-DD-empresa-cargo` con la fecha de registro, solo
  en ASCII (sin tildes ni ñ, a diferencia de `slugify()` actual, que las
  conserva). Si ya existe, se agrega un sufijo numérico. La función que lo
  calcula vive en un módulo que no importa `anthropic`.
- **Identificador provisional:** si no se dieron `COMPANY` y `ROLE`, la oferta
  se guarda primero como `AAAA-MM-DD-pendiente-<8 caracteres del hash>` y se
  renombra una sola vez, cuando la primera extracción identifica empresa y
  cargo. Mientras la extracción esté pendiente conserva el provisional.
- **Estabilidad:** una vez asignado el definitivo, el identificador no cambia.
  Volver a extraer no modifica `id`, `company` ni `role`; esos campos solo
  cambian por edición manual.
- **Duplicados:** se guarda el SHA-256 del texto crudo. Registrar un texto
  idéntico se rechaza indicando el identificador existente.
- **Inmutabilidad:** la sección `raw` se escribe una vez. Volver a extraer solo
  reemplaza `extraction`.

Forma de un archivo de oferta:

```json
{
  "id": "2026-11-19-empresa-ml-engineer",
  "added": "2026-11-19",
  "company": "Empresa",
  "role": "ML Engineer",
  "url": "",
  "status": null,
  "raw": { "text": "...", "sha256": "..." },
  "extraction": {
    "schema_version": 1,
    "model": "...",
    "extracted_at": "2026-11-19T13:30:00-05:00",
    "role_family": "ml-engineer",
    "seniority": "senior",
    "language": "es",
    "languages_required": [{ "language": "en", "level": "B2" }],
    "years_required": 3,
    "skills_required": [
      { "term": "K8s", "canonical": "Kubernetes" },
      { "term": "DBT Core", "canonical": "dbt" }
    ],
    "skills_nice": [],
    "responsibilities": ["..."]
  }
}
```

`company` y `role` del nivel superior son los definitivos: salen de los
parámetros del comando si se dieron y, si no, de lo que identificó el modelo en
la primera extracción. `extraction` es `null` mientras la extracción esté
pendiente.

### Registro de una oferta

`make offer-add FILE=<archivo>` (o el texto por entrada estándar), con
`COMPANY`, `ROLE` y `URL` opcionales.

1. Guarda el texto crudo. Si la extracción falla después, la oferta ya está a
   salvo con la extracción pendiente.
2. Extrae la estructura con el modelo.
3. Muestra empresa, cargo, familia y el identificador asignado.

`make offers-extract` vuelve a extraer las ofertas pendientes; con `FORCE=1`,
todas. Sirve cuando cambia el esquema o el vocabulario. `make offers-list`
muestra identificador, empresa, cargo, familia y estado.

### Extracción

Una llamada al modelo por oferta. Recibe el texto crudo, la lista de familias y
el vocabulario de habilidades. Devuelve los campos de `extraction`.

- **Familias de cargo:** las claves de `profiles` en `data/cv.json` menos
  `default`, más `other`. Se leen en tiempo de ejecución, así que un perfil
  nuevo crea su familia sin tocar código.
- **Seniority:** `junior`, `mid`, `senior`, `lead` o `null` si la oferta no lo
  dice.
- **Habilidades:** solo técnicas (herramientas, plataformas, lenguajes,
  métodos). Para cada una, `term` es como aparece en la oferta y `canonical`
  nunca es nulo: es el nombre del vocabulario al que corresponde o, si no
  corresponde a ninguno, el nombre corto habitual de esa tecnología. Así "dbt"
  y "DBT Core" se cuentan como una sola. En qué estado queda cada habilidad lo
  decide el código, no el modelo.
- **Idiomas:** `language` es el idioma en que está escrita la oferta y define
  el idioma de salida por defecto. `languages_required` son los idiomas que
  pide, con el nivel si lo dice. Se reportan aparte y no cuentan para la
  cobertura.
- Las habilidades blandas no se extraen como habilidades; si importan, quedan
  en `responsibilities`.
- La respuesta se valida contra el esquema. Si no cumple, se reintenta una vez
  y después falla con un error claro, dejando la extracción pendiente.

### Vocabulario de habilidades y estados

Los nombres canónicos del vocabulario son los de `tech_stack` en
`data/cv.json` (49 hoy). `tech_stack` no contiene todo lo que el CV menciona:
FAISS, Pandas, Power BI, OCR y RAG aparecen entre 7 y 25 veces en las viñetas y
los proyectos, y ninguno es un nombre de `tech_stack`. Por eso cada habilidad
pedida por una oferta queda en uno de tres estados:

| Estado | Condición | Qué significa |
|---|---|---|
| Cubierta | Su nombre canónico está en `tech_stack` | El CV la lista como habilidad |
| Mencionada | No está en `tech_stack`, pero aparece en el texto de `data/cv.json` | El CV la respalda; es candidata a agregarse a `tech_stack` |
| Vacío | No aparece en `data/cv.json` | El CV no la respalda |

Un archivo que sí se versiona, `data/skills_vocabulary.json`, guarda los alias
y los términos generales. No contiene nada privado y solo lo edita el dueño del
CV; el modelo nunca lo escribe.

```json
{
  "aliases": {
    "K8s": "Kubernetes",
    "MLflow": "Databricks + MLflow",
    "DBT Core": "dbt"
  },
  "general_terms": {
    "Lakehouse": ["Delta Lake", "Unity Catalog"],
    "NoSQL": ["DynamoDB"]
  }
}
```

**Términos generales.** Una oferta puede pedir una clase de tecnologías en
lugar de una herramienta: Lakehouse, Data Lake, NoSQL, bases de datos
relacionales. El CV no usa esas palabras, pero nombra herramientas que
pertenecen a esa clase. Sin tratamiento propio serían vacíos: el informe los
mostraría como algo que falta y el validador prohibiría escribirlos aunque sean
ciertos. `general_terms` relaciona cada término general con las habilidades del
CV que lo respaldan.

- Un término general declarado toma el mejor estado de sus habilidades: es
  cubierto si alguna es cubierta y mencionado en otro caso.
- Cada habilidad listada debe ser cubierta o mencionada. Si alguna es un vacío,
  el comando falla: no se puede declarar un término general respaldado por algo
  que el CV no nombra.
- Un término general sin declarar es un vacío, como cualquier otro. El informe
  no propone términos generales; su dueño decide cuáles declarar al leer la
  lista de vacíos.
- "Categoría" queda reservada para los grupos de la sección de habilidades
  (`tech_stack[].category`), que ya usan ese nombre.

Reglas, todas deterministas:

- Un alias puede apuntar a un nombre del vocabulario o a cualquier otro nombre.
  Lo segundo sirve para agrupar variantes de un mismo vacío.
- Al resolver el canónico de una habilidad, el archivo de alias tiene prioridad
  sobre lo que asignó el modelo. Así una corrección de alias surte efecto sin
  volver a llamar al modelo.
- "Aparece en el texto" significa que el nombre canónico o alguno de sus alias
  está en cualquier valor de texto de `data/cv.json`, en cualquiera de los dos
  idiomas, sin distinguir mayúsculas y como término completo: no cuenta si está
  pegado a letras, dígitos o guion. Esto evita que "R" coincida con "R-1".
- El alias también cubre nombres compuestos de `tech_stack` como
  `Databricks + MLflow`, que de otro modo dejarían "MLflow" como mencionada.

### Informe de mercado

`make offers-report`, con `FAMILY` y `SINCE=AAAA-MM-DD` opcionales. Sin
`FAMILY` genera un informe por cada familia que tenga ofertas. No usa el modelo.

Contenido por familia:

- Número de ofertas y rango de fechas.
- Por habilidad: en cuántas ofertas aparece como requerida y como deseable, y
  su estado. Un término general declarado se muestra con las habilidades que lo
  respaldan.
- Vacíos ordenados por frecuencia.
- Mencionadas ordenadas por frecuencia: las candidatas a agregar a
  `tech_stack`.
- Cubiertas ordenadas por frecuencia: las que conviene destacar.
- Cobertura por oferta: proporción de habilidades requeridas que no son vacíos.
- Distribución de seniority, mediana de años pedidos, idioma de las ofertas e
  idiomas requeridos.
- Las responsabilidades de cada oferta, sin agregar, para el generador.

Salida en `applications/_market/<familia>/`: `report.json` para el generador y
`report.md` para leer, ambos del mismo cálculo. Con menos de 10 ofertas en la
familia, el informe lo advierte al inicio: la señal es débil. Las ofertas con
extracción pendiente se excluyen y se listan.

### Objetivo y generador

Un solo generador produce ajustes a partir de `data/cv.json` y un objetivo. El
objetivo se construye desde una oferta o desde un informe y tiene la misma
forma en ambos casos:

- tipo (`offer` o `family`) y etiqueta;
- idioma de salida;
- habilidades cubiertas y mencionadas a destacar, ordenadas por peso;
- términos generales declarados que la oferta o la familia piden, cada uno con
  las habilidades que lo respaldan;
- vacíos, con sus alias, que no se pueden mencionar;
- responsabilidades;
- contexto: empresa y cargo, o familia y número de ofertas;
- texto crudo de la oferta, solo cuando el objetivo es una oferta. Es el único
  campo que distingue ambos tipos y existe para que la carta tenga contexto de
  la empresa.

**Material de partida.** El generador recibe todo lo escrito a mano, no solo
el perfil de la familia: para cada entrada de experiencia, las viñetas base y
las de cada perfil que las reemplaza en `profile_overrides`; todos los
resúmenes de `profiles`; y todos los títulos. Puede elegir, reordenar, combinar
y reformular entre esas variantes. El CV derivado es un documento aparte con su
propio propósito, así que aprovecha todo el material; los perfiles publicados
no cambian.

Recibe además la sección de habilidades y la lista completa de proyectos y
proyectos académicos, incluidos los que `data/cv.json` oculta del CV diseñado.
Sobre ellos solo puede reordenar y seleccionar: no agrega habilidades ni edita
proyectos.

Comandos:

- `make apply OFFER=<id>` genera CV derivado y carta. El idioma es el de la
  oferta; `OFFER_LANG` lo reemplaza. Sin `OFFER`, falla explicando el flujo
  nuevo.
- `make cv-market FAMILY=<familia>` genera solo el CV derivado. Regenera el
  informe de esa familia antes de usarlo. Idioma `es` por defecto; `OFFER_LANG`
  lo cambia.
- `HTML=1` omite los PDF en ambos, como hoy.

El prompt conserva las reglas actuales de `tailor.py`: no inventar, mantener
fechas, empresas y cifras, solo reformular, reordenar y destacar. Agrega una:
al combinar variantes, cada entrada debe seguir contando una sola historia
coherente.

### Ajustes

El archivo de ajustes contiene solo las diferencias respecto a `data/cv.json`:

```json
{
  "target": { "kind": "offer", "id": "2026-11-19-empresa-ml-engineer" },
  "lang": "es",
  "profile": "ml-engineer",
  "title": "Machine Learning Engineer | AI Engineer",
  "summary": "...",
  "experience_order": ["Periferia IT Group", "Global Hitss"],
  "experience": { "Periferia IT Group": ["viñeta", "viñeta"] },
  "tech_stack_order": [
    { "category": "MLOps & Engineering", "first": ["Python", "ETL"] },
    { "category": "Azure AI & Cloud", "first": ["Databricks + MLflow"] }
  ],
  "projects_shown": ["NL-to-SQL/Pandas Agent"],
  "academic_shown": ["Marketplace de Envíos Event-Driven en AWS"]
}
```

- Los ajustes se aplican sobre los datos base de `data/cv.json`. Una entrada
  que no aparece en `experience` conserva sus viñetas base.
- `profile` lo fija el código, no el modelo: es el perfil que corresponde a la
  familia del objetivo, y `default` para la familia `other`. Solo se usa como
  etiqueta al renderizar, igual que hoy.
- `title` es opcional y debe ser uno de los títulos escritos a mano: el base o
  el de algún perfil.
- `experience` se indexa por empresa, igual que `profile_overrides`. Hoy las 7
  empresas son únicas; si dejan de serlo, aplicar ajustes debe fallar con un
  error en lugar de elegir una.
- `experience_order` incluye todas las entradas que existen en ese idioma.
- `tech_stack_order` reordena la sección de habilidades sin agregar ni quitar
  ninguna. Los grupos van en el orden dado y los no listados conservan su orden
  relativo al final. Dentro de un grupo, las líneas cuya primera habilidad está
  en `first` van primero, en ese orden. Es opcional.
- `projects_shown` y `academic_shown` son los títulos de los proyectos que
  muestra el CV diseñado, en ese orden; los demás se ocultan. Pueden incluir
  proyectos que `data/cv.json` oculta. Si se omiten, se respeta la marca `cv`
  de `data/cv.json`. Son también la palanca para volver al límite de páginas
  sin recortar viñetas.
- `build.py` gana una función que aplica ajustes sobre los datos del CV, junto
  a `apply_profile_overrides()`. Una empresa desconocida es un error, como allí.
- La carta, cuando el objetivo es una oferta, va en un archivo aparte con la
  forma de `data/cover_letter.json` en un solo idioma.
- Editar el archivo de ajustes a mano y volver a renderizar sin llamar al
  modelo debe ser posible (`make apply OFFER=<id> RENDER=1` o equivalente). El
  validador se ejecuta también en ese caso.

Salida:

- `applications/<id-oferta>/`: `adjustments.json`, `cover_letter.json`, CV y
  carta en HTML y PDF, `static/`.
- `applications/_market/<familia>/`: `report.json`, `report.md`,
  `adjustments.json`, CV en HTML y PDF, `static/`.

`applications/` sigue ignorada por git.

### Validador

Determinista. Se ejecuta sobre los ajustes y sobre la carta antes de
renderizar. El "original" de una entrada de experiencia es la unión de todas
sus variantes escritas a mano en ese idioma. Rechaza si:

1. Algún texto menciona un vacío del objetivo o uno de sus alias, con la misma
   comparación de término completo del vocabulario. En la carta quedan exentos
   el nombre de la empresa y el del cargo tal como están en la oferta, porque
   un cargo puede incluir un vacío en su propio título.
2. Una viñeta contiene una cifra que no está en ninguna variante original de
   esa misma entrada, o el resumen o la carta contienen una cifra que no está
   en el texto de `data/cv.json` en ese idioma. La fecha de la carta queda
   exenta.
3. Una entrada tiene más viñetas que su variante original más larga.
4. Aparece una empresa que no existe en `data/cv.json`, falta una entrada en
   `experience_order`, o `title` no es uno de los títulos escritos a mano.
5. `tech_stack_order` nombra un grupo o una habilidad que no existe, o
   `projects_shown` o `academic_shown` nombran un proyecto que no existe. Tras
   aplicar el orden, el conjunto de habilidades debe ser idéntico al de
   `data/cv.json`.
6. Un texto usa un término general declarado sin nombrar, en la misma viñeta o
   en el mismo párrafo, al menos una de las habilidades que lo respaldan. Así
   "Lakehouse" solo aparece junto a "Delta Lake" o "Unity Catalog".

Si rechaza, el generador reintenta una vez pasando los motivos al modelo. Si
vuelve a fallar, el comando termina con error, no renderiza y deja el resultado
rechazado en `adjustments.rejected.json` con los motivos.

Lo que el validador no cubre queda a la lectura del archivo de ajustes:

- exageraciones de redacción;
- una entrada que mezcla dos historias de variantes distintas;
- el límite de 4 páginas del CV diseñado. La regla 3 lo acota pero no lo
  garantiza, así que el comando informa el número de páginas del PDF y avisa si
  supera 4. Se corrige quitando un proyecto de `projects_shown` o
  `academic_shown` y volviendo a renderizar.

Estas reglas se probaron a mano el 2026-11-19 con una oferta real, antes de
implementar nada. De esa corrida salieron `tech_stack_order`, la selección de
proyectos y los términos generales: el primer CV derivado tenía 5 páginas y se
resolvió ocultando un proyecto académico.

## Qué se retira

- `data/job_offer_template.json` y la lectura de `data/job_offer.json`.
- La línea `data/job_offer.json` de `.gitignore`, reemplazada por `data/offers/`.
- `tailoring_result.json`, reemplazado por `adjustments.json`.
- La lista de perfiles escrita a mano en el prompt de `tailor.py`, y la
  elección del perfil por el modelo.

`CLAUDE.md`, `README.md` y `make help` se actualizan con el flujo nuevo.

## Pruebas

`pytest` como dependencia de desarrollo y `make test`. Cubren lo determinista:

- historial: agregar, identificador, identificador provisional y su renombrado
  único, sufijo por colisión, duplicado por hash, inmutabilidad del texto
  crudo, ruta por `OFFERS_DIR`;
- vocabulario: alias, prioridad del alias sobre el modelo, los tres estados,
  coincidencia de término completo con términos cortos, términos generales
  (estado heredado y fallo si una habilidad que lo respalda es un vacío);
- informe: frecuencias, cobertura, listas por estado, filtro por fecha,
  advertencia por pocas ofertas;
- validador: cada regla de rechazo, las exenciones y un caso que pasa;
- aplicación de ajustes sobre los datos del CV, incluidos el orden de
  habilidades y la selección de proyectos.

Las llamadas al modelo pasan por una función que las pruebas sustituyen por
respuestas guardadas. Ninguna prueba llama a la API.

## Entregas

Cada una funciona por separado.

1. **Registro y extracción:** historial, vocabulario, `offer-add`,
   `offers-extract`, `offers-list`, pruebas.
2. **Informe de mercado:** `offers-report`.
3. **Generador unificado:** objetivo, ajustes, validador, `make apply
   OFFER=<id>` y retiro del flujo anterior.
4. **CV por familia:** `make cv-market`.

Las entregas 2 y 4 solo aportan cuando haya ofertas acumuladas.

## Queda a criterio de quien implementa

- Organización de los módulos: planos en la raíz, como `build.py` y `tailor.py`
  hoy, o un paquete.
- Nombres exactos de funciones y de los archivos de la interfaz de línea de
  comandos.
- Identificadores de modelo, en una constante por tarea (extracción y
  redacción). El actual, `claude-sonnet-4-20250514`, se reemplaza por modelos
  vigentes verificados contra la documentación de la API al implementar.
- Mecanismo para forzar la respuesta estructurada del modelo.
- Redacción de los prompts y formato exacto de `report.md`.
- Peso con que se ordenan las habilidades a destacar (por ejemplo, requeridas
  por encima de deseables, cubiertas por encima de mencionadas).
- Contenido inicial de `data/skills_vocabulary.json`.
