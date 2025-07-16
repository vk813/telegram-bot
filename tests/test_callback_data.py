import pytest
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))
from utils import safe_callback_data

@pytest.mark.parametrize("value", [
    123,
    "", 
    None,
    "a"*70,
    {"k":"v"},
    "тест",
    "valid_123",
])
def test_safe_callback_data(value):
    result = safe_callback_data(value)
    assert isinstance(result, str)
    assert result
    assert len(result.encode('utf-8')) <= 64
    assert all(c.isalnum() or c in "_-" for c in result)

