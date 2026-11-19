# ADR-0001: Historial de ofertas en archivos JSON locales, fuera de git

## Status

Accepted

## Date

2026-11-19

## Context

Se van a guardar las ofertas de empleo a las que se aplica o que se quieren
analizar, con su texto original y una extracción estructurada. Hasta ahora solo
existía `data/job_offer.json`, un archivo único que se sobrescribía con cada
oferta.

Condiciones que pesan en la decisión:

- El repositorio es público y GitHub Pages sirve `docs/`. Una oferta guardada
  revela a qué empresas se aplica y reproduce texto de terceros. Un archivo
  publicado no se puede retirar del historial de git sin reescribirlo.
- Un solo usuario, una sola máquina, sin escrituras concurrentes.
- Volumen esperado: decenas de ofertas, quizá unos pocos cientos con el tiempo.
- El resto del repo guarda sus datos en JSON legible y editable a mano
  (`data/cv.json`, `data/cover_letter.json`).
- El análisis del conjunto necesita recorrer todas las ofertas, no consultas
  cruzadas.

## Decision

Guardar un archivo JSON por oferta en `data/offers/`, carpeta ignorada por git.

- La ruta se puede reemplazar con la variable de entorno `OFFERS_DIR`, para
  apuntar a un repositorio privado sin tocar código.
- Un único módulo (`offers.py`) lee y escribe esos archivos. El resto del
  código pide ofertas por su interfaz y no conoce el formato de almacenamiento
  (patrón Repository).
- El texto original de la oferta se escribe una vez y no se modifica. La
  extracción es un derivado que se puede regenerar.

## Alternatives Considered

### SQLite

- Pros: consultas con SQL, filtros y agregaciones sin cargar todo en memoria,
  un solo archivo. Es la opción que más gustó al dueño del repo.
- Cons: archivo binario que no se puede leer, editar ni comparar a mano;
  introduce esquema y migraciones; el análisis previsto es un recorrido
  completo que no aprovecha un motor de consultas.
- Rejected: por ahora. Es excesivo para decenas de ofertas. Queda como deuda
  técnica aceptada; ver "Consequences".

### Un archivo JSONL de solo-agregar

- Pros: recorrido trivial, un solo archivo, agregar es escribir una línea.
- Cons: corregir una oferta a mano es incómodo, volver a extraer obliga a
  reescribir el archivo, y un error de formato en una línea afecta la lectura
  de todo.
- Rejected: la extracción se regenera, así que los registros no son de
  solo-agregar.

### Versionar las ofertas en este repositorio

- Pros: respaldo e historial sin infraestructura adicional.
- Cons: publica a qué empresas se aplica y texto ajeno; no se puede deshacer
  sin reescribir el historial de git.
- Rejected: la exposición es irreversible.

### Repositorio privado aparte desde el inicio

- Pros: respaldo e historial sin exponer nada.
- Cons: un segundo repositorio que mantener y sincronizar antes de saber si el
  historial llega a tener valor.
- Rejected: como punto de partida. `OFFERS_DIR` deja el camino abierto.

### Lectura directa de archivos desde cada script

- Pros: menos código al inicio, sin capa intermedia.
- Cons: cada script que lee ofertas conoce el formato; cambiar de
  almacenamiento obliga a tocarlos todos.
- Rejected: encarecería la migración a SQLite, que se quiere mantener barata.

## Consequences

- El historial no tiene respaldo ni versiones. Si se daña el disco, se pierde.
  Se mitiga apuntando `OFFERS_DIR` a un repositorio privado cuando el historial
  tenga valor que no se quiera perder.
- Las ofertas se pueden leer y corregir con un editor de texto.
- El identificador de la oferta es el nombre del archivo, lo que resuelve la
  colisión que tenía `applications/<empresa>/` con dos cargos en la misma
  empresa.
- El análisis lee todos los archivos en cada ejecución. Es irrelevante con
  cientos de ofertas.
- **Deuda técnica aceptada: migrar a SQLite.** Señal para retomarla: más de
  unas 500 ofertas, o una consulta que tarde más de un par de segundos, o la
  necesidad de consultas cruzadas que un recorrido no resuelva bien. La
  migración debe limitarse a reescribir `offers.py` y convertir los archivos
  existentes; si exige tocar otros módulos, el módulo dejó de aislar el
  almacenamiento y eso se corrige primero.
