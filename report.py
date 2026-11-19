"""Market report for a role family: deterministic counting, no model involved."""

MIN_OFFERS = 10  # below this, the report warns that the signal is weak


def skill_weight(required: int, nice: int, state: str) -> float:
    """Weight used to order a skill in the report and in a target.

    Market demand only: a required mention counts double a nice-to-have one, and
    the state (covered, mentioned, gap) does not change it, so the report shows
    what offers ask for most regardless of what the CV already lists.
    """
    return 2 * required + nice
