#!/usr/bin/env python3
"""
Hydra Local Test Runner
=======================
Run this script locally to test the system WITHOUT Ollama.
It uses the built-in template engine to generate real articles
and RSS updates, so you can verify everything works before
deploying to GitHub Actions.

Usage:
    python3 scripts/local_test_run.py

No dependencies needed beyond Python 3.8+.
"""

import sys
import os

# Add the scripts directory to path
sys.path.insert(0, os.path.dirname(__file__))

# Monkey-patch ollama_generate to always return empty string
# so the template fallback is always used
import hydra_zero_key_generator as gen

original_ollama = gen.ollama_generate

def mock_ollama(prompt, expect_json=False):
    print("  [TEST MODE] Using template fallback (no Ollama needed).")
    return ""

gen.ollama_generate = mock_ollama

if __name__ == "__main__":
    print("\n" + "="*60)
    print("  HYDRA LOCAL TEST RUN (Template Mode — No Ollama)")
    print("="*60)
    gen.main()
    print("\nTest complete! Check the /articles/ folders and rss.xml files.")
    print("To use the real AI, install Ollama and run:")
    print("  ollama pull llama3.2:1b && ollama serve")
    print("  python3 scripts/hydra_zero_key_generator.py")
