import pytest
from your_module import Task, set_task_status, get_task_status # Replace your_module


def test_basic():
    assert True

def test_simple_math():
    assert 2 + 2 == 4

def test_set_awaiting_review_status():
    task_id = "test_task_1"
    set_task_status(task_id, "in_progress") # Set initial status
    assert get_task_status(task_id) == "in_progress"
    set_task_status(task_id, "awaiting_review")
    assert get_task_status(task_id) == "awaiting_review"

def test_get_awaiting_review_status():
    task_id = "test_task_2"
    set_task_status(task_id, "awaiting_review")
    assert get_task_status(task_id) == "awaiting_review"

def test_check_awaiting_review_status_after_completion():
    task_id = "test_task_3"
    set_task_status(task_id, "awaiting_review")
    assert get_task_status(task_id) == "awaiting_review"
    set_task_status(task_id, "completed") # Simulate completion
    assert get_task_status(task_id) == "completed" # Check if status changed correctly

