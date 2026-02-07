from rover.motors import MotorController


def test_open_lid_sets_aux_state():
    m = MotorController()
    m.open_lid()
    assert m.state["aux_lid_open"] is True


def test_close_lid_sets_aux_state_false():
    m = MotorController()
    m.open_lid()
    m.close_lid()
    assert m.state["aux_lid_open"] is False
