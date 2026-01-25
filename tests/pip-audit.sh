#!/bin/bash
# Run pip-audit for dependency vulnerability scanning
source venv/Scripts/activate
pip install pip-audit
pip-audit
