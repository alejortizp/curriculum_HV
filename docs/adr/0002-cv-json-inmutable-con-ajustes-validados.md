# ADR-0002: `cv.json` no se modifica; los CV derivados salen de ajustes validados

## Status

Accepted

## Date

2026-11-19

## Context

El análisis de las ofertas guardadas muestra qué pide el mercado y qué de eso
ya respalda el CV. Hay que decidir cómo vuelve ese resultado al CV.

Condiciones que pesan en la decisión:

- `data/cv.json` es la única fuente de verdad. De él salen 10 CV diseñados, los
  CV para ATS y el portafolio público en GitHub Pages.
- La regla del proyecto es no inventar experiencia: solo reformular, reordenar
  y destacar lo que existe.
- Redactar un CV orientado a una oferta o a una familia de cargo requiere un
  modelo de lenguaje, y un modelo tiende a mencionar justo lo que la oferta
  pide y el CV no tiene.
- El repo ya aplica capas de cambios sobre los datos base en dos sitios:
  `profile_overrides` dentro de `cv.json` y `apply_tailoring()` en `tailor.py`.
- `cv.json` contiene varias versiones escritas a mano de la misma experiencia:
  las viñetas base y las de los perfiles `mlops` y `data-engineer`.
- El dueño del repo quiere que el sistema proponga cambios concretos, pero sin
  que `cv.json` se modifique. Entiende el CV derivado como un documento aparte,
  con su propio propósito: aprender de las ofertas y mejorar con el tiempo.
- El 2026-11-19 se generó a mano un CV derivado para una oferta real, siguiendo
  estas reglas. Mostró tres cosas: hizo falta reordenar la sección de
  habilidades, hizo falta elegir qué proyectos mostrar (el primer resultado
  tenía 5 páginas), y la oferta pedía clases de tecnología como "Lakehouse" o
  "NoSQL" que el CV respalda con herramientas concretas sin usar esas palabras.
- Ese mismo día apareció experiencia real que `cv.json` aún no nombraba. Su
  dueño la agregó primero a `cv.json`; el CV derivado la tomó de ahí.

## Decision

`data/cv.json` es de solo lectura para todo el sistema. Un CV derivado se
produce a partir de un archivo de ajustes separado que contiene solo las
diferencias (título, resumen, orden de la experiencia, viñetas, orden de las
habilidades y proyectos visibles) y que se aplica sobre los datos base al
renderizar (patrón Overlay).

- Un solo generador produce los ajustes, tanto para una oferta como para el
  informe de una familia de cargo.
- El generador recibe todas las variantes escritas a mano de cada entrada (la
  base y la de cada perfil) y puede elegir, combinar y reformular entre ellas.
- Un validador determinista revisa los ajustes antes de renderizar. Toma como
  original la unión de esas variantes y rechaza si aparece un vacío del
  objetivo, una cifra que no está en ninguna variante de esa entrada, más
  viñetas que la variante más larga, una empresa inexistente o un título que no
  fue escrito a mano.
- Sobre las habilidades y los proyectos, los ajustes solo reordenan y
  seleccionan. El validador comprueba que no se agregó ni quitó ninguna
  habilidad y que todo proyecto nombrado existe.
- Un término general ("Lakehouse", "NoSQL") se puede usar solo si el dueño lo
  declaró en el archivo de vocabulario junto con las habilidades del CV que lo
  respaldan, y solo en un texto que nombre al menos una de ellas. El modelo no
  decide qué término general está respaldado.
- Lo que no está en `cv.json` no entra a un CV derivado. La experiencia real
  que aún no se ha nombrado se agrega primero a `cv.json`.
- Los ajustes y los CV derivados se escriben en `applications/`, ignorada por
  git. Nada derivado se publica.
- El camino de vuelta a `cv.json` es manual: si un ajuste convence, su dueño lo
  copia.

## Alternatives Considered

### Solo un informe; el CV se edita a mano

- Pros: imposible que se cuele texto inventado; no hay generador ni validador
  que mantener.
- Cons: todo el trabajo de redacción queda manual; el informe dice qué
  destacar pero no cómo.
- Rejected: el dueño quiere una propuesta concreta que pueda revisar.

### El sistema propone un diff sobre `cv.json`

- Pros: un solo archivo de verdad; al aceptar el diff, todos los CV y el
  portafolio se actualizan.
- Cons: cada propuesta toca el archivo del que sale el sitio público; un diff
  aceptado sin leer con cuidado publica el error; no sirve para ajustes
  específicos de una oferta, que no deben quedar en el CV base.
- Rejected: el dueño pidió expresamente no modificar `cv.json`.

### Escritura automática en `cv.json`

- Pros: sin pasos manuales.
- Cons: cambia el CV público sin revisión y hace depender la regla de no
  inventar de la obediencia del modelo.
- Rejected: incompatible con la regla del proyecto.

### Copia completa de `cv.json` modificada

- Pros: fácil de entender; el render no cambia.
- Cons: la copia queda desactualizada cuando se edita `cv.json`; no se
  distingue qué cambió el modelo de lo que ya estaba.
- Rejected: pierde la posibilidad de revisar solo las diferencias.

### Guardar solo el HTML/PDF final

