from games.towerdefense.waves import WAVES, get_wave

def test_waves_count():
    assert len(WAVES) == 10

def test_wave_has_required_fields():
    for wave in WAVES:
        assert "enemies" in wave
        assert "boss" in wave

def test_get_wave():
    wave = get_wave(1)
    assert wave["enemies"]["type"] == "zombie"
    assert wave["enemies"]["count"] == 15

def test_wave_5_has_boss():
    wave = get_wave(5)
    assert wave["boss"] is not None
