import pytest

def test_addition():
    assert 1 + 1 == 2
    assert 10 + 5 == 15
    assert -5 + 5 == 0

def test_subtraction():
    assert 5 - 2 == 3
    assert 10 - 15 == -5

def test_multiplication():
    assert 2 * 3 == 6
    assert 0 * 10 == 0

def test_division():
    assert 10 / 2 == 5.0
    with pytest.raises(ZeroDivisionError):
        10 / 0

def test_string_manipulation():
    assert "hello" + " world" == "hello world"
    assert len("test") == 4
    assert "hello".upper() == "HELLO"

def test_list_manipulation():
    my_list = [1, 2, 3]
    assert len(my_list) == 3
    assert 2 in my_list
    my_list.append(4)
    assert my_list == [1, 2, 3, 4]

# Add more tests here as needed, covering different aspects of your application's functionality.  Remember to replace these examples with tests relevant to your code.

