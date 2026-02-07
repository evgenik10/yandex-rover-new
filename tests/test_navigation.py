from rover.navigation import Navigator


def test_haversine_non_zero():
    d = Navigator.haversine_m(60.1699, 24.9384, 60.1700, 24.9385)
    assert d > 0
