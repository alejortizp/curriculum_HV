from report import skill_weight


def test_weight_grows_with_required_count():
    assert skill_weight(3, 0, "covered") > skill_weight(1, 0, "covered")


def test_one_required_mention_is_worth_two_nice_ones():
    assert skill_weight(1, 0, "covered") == skill_weight(0, 2, "covered")


def test_state_does_not_change_the_weight():
    assert skill_weight(2, 1, "covered") == skill_weight(2, 1, "mentioned") == skill_weight(2, 1, "gap")


def test_skill_nobody_asks_for_weighs_nothing():
    assert skill_weight(0, 0, "covered") == 0
