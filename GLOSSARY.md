# Curriculum HV

Generación de la hoja de vida, la carta de presentación y el portafolio de una
persona a partir de una sola fuente de datos, y adaptación de esos documentos a
las ofertas de empleo que le interesan.

## Language

### El CV

**CV base**:
La hoja de vida tal como la define su dueño, sin adaptar a ninguna oferta.
_Avoid_: CV original, CV maestro

**Perfil**:
Variante del CV base orientada a un rol, con su propio resumen profesional y,
si hace falta, su propio título y viñetas.
_Avoid_: versión, variante, rol

**CV derivado**:
Hoja de vida producida aplicando ajustes al CV base para un objetivo concreto.
_Avoid_: CV adaptado, CV personalizado, tailored CV

**Ajustes**:
Conjunto de diferencias respecto al CV base que produce un CV derivado: resumen,
orden de la experiencia y viñetas reformuladas.
_Avoid_: overlay, tailoring, cambios, parche

**Objetivo**:
Aquello hacia lo que se orienta un CV derivado: una oferta o el informe de
mercado de una familia de cargo.
_Avoid_: target, destino

**Aplicación**:
Los documentos que se envían a una oferta: el CV derivado y su carta.
_Avoid_: postulación, candidatura

### Las ofertas

**Oferta**:
Publicación de una empresa que busca cubrir un cargo, con su texto completo.
_Avoid_: vacante, job description, JD, posting

**Historial de ofertas**:
Todas las ofertas registradas, se haya aplicado a ellas o no.
_Avoid_: base de ofertas, corpus, banco de ofertas

**Extracción**:
Lectura estructurada de una oferta: familia de cargo, seniority, habilidades
requeridas y deseables, responsabilidades, años pedidos e idioma.
_Avoid_: parseo, resumen de la oferta

**Familia de cargo**:
Clasificación de una oferta según el rol que busca. Coincide con los perfiles
del CV base, más "otra" para lo que no encaja en ninguno.
_Avoid_: categoría, tipo de oferta, perfil

### El análisis

**Vocabulario de habilidades**:
Lista de nombres canónicos de las habilidades que el CV base presenta en su
sección de habilidades.
_Avoid_: taxonomía, catálogo, lista de skills

**Alias**:
Otra forma de escribir una misma habilidad, como "K8s" para "Kubernetes".
_Avoid_: sinónimo, variante

**Habilidad cubierta**:
Habilidad pedida por una oferta que está en el vocabulario de habilidades.
_Avoid_: match, coincidencia

**Habilidad mencionada**:
Habilidad pedida por una oferta que el CV base nombra en su experiencia o sus
proyectos, pero que no está en el vocabulario de habilidades.
_Avoid_: implícita, parcial

**Vacío**:
Habilidad pedida por una oferta que no aparece en ninguna parte del CV base.
_Avoid_: gap, brecha, faltante

**Término general**:
Nombre de una clase de tecnologías que una oferta pide en lugar de una
herramienta concreta, como "Lakehouse" o "NoSQL".
_Avoid_: categoría, término paraguas, concepto

**Cobertura**:
Proporción de las habilidades requeridas por una oferta que no son vacíos.
_Avoid_: match, puntaje, afinidad

**Informe de mercado**:
Resultado de contar, para una familia de cargo, qué habilidades piden sus
ofertas, con qué frecuencia y cuáles son vacíos.
_Avoid_: reporte, análisis, estudio de mercado
