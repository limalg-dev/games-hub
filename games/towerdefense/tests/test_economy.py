from games.towerdefense.economy import Economy


def test_economy_init():
    eco = Economy()
    assert eco.gold == 200
    assert eco.gems == 0


def test_economy_spend_gold():
    eco = Economy()
    result = eco.spend(50)
    assert result is True
    assert eco.gold == 150


def test_economy_spend_insufficient():
    eco = Economy()
    result = eco.spend(300)
    assert result is False
    assert eco.gold == 200


def test_economy_earn_gold():
    eco = Economy()
    eco.earn_gold(100)
    assert eco.gold == 300


def test_economy_earn_gems():
    eco = Economy()
    eco.earn_gems(5)
    assert eco.gems == 5
