import os

base_dir = r"c:\Users\aksha\OneDrive\Desktop\college\Hackthon\Fixit_ai\tests"
os.makedirs(base_dir, exist_ok=True)

test_files = {
    "test_audio.py": '''import pytest
from unittest.mock import patch
from diagnostics.audio import check_audio

@patch('diagnostics.audio.run_ps')
def test_audio_healthy(mock_run_ps):
    mock_run_ps.side_effect = ["Running", "Running", '[{"Name":"Audio","Status":"OK"}]']
    res = check_audio()
    assert res["status"] == "healthy"
''',
    "test_bluetooth.py": '''import pytest
from unittest.mock import patch
from diagnostics.bluetooth import check_bluetooth

@patch('diagnostics.bluetooth.run_ps')
def test_bluetooth_healthy(mock_run_ps):
    mock_run_ps.side_effect = ["Running", '[{"Name":"BT Adapter","Status":"OK"}]']
    res = check_bluetooth()
    assert res["status"] == "healthy"
''',
    "test_display.py": '''import pytest
from unittest.mock import patch
from diagnostics.display import check_display

@patch('diagnostics.display.run_ps')
def test_display_healthy(mock_run_ps):
    mock_run_ps.side_effect = ['[{"Name":"GPU","Status":"OK"}]', '[{"Name":"Monitor","Status":"OK"}]']
    res = check_display()
    assert res["status"] == "healthy"
''',
    "test_keyboard.py": '''import pytest
from unittest.mock import patch
from diagnostics.keyboard import check_keyboard

@patch('diagnostics.keyboard.run_ps')
def test_keyboard_healthy(mock_run_ps):
    mock_run_ps.return_value = '[{"Name":"KB","Status":"OK"}]'
    res = check_keyboard()
    assert res["status"] == "healthy"
''',
    "test_input.py": '''import pytest
from unittest.mock import patch
from diagnostics.input_devices import check_input

@patch('diagnostics.input_devices.run_ps')
def test_input_healthy(mock_run_ps):
    mock_run_ps.return_value = '[{"Name":"Mouse","Status":"OK"}]'
    res = check_input()
    assert res["status"] == "healthy"
''',
    "test_microphone.py": '''import pytest
from unittest.mock import patch
from diagnostics.microphone import check_microphone

@patch('diagnostics.microphone.run_ps')
def test_microphone_healthy(mock_run_ps):
    mock_run_ps.side_effect = ["Running", '[{"Name":"Mic","Status":"OK"}]']
    res = check_microphone()
    assert res["status"] == "healthy"
''',
    "test_usb.py": '''import pytest
from unittest.mock import patch
from diagnostics.usb import check_usb

@patch('diagnostics.usb.run_ps')
def test_usb_healthy(mock_run_ps):
    mock_run_ps.return_value = '[{"Name":"USBHub","Status":"OK"}]'
    res = check_usb()
    assert res["status"] == "healthy"
''',
    "test_printer.py": '''import pytest
from unittest.mock import patch
from diagnostics.printer import check_printer

@patch('diagnostics.printer.run_ps')
def test_printer_healthy(mock_run_ps):
    mock_run_ps.side_effect = ["Running", '[{"Name":"Print","PrinterStatus":3}]']
    res = check_printer()
    assert res["status"] == "healthy"
''',
    "test_battery.py": '''import pytest
from unittest.mock import patch
from diagnostics.battery import check_battery

@patch('diagnostics.battery.run_ps')
def test_battery_healthy(mock_run_ps):
    mock_run_ps.return_value = '[{"Name":"Bat","EstimatedChargeRemaining":100,"BatteryStatus":2}]'
    res = check_battery()
    assert res["status"] == "healthy"
''',
    "test_storage.py": '''import pytest
from unittest.mock import patch
from diagnostics.storage import check_storage

@patch('diagnostics.storage.run_ps')
def test_storage_healthy(mock_run_ps):
    mock_run_ps.return_value = '[{"DriveLetter":"C","SizeRemaining":50000000000,"Size":100000000000}]'
    res = check_storage()
    assert res["status"] == "healthy"
''',
    "test_performance.py": '''import pytest
from unittest.mock import patch
from diagnostics.performance import check_performance

@patch('diagnostics.performance.run_ps')
def test_performance_healthy(mock_run_ps):
    mock_run_ps.side_effect = ["10", '[{"FreePhysicalMemory":8000000,"TotalVisibleMemorySize":16000000}]']
    res = check_performance()
    assert res["status"] == "healthy"
''',
    "test_drivers.py": '''import pytest
from unittest.mock import patch
from diagnostics.drivers import check_drivers

@patch('diagnostics.drivers.run_ps')
def test_drivers_healthy(mock_run_ps):
    mock_run_ps.return_value = '[]'
    res = check_drivers()
    assert res["status"] == "healthy"
''',
    "test_windows.py": '''import pytest
from unittest.mock import patch
from diagnostics.windows import check_windows

@patch('diagnostics.windows.run_ps')
def test_windows_healthy(mock_run_ps):
    mock_run_ps.side_effect = ["Running", '[]']
    res = check_windows()
    assert res["status"] == "healthy"
'''
}

for filename, content in test_files.items():
    filepath = os.path.join(base_dir, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
