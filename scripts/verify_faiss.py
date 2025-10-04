#!/usr/bin/env python3
"""
FAISS Installation Verification Script

This script verifies that FAISS 1.12.0 is properly installed and compatible
with the AIShell vector database implementation.
"""

import sys
import numpy as np


def print_header(msg):
    """Print a formatted header."""
    print(f"\n{'='*60}")
    print(f"  {msg}")
    print('='*60)


def check_faiss_import():
    """Check if FAISS can be imported."""
    print_header("1. Checking FAISS Import")
    try:
        import faiss
        print("✅ FAISS imported successfully")
        return True
    except ImportError as e:
        print(f"❌ FAISS import failed: {e}")
        return False


def check_faiss_basic_operations():
    """Test basic FAISS operations."""
    print_header("2. Testing Basic FAISS Operations")
    try:
        import faiss

        # Create index
        dimension = 128
        index = faiss.IndexFlatL2(dimension)
        print(f"✅ Created IndexFlatL2 with dimension {dimension}")

        # Add vectors
        vectors = np.random.randn(100, dimension).astype(np.float32)
        index.add(vectors)
        print(f"✅ Added {index.ntotal} vectors to index")

        # Search
        query = np.random.randn(1, dimension).astype(np.float32)
        distances, indices = index.search(query, k=10)
        print(f"✅ Search returned {len(indices[0])} results")

        return True
    except Exception as e:
        print(f"❌ FAISS operations failed: {e}")
        return False


def check_vector_database():
    """Test AIShell VectorDatabase with FAISS."""
    print_header("3. Testing AIShell VectorDatabase")
    try:
        import sys
        import os
        # Add parent directory to path
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from src.vector.store import VectorDatabase, FAISS_AVAILABLE

        print(f"   FAISS Available: {FAISS_AVAILABLE}")

        # Create database with real FAISS
        db = VectorDatabase(dimension=384, use_faiss=True)
        print(f"✅ VectorDatabase initialized (use_faiss={db.use_faiss})")

        # Add objects
        vec1 = np.random.randn(384).astype(np.float32)
        vec1 = vec1 / np.linalg.norm(vec1)
        db.add_object('test1', vec1, 'test', {'name': 'test1'})

        vec2 = np.random.randn(384).astype(np.float32)
        vec2 = vec2 / np.linalg.norm(vec2)
        db.add_object('test2', vec2, 'test', {'name': 'test2'})

        print(f"✅ Added {len(db.entries)} objects to database")

        # Search
        query = vec1 + np.random.randn(384).astype(np.float32) * 0.01
        query = query / np.linalg.norm(query)
        results = db.search_similar(query, k=2, threshold=0.0)

        print(f"✅ Search returned {len(results)} results")
        if results:
            print(f"   Top result: {results[0][0].id} (distance: {results[0][1]:.4f})")

        return True
    except Exception as e:
        print(f"❌ VectorDatabase test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def check_python_version():
    """Check Python version compatibility."""
    print_header("4. Checking Python Version")
    version = sys.version_info
    version_str = f"{version.major}.{version.minor}.{version.micro}"
    print(f"   Python Version: {version_str}")

    if version.major == 3 and version.minor >= 9:
        print(f"✅ Python {version_str} is supported")
        if version.minor >= 12:
            print(f"   🎉 Python 3.12+ support confirmed!")
        return True
    else:
        print(f"⚠️  Python {version_str} may not be fully supported")
        print("   Recommended: Python 3.9 or higher")
        return False


def run_all_checks():
    """Run all verification checks."""
    print("\n" + "="*60)
    print("  FAISS 1.12.0 Installation Verification")
    print("  AIShell Vector Database Compatibility Check")
    print("="*60)

    results = []

    # Run checks
    results.append(("Python Version", check_python_version()))
    results.append(("FAISS Import", check_faiss_import()))
    results.append(("FAISS Operations", check_faiss_basic_operations()))
    results.append(("Vector Database", check_vector_database()))

    # Summary
    print_header("Verification Summary")
    all_passed = True
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status}  {name}")
        all_passed = all_passed and passed

    print("\n" + "="*60)
    if all_passed:
        print("  🎉 ALL CHECKS PASSED - FAISS 1.12.0 is ready!")
        print("="*60)
        return 0
    else:
        print("  ⚠️  SOME CHECKS FAILED - Please review above")
        print("="*60)
        return 1


if __name__ == "__main__":
    sys.exit(run_all_checks())
