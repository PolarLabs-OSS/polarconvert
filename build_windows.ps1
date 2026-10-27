Set-Location $PSScriptRoot
python -m pip install -r requirements.txt pyinstaller
python -m PyInstaller --noconfirm --onedir --windowed --name PolarConvert --icon PolarConvert.ico --add-data 'PolarConvert.ico;.' --add-data 'PolarConvert.png;.' polarconvert.py
