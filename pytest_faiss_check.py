"""Pytest configuration hook to ensure FAISS is installed."""

def pytest_configure(config):
    """Check FAISS installation before running tests."""
    try:
        import faiss
        print(f"\n✓ FAISS is installed and available")
        print(f"✓ FAISS IndexFlatL2: {hasattr(faiss, 'IndexFlatL2')}")
    except ImportError:
        import sys
        print("\n" + "="*70)
        print("ERROR: FAISS is required but not installed!")
        print("="*70)
        print("\nFAISS is now a required dependency for running tests.")
        print("\nInstall FAISS with:")
        print("  pip install faiss-cpu==1.12.0")
        print("\nOr if you have a GPU:")
        print("  pip install faiss-gpu==1.12.0")
        print("\n" + "="*70 + "\n")
        sys.exit(1)
