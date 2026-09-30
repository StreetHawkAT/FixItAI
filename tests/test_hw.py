import pytest
from core.hardware_detection import detect_hardware
def test_hw():
    hw = detect_hardware()
    assert 'architecture' in hw
