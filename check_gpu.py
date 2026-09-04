"""
Check GPU availability and PyTorch CUDA setup
"""
import torch
import sys

print("=" * 60)
print("GPU & CUDA Check for EduClassify")
print("=" * 60)

# Check PyTorch version
print(f"\n📦 PyTorch Version: {torch.__version__}")

# Check CUDA availability
cuda_available = torch.cuda.is_available()
print(f"\n🔥 CUDA Available: {cuda_available}")

if cuda_available:
    print(f"✅ GPU DETECTED - Training & Prediction akan menggunakan GPU")
    print(f"\n📊 GPU Information:")
    print(f"   - GPU Count: {torch.cuda.device_count()}")
    print(f"   - Current Device: {torch.cuda.current_device()}")
    print(f"   - Device Name: {torch.cuda.get_device_name(0)}")
    print(f"   - CUDA Version: {torch.version.cuda}")
    
    # Memory info
    if torch.cuda.device_count() > 0:
        total_memory = torch.cuda.get_device_properties(0).total_memory / (1024**3)
        print(f"   - Total Memory: {total_memory:.2f} GB")
        
        # Check if memory is allocated
        allocated = torch.cuda.memory_allocated(0) / (1024**3)
        cached = torch.cuda.memory_reserved(0) / (1024**3)
        print(f"   - Allocated Memory: {allocated:.2f} GB")
        print(f"   - Cached Memory: {cached:.2f} GB")
else:
    print(f"❌ NO GPU - Training & Prediction menggunakan CPU (LAMBAT!)")
    print(f"\n⚠️  Untuk mempercepat, install PyTorch dengan CUDA:")
    print(f"   pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118")

# Test tensor creation
print(f"\n🧪 Testing Tensor Creation:")
device = torch.device("cuda" if cuda_available else "cpu")
print(f"   - Device: {device}")

try:
    test_tensor = torch.randn(3, 3).to(device)
    print(f"   - Test Tensor Created: ✅")
    print(f"   - Tensor Device: {test_tensor.device}")
except Exception as e:
    print(f"   - Test Tensor Failed: ❌")
    print(f"   - Error: {e}")

# Check cuDNN
if cuda_available:
    print(f"\n🔧 cuDNN:")
    print(f"   - Enabled: {torch.backends.cudnn.enabled}")
    print(f"   - Version: {torch.backends.cudnn.version()}")

# Recommendations
print(f"\n💡 Recommendations:")
if cuda_available:
    print(f"   ✅ GPU sudah aktif! Prediksi akan cepat.")
    print(f"   ✅ Training akan menggunakan GPU secara otomatis.")
else:
    print(f"   ⚠️  Install CUDA-enabled PyTorch untuk mempercepat:")
    print(f"      1. Uninstall PyTorch saat ini:")
    print(f"         pip uninstall torch torchvision torchaudio")
    print(f"      2. Install PyTorch dengan CUDA 11.8:")
    print(f"         pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118")
    print(f"      3. Atau CUDA 12.1:")
    print(f"         pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121")
    print(f"   ⚠️  Pastikan NVIDIA GPU driver sudah terinstall")
    print(f"   ⚠️  Prediksi akan 10-100x lebih lambat tanpa GPU")

print(f"\n" + "=" * 60)
