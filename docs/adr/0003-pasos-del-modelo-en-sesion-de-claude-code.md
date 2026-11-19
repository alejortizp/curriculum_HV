# ADR-0003: Los pasos del modelo se responden en una sesión de Claude Code; la API queda como deuda

## Status

Accepted. Reemplaza la decisión Q5 del diseño (extracción y redacción con script y API) como camino por defecto.

## Date

2026-11-19

## Context

El diseño usa un modelo de lenguaje en dos pasos: extraer la estructura de una
oferta y redactar los ajustes de un CV derivado. Se decidió hacerlo con un
script que llama a la API de Anthropic, para que fuera repetible con `make`.

Al implementarlo aparecieron dos hechos:

- La API se factura aparte de la suscripción de Claude. La primera llamada real
  falló con "Your credit balance is too low": la clave de `.env` no tiene saldo.
- El dueño del repo prefiere no asumir ese costo y hacer esos dos pasos en
  sesiones de Claude Code, que ya paga con su suscripción.

El código ya separaba el modelo del resto: todo lo que lo usa recibe una función
`complete(prompt, schema, ...)`, y solo `llm.py` importa `anthropic`. Esa
separación se pensó para las pruebas.

## Decision

El proveedor por defecto de los pasos del modelo es una sesión de Claude Code,
mediante intercambio de archivos (`session.py`):

1. El comando escribe `<paso>.prompt.md` y `<paso>.schema.json` y se detiene.
2. En una sesión, Claude lee el prompt y escribe `<paso>.response.json`.
3. El mismo comando, ejecutado de nuevo, lee la respuesta, comprueba que cumple
   el esquema y sigue: validación de la extracción o validador de ajustes, y
   render.

- Los archivos de la extracción viven en `applications/_inbox/<id>/` y se
  borran al terminar; los de la redacción, en la carpeta del CV derivado.
- Una respuesta que corresponde a un prompt anterior se descarta: el prompt
  lleva una huella de su contenido.
- En sesión no hay reintento automático. Si la respuesta se rechaza, el comando
  muestra los motivos y quien está en la sesión corrige el archivo y vuelve a
  ejecutar.
- El adaptador de la API (`llm.py`) se conserva, apagado. Se activa con
  `LLM_PROVIDER=api`.
- El validador no cambia: una respuesta escrita en sesión pasa por las mismas
  reglas que una de la API.

## Alternatives Considered

### Seguir con la API como único camino

- Pros: un solo comando por paso, sin sesión abierta; reintento automático;
  esquema forzado por la API.
- Cons: costo aparte de la suscripción; exige saldo en la Consola.
- Rejected: el dueño no quiere ese costo ahora.

### Llamar a `claude -p` desde el script

- Pros: un solo comando, sin sesión abierta, con la suscripción; admite
  `--json-schema`.
- Cons: cada llamada carga todo el entorno de Claude Code. Una pregunta trivial
  de prueba reportó un costo estimado de 1,10 USD de uso, más que la misma
  llamada por API. Si `ANTHROPIC_API_KEY` está en el entorno, factura a la API.
- Rejected: gasta más límite de uso por llamada que cualquiera de las otras
  opciones.

### Un comando de Claude Code que orqueste todo

- Pros: un solo paso para el usuario dentro de la sesión.
- Cons: la orquestación sería un texto de instrucciones, no código probado, y
  necesita igualmente el intercambio por archivos por debajo. `.claude/` está
  ignorado por git en este repo.
- Rejected: por ahora. Es una comodidad encima de esta decisión y se puede
  agregar sin cambiarla.

### Eliminar `llm.py` y la dependencia `anthropic`

- Pros: no queda código sin verificar ni una dependencia sin uso.
- Cons: retomar la API obliga a reescribir el adaptador.
- Rejected: conservarlo cuesta poco y deja la deuda a una variable de entorno
  de distancia.

## Consequences

- Registrar una oferta y generar un CV derivado no cuestan nada fuera de la
  suscripción, pero requieren una sesión abierta y dos ejecuciones por paso.
- El informe de mercado, `RENDER=1` y las pruebas no cambian: nunca usaron el
  modelo.
- La API ya no garantiza el esquema de la respuesta; `session.conforms()` lo
  comprueba.
- **Deuda técnica aceptada: ejecución automática por API.** El adaptador
  `llm.py` **nunca ha completado una llamada real**: no se ha verificado que la
  API acepte el modelo `claude-opus-5-5` con el respaldo ante rechazos tal como
  está escrito. Señal para retomarla: registrar ofertas con tanta frecuencia
  que el paso manual estorbe, o querer ejecutar el flujo sin sesión (por
  ejemplo, programado). Para pagarla: recargar saldo, poner `LLM_PROVIDER=api`,
  ejecutar la llamada de prueba de la tarea 4 del plan y corregir lo que falle.
- La calidad de la extracción y de la redacción depende del modelo de la
  sesión, no de una constante del código.
