try:
    import sentence_transformers
    print("✅ sentence-transformers is installed")
except ImportError:
    print("❌ sentence-transformers is NOT installed")

try:
    import transformers
    print("✅ transformers is installed")
except ImportError:
    print("❌ transformers is NOT installed")
