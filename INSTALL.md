# Backend Installation Troubleshooting

## Command Line Tools Issue

If you see an error like:
```
xcrun: error: invalid active developer path
```

### Solution 1: Reinstall Command Line Tools (Recommended)

1. Open Terminal
2. Run:
```bash
sudo xcode-select --reset
xcode-select --install
```

3. Follow the GUI prompt to install Command Line Tools
4. After installation, try installing requirements again:
```bash
pip install -r requirements.txt
```

### Solution 2: Use Pre-built Wheels

If you can't install Command Line Tools, we've pinned pydantic to version 2.4.2 which has pre-built wheels for most platforms. This should avoid the compilation issue.

### Solution 3: Use Python 3.11 or 3.12

Python 3.13 is very new and some packages may not have pre-built wheels yet. Consider using Python 3.11 or 3.12:

```bash
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Solution 4: Install via Homebrew

If you have Homebrew:
```bash
brew install python@3.12
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

