"""Market report for a role family: deterministic counting, no model involved."""

MIN_OFFERS = 10  # below this, the report warns that the signal is weak


def skill_weight(required: int, nice: int, state: str) -> float:
    """Peso con que una habilidad se ordena en el informe y en el objetivo.

    required/nice: en cuántas ofertas de la familia aparece como requerida o deseable.
    state: "covered", "mentioned" o "gap".
    Mayor peso = más arriba en el informe y más prioridad para destacarla en el CV.
    """
    # TODO(Alejandro): 5-10 líneas.
    raise NotImplementedError
