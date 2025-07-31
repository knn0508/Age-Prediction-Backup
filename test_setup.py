#!/usr/bin/env python3
"""
Simple test script to validate the age detection app dependencies
"""

import sys
import importlib

def test_import(module_name, package_name=None):
    """Test if a module can be imported"""
    try:
        importlib.import_module(module_name)
        print(f"✅ {package_name or module_name} - OK")
        return True
    except ImportError as e:
        print(f"❌ {package_name or module_name} - FAILED: {e}")
        return False

def main():
    print("🧪 Testing Age Detection App Dependencies...")
    print("=" * 50)
    
    # Test core dependencies
    tests = [
        ("streamlit", "Streamlit"),
        ("cv2", "OpenCV"),
        ("numpy", "NumPy"),
        ("pandas", "Pandas"),
        ("PIL", "Pillow"),
        ("sklearn", "Scikit-learn"),
        ("matplotlib", "Matplotlib"),
    ]
    
    passed = 0
    total = len(tests)
    
    for module, name in tests:
        if test_import(module, name):
            passed += 1
    
    print("=" * 50)
    print(f"📊 Results: {passed}/{total} dependencies available")
    
    # Test InsightFace separately (might require special handling)
    print("\n🔍 Testing InsightFace (may take longer)...")
    try:
        from insightface.app import FaceAnalysis
        print("✅ InsightFace - OK")
        passed += 1
        total += 1
    except Exception as e:
        print(f"❌ InsightFace - FAILED: {e}")
        total += 1
    
    print("=" * 50)
    print(f"🎯 Final Results: {passed}/{total} dependencies ready")
    
    if passed == total:
        print("🎉 All dependencies are ready! App should work correctly.")
        return 0
    else:
        print("⚠️  Some dependencies are missing. Please install them before running the app.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
