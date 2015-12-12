# required-method: eq_

class TestEq(TestCase):
    def test_simple(self):
        assert 100 == 100

    def test_is(self):
        assert True is True
        assert None is None
        assert False is False

    def test_multiline(self):
        assert foo('bar', a=b) == 3615

    def test_custom_assert(self):
        return True is True
