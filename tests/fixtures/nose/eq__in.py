# required-method: eq_

class TestEq(TestCase):
    def test_simple(self):
        eq_(100, 100)

    def test_is(self):
        eq_(True, True)
        eq_(None, None)
        eq_(False, False)

    def test_multiline(self):
        eq_(foo('bar',
                a=b), 3615)
