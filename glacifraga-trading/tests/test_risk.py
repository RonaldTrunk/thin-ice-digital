from app.risk import position_plan


def test_one_percent_risk_two_atr_stop():
    plan = position_plan(price=50, atr_value=2.5, account_size=100_000)
    assert plan is not None
    assert plan.stop_distance == 5.0
    assert plan.stop_loss == 45.0
    assert plan.take_profit == 60.0
    assert plan.shares == 200
    assert plan.qty == 200.0
    assert plan.risk_amount == 1000.0
    assert plan.capped is False


def test_max_position_cap():
    plan = position_plan(price=400, atr_value=2.5, account_size=100_000)
    assert plan is not None
    assert plan.shares == 25  # 10% of 100k / 400
    assert plan.qty == 25.0
    assert plan.capped is True


def test_rejects_untradeable_size():
    assert position_plan(price=50, atr_value=0, account_size=100_000) is None
    assert position_plan(price=50, atr_value=80, account_size=100) is None