- Pros: ningún archivo intermedio.
- Cons: no se puede revisar qué cambió el modelo, ni regenerar tras editar
  `cv.json`, ni validar antes de renderizar.
- Rejected: elimina las dos barreras de revisión.

### Confiar solo en la instrucción del prompt

- Pros: sin código adicional; es lo que hacía `tailor.py`.
- Cons: ninguna verificación de que el modelo obedeció.
- Rejected: la barrera contra experiencia inventada no puede depender solo del
  modelo.

### Partir solo de las viñetas base

- Pros: un único original; el validador es más simple. Es lo que hacía
  `tailor.py`, que elegía un perfil pero solo lo usaba como etiqueta.
- Cons: el generador no ve las viñetas de los perfiles, que cuentan la misma
  experiencia desde otro ángulo.
- Rejected: deja fuera material escrito a mano que el CV derivado puede usar.

### Partir del perfil que corresponde a la familia

- Pros: el punto de partida ya está orientado al rol; el original sigue siendo
  uno por entrada.
- Cons: limita el CV derivado a una sola de las versiones escritas a mano, y
  los perfiles sin viñetas propias quedan igual que la base.
- Rejected: el CV derivado es un documento aparte que no tiene por qué seguir
  la frontera de un perfil. Los perfiles conservan su función como CV
  publicados.

### Limitar los ajustes al texto (título, resumen y viñetas)

- Pros: formato de ajustes más pequeño y validador más simple.
- Cons: el CV derivado conserva el orden de habilidades de la base, que empieza
  por lo menos pertinente para algunas ofertas; no puede mostrar un proyecto
  oculto que respalda un requisito; y la única forma de volver al límite de
  páginas es recortar viñetas.
- Rejected: la corrida manual necesitó las dos cosas. Reordenar y seleccionar
  no agrega contenido, así que no debilita la regla de no inventar.

### Tratar los términos generales como vacíos

- Pros: una sola regla; nada nuevo que mantener.
- Cons: el informe muestra como faltante algo que el CV respalda, y el
  validador prohíbe escribir una palabra cierta que la oferta busca.
- Rejected: produce informes engañosos y CV derivados peores sin ganar
  seguridad.

### Dejar que el modelo decida qué término general está respaldado

- Pros: sin lista que mantener; cubre términos nuevos automáticamente.
- Cons: es justo el juicio que el validador existe para no delegar; un modelo
  dispuesto a complacer encontrará respaldo para casi cualquier término.
- Rejected: la relación entre un término general y las habilidades que lo
  respaldan la declara el dueño del CV.

### Términos confirmados por el dueño dentro del archivo de ajustes

- Pros: rápido; no obliga a editar `cv.json` antes de generar.
- Cons: la verdad queda repartida en dos lugares, y lo confirmado para una
  oferta no sirve para la siguiente ni llega a los CV publicados.
- Rejected: se probó el 2026-11-19 y el dueño prefirió agregar la experiencia
  a `cv.json`.

## Consequences

- `cv.json` y todo lo que se publica a partir de él solo cambian por edición
  manual.
- Un CV derivado se regenera tras editar `cv.json` sin perder los ajustes, y un
  ajuste se descarta borrando un archivo.
- Los ajustes se pueden leer como un diff contra el CV base y editar a mano
  antes de renderizar.
- Hay tres barreras contra experiencia inventada: el prompt, el validador y la
  lectura de los ajustes. El validador cubre habilidades, cifras, número de
  viñetas, empresas y títulos.
- El validador **no** detecta exageraciones de redacción ni una entrada que
  mezcle dos historias de variantes distintas. Al permitir combinar variantes,
  ese segundo riesgo es mayor que si se partiera de un solo perfil; queda a la
  lectura humana y a una instrucción en el prompt.
- El original de cada entrada es una unión de variantes, lo que hace el
  validador más permisivo: una cifra escrita en cualquier perfil es válida en
  esa entrada.
- El validador depende de la clasificación de habilidades. Solo prohíbe los
  vacíos, es decir, lo que no aparece en ningún lugar de `cv.json`; lo que el
  CV menciona fuera de `tech_stack` se permite.
- `make apply` cambia de interfaz y de formato de salida:
  `tailoring_result.json` se reemplaza por el archivo de ajustes, y el modelo
  deja de elegir el perfil.
- Existen dos mecanismos de capas: `profile_overrides` (escrito a mano, dentro
  de `cv.json`, publicado) y los ajustes (generados, fuera de `cv.json`,
  locales). Los primeros son material de entrada para los segundos; unificarlos
  no es un objetivo.
- Las mejoras descubiertas en un CV derivado no llegan al CV base por sí solas.
- El archivo de vocabulario gana una segunda responsabilidad, los términos
  generales, y pasa a ser una pieza que su dueño mantiene. Un término general
  mal declarado permitiría una afirmación floja; lo acota que cada habilidad
  que lo respalda debe aparecer en `cv.json` y acompañar al término en el
  texto.
- Generar un CV derivado para una oferta que pide algo real pero aún no escrito
  exige editar `cv.json` antes. Es más lento, y a cambio la experiencia queda
  disponible para todos los CV.
- El límite de páginas del CV diseñado deja de depender solo de recortar
  viñetas: se puede recuperar ocultando un proyecto.
