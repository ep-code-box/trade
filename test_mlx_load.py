import mlx.core as mx
from mlx_lm import load
import sys

print(f"Python version: {sys.version}")
print(f"MLX version: {mx.__version__}")

model_path = "mlx-community/Qwen2-VL-2B-Instruct-4bit"
try:
    print(f"Attempting to load model: {model_path}")
    model, tokenizer = load(model_path)
    print("Model loaded successfully!")
except Exception as e:
    print(f"Error loading model: {e}")
