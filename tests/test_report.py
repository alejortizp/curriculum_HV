from report import skill_weight


def test_weight_grows_with_required_count():
    assert skill_weight(3, 0, "covered") > skill_weight(1, 0, "covered")
