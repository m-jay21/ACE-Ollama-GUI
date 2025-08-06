import os
import json
import platform
import subprocess
import shutil
import logging
import time
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import sys

# Fine-tuning imports
FINE_TUNING_AVAILABLE = False
try:
    import torch
    import transformers
    from transformers import (
        AutoTokenizer, 
        AutoModelForCausalLM, 
        TrainingArguments, 
        Trainer,
        DataCollatorForLanguageModeling,
        TrainerCallback
    )
    from peft import (
        LoraConfig, 
        get_peft_model, 
        TaskType,
        prepare_model_for_kbit_training
    )
    from datasets import Dataset
    from trl import SFTTrainer
    import accelerate
    import bitsandbytes as bnb
    FINE_TUNING_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Fine-tuning dependencies not available: {e}")
    FINE_TUNING_AVAILABLE = False

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FineTuningManager:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.fine_tuned_models_dir = Path("./fine_tuned_models")
        self.fine_tuned_models_dir.mkdir(exist_ok=True)
        
    def check_system_requirements(self) -> Dict:
        """Check if the system can handle fine-tuning using built-in modules only"""
        try:
            # Get RAM information (cross-platform)
            ram_gb = self._get_ram_gb()
            
            # Get storage information (built-in)
            storage_gb = shutil.disk_usage('/').free / (1024**3)
            
            # Check GPU availability (lightweight)
            gpu_available, gpu_memory_gb = self._check_gpu()
            
            # Determine if fine-tuning is possible
            can_fine_tune = (
                ram_gb >= 8 and  # Minimum 8GB RAM
                storage_gb >= 5 and  # Minimum 5GB free space
                (gpu_available or ram_gb >= 16)  # GPU or 16GB+ RAM
            )
            
            return {
                "ram_gb": ram_gb,
                "storage_gb": storage_gb,
                "gpu_available": gpu_available,
                "gpu_memory_gb": gpu_memory_gb,
                "can_fine_tune": can_fine_tune
            }
            
        except Exception as e:
            self.logger.error(f"Error checking system requirements: {e}")
            return {
                "ram_gb": 0,
                "storage_gb": 0,
                "gpu_available": False,
                "gpu_memory_gb": 0,
                "can_fine_tune": False,
                "error": str(e)
            }
    
    def _get_ram_gb(self) -> float:
        """Get RAM in GB using platform-specific methods"""
        try:
            if platform.system() == "Windows":
                # Windows: use wmic command
                result = subprocess.run(['wmic', 'computersystem', 'get', 'TotalPhysicalMemory'], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    lines = result.stdout.strip().split('\n')
                    if len(lines) >= 2:
                        memory_kb = int(lines[1].strip()) / 1024  # Convert to MB
                        return memory_kb / 1024  # Convert to GB
                        
            elif platform.system() == "Linux":
                # Linux: read from /proc/meminfo
                with open('/proc/meminfo', 'r') as f:
                    meminfo = f.read()
                    for line in meminfo.split('\n'):
                        if 'MemTotal' in line:
                            memory_kb = int(line.split()[1])
                            return memory_kb / 1024 / 1024  # Convert to GB
                            
            elif platform.system() == "Darwin":  # macOS
                # macOS: use sysctl command
                result = subprocess.run(['sysctl', '-n', 'hw.memsize'], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    memory_bytes = int(result.stdout.strip())
                    return memory_bytes / 1024 / 1024 / 1024  # Convert to GB
                    
        except Exception as e:
            self.logger.error(f"Error getting RAM info: {e}")
            
        # Fallback: return a conservative estimate
        return 8.0
    
    def _check_gpu(self) -> Tuple[bool, float]:
        """Check GPU availability using nvidia-smi"""
        try:
            # Try to run nvidia-smi to check for NVIDIA GPU
            result = subprocess.run(['nvidia-smi', '--query-gpu=memory.total', '--format=csv,noheader,nounits'], 
                                  capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                # Parse GPU memory
                gpu_memory_mb = float(result.stdout.strip())
                gpu_memory_gb = gpu_memory_mb / 1024
                return True, gpu_memory_gb
            else:
                return False, 0
                
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
            self.logger.debug(f"GPU check failed (this is normal if no GPU): {e}")
            return False, 0
    
    def _check_gpu_type(self) -> str:
        """Check what type of GPU is available"""
        try:
            # Check for NVIDIA GPU
            result = subprocess.run(['nvidia-smi'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                return "nvidia"
            
            # Check for Intel GPU
            result = subprocess.run(['lspci'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0 and 'Intel' in result.stdout and 'VGA' in result.stdout:
                return "intel"
            
            # Check for AMD GPU
            result = subprocess.run(['lspci'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0 and 'AMD' in result.stdout and 'VGA' in result.stdout:
                return "amd"
                
        except Exception as e:
            self.logger.debug(f"GPU type check failed: {e}")
        
        return "none"
    
    def validate_training_data(self, files: List[str]) -> Tuple[bool, str]:
        """Validate uploaded training data"""
        if not files:
            return False, "No training files provided"
        
        total_size = 0
        valid_extensions = {'.txt', '.md', '.json', '.csv', '.docx', '.pdf'}
        
        for file_path in files:
            if not os.path.exists(file_path):
                return False, f"File not found: {file_path}"
            
            file_ext = Path(file_path).suffix.lower()
            if file_ext not in valid_extensions:
                return False, f"Unsupported file type: {file_ext}"
            
            total_size += os.path.getsize(file_path)
        
        # Check if total size is reasonable (max 100MB)
        if total_size > 100 * 1024 * 1024:
            return False, "Total file size exceeds 100MB limit"
        
        return True, "Training data validation passed"
    
    def prepare_training_data(self, files: List[dict]) -> str:
        """Convert uploaded files into training dataset format"""
        training_texts = []
        
        for file_data in files:
            try:
                file_name = file_data.get('name', 'unknown')
                file_content = file_data.get('content', '')
                file_ext = Path(file_name).suffix.lower()
                
                if file_ext == '.txt' or file_ext == '.md':
                    # Split into chunks for better training
                    chunks = self._split_text_into_chunks(file_content, max_length=1000)
                    for chunk in chunks:
                        training_texts.append({
                            "text": f"### Instruction:\n{chunk}\n\n### Response:\nThe model will learn to respond appropriately to this type of content."
                        })
                
                elif file_ext == '.json':
                    try:
                        data = json.loads(file_content)
                        # Handle different JSON formats
                        if isinstance(data, list):
                            for item in data:
                                if isinstance(item, dict):
                                    # Extract text from various possible keys
                                    text = item.get('text', item.get('content', item.get('instruction', str(item))))
                                    training_texts.append({
                                        "text": f"### Instruction:\n{text}\n\n### Response:\nThe model will learn to respond appropriately."
                                    })
                        elif isinstance(data, dict):
                            text = str(data)
                            training_texts.append({
                                "text": f"### Instruction:\n{text}\n\n### Response:\nThe model will learn to respond appropriately."
                            })
                    except json.JSONDecodeError as e:
                        self.logger.error(f"Error parsing JSON file {file_name}: {e}")
                        continue
                
                elif file_ext == '.csv':
                    import csv
                    from io import StringIO
                    try:
                        csv_file = StringIO(file_content)
                        reader = csv.DictReader(csv_file)
                        for row in reader:
                            # Combine all columns into a single text
                            text = ' '.join([f"{k}: {v}" for k, v in row.items()])
                            training_texts.append({
                                "text": f"### Instruction:\n{text}\n\n### Response:\nThe model will learn to respond appropriately to this data."
                            })
                    except Exception as e:
                        self.logger.error(f"Error parsing CSV file {file_name}: {e}")
                        continue
                
                else:
                    # For other file types, use content as-is
                    training_texts.append({
                        "text": f"### Instruction:\n{file_content}\n\n### Response:\nThe model will learn to respond appropriately."
                    })
                        
            except Exception as e:
                self.logger.error(f"Error processing file {file_data.get('name', 'unknown')}: {e}")
                continue
        
        # Save training data to temporary file
        training_data_path = self.fine_tuned_models_dir / "training_data.json"
        with open(training_data_path, 'w', encoding='utf-8') as f:
            json.dump(training_texts, f, indent=2)
        
        self.logger.info(f"Prepared {len(training_texts)} training examples")
        return str(training_data_path)
    
    def _split_text_into_chunks(self, text: str, max_length: int = 1000) -> List[str]:
        """Split text into smaller chunks for training"""
        words = text.split()
        chunks = []
        current_chunk = []
        current_length = 0
        
        for word in words:
            if current_length + len(word) + 1 > max_length:
                if current_chunk:
                    chunks.append(' '.join(current_chunk))
                    current_chunk = [word]
                    current_length = len(word)
                else:
                    # Single word is too long, truncate it
                    chunks.append(word[:max_length])
            else:
                current_chunk.append(word)
                current_length += len(word) + 1
        
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        return chunks
    
    def setup_lora_config(self) -> Dict:
        """Configure LoRA parameters for efficient fine-tuning"""
        return {
            "task_type": TaskType.CAUSAL_LM,
            "inference_mode": False,
            "r": 8,  # Rank
            "lora_alpha": 32,
            "lora_dropout": 0.1,
            "target_modules": ["q_proj", "v_proj", "k_proj", "o_proj"],  # Which layers to adapt
            "bias": "none"
        }
    
    def _prepare_model_for_training(self, model_name: str) -> Tuple:
        """Load and prepare model for LoRA fine-tuning using Hugging Face models"""
        try:
            self.logger.info(f"Preparing model '{model_name}' for fine-tuning...")
            
            # Send progress update
            progress_data = {
                "stage": "Checking model availability",
                "percentage": 10,
                "message": f"Checking if model '{model_name}' is available in Ollama..."
            }
            print(f"PROGRESS_UPDATE: {json.dumps(progress_data)}")
            
            # Check if the model exists in Ollama first
            model_exists = self._check_ollama_model_exists(model_name)
            
            if not model_exists:
                raise Exception(
                    f"Model '{model_name}' not found in your Ollama installation.\n"
                    f"Please download it first using: ollama pull {model_name}"
                )
            

            
            # Send progress update
            progress_data = {
                "stage": "Detecting Hugging Face equivalent",
                "percentage": 20,
                "message": f"Finding Hugging Face equivalent for '{model_name}'..."
            }
            print(f"PROGRESS_UPDATE: {json.dumps(progress_data)}")
            
            # For the hybrid approach, we use Hugging Face models for fine-tuning
            # but check Ollama for availability first
            huggingface_model = self._get_huggingface_equivalent(model_name)
            
            self.logger.info(f"Using Hugging Face model: {huggingface_model}")
            
            # Send progress update
            progress_data = {
                "stage": "Loading tokenizer",
                "percentage": 30,
                "message": f"Loading tokenizer for {huggingface_model}..."
            }
            print(f"PROGRESS_UPDATE: {json.dumps(progress_data)}")
            
            # Load tokenizer and model from Hugging Face with retry mechanism
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    # Add progress callback for tokenizer download
                    progress_data = {
                        "stage": "Loading tokenizer",
                        "percentage": 30,
                        "message": f"Downloading tokenizer from Hugging Face... (attempt {attempt + 1}/{max_retries})"
                    }
                    print(f"PROGRESS_UPDATE: {json.dumps(progress_data)}")
                    
                    # Send initial progress update
                    progress_data = {
                        "stage": "Loading tokenizer",
                        "percentage": 30,
                        "message": f"Starting tokenizer download from Hugging Face... (attempt {attempt + 1}/{max_retries})"
                    }
                    print(f"PROGRESS_UPDATE: {json.dumps(progress_data)}")
                    
                    # Start background progress updates
                    import threading
                    import time
                    
                    progress_stopped = threading.Event()
                    
                    def progress_updater():
                        progress = 30
                        while not progress_stopped.is_set() and progress < 35:
                            progress_data = {
                                "stage": "Loading tokenizer",
                                "percentage": progress,
                                "message": f"Downloading tokenizer files... ({progress - 30}%)"
                            }
                            print(f"PROGRESS_UPDATE: {json.dumps(progress_data)}")
                            progress += 1
                            time.sleep(3)  # Update every 3 seconds
                    
                    progress_thread = threading.Thread(target=progress_updater, daemon=True)
                    progress_thread.start()
                    
                    # Add timeout for tokenizer download
                    import signal
                    
                    def timeout_handler(signum, frame):
                        progress_stopped.set()
                        raise TimeoutError("Tokenizer download timed out")
                    
                    # Set timeout to 5 minutes
                    signal.signal(signal.SIGALRM, timeout_handler)
                    signal.alarm(300)
                    
                    try:
                        print(f"DEBUG: Starting tokenizer download for {huggingface_model}")
                        tokenizer = AutoTokenizer.from_pretrained(
                            huggingface_model,
                            trust_remote_code=True,  # Allow custom tokenizer code
                            use_fast=True  # Use fast tokenizer when possible
                        )
                        print(f"DEBUG: Tokenizer download completed successfully")
                        signal.alarm(0)  # Cancel timeout
                        progress_stopped.set()  # Stop progress updates
                        
                        progress_data = {
                            "stage": "Loading tokenizer",
                            "percentage": 35,
                            "message": "Tokenizer download completed successfully!"
                        }
                        print(f"PROGRESS_UPDATE: {json.dumps(progress_data)}")
                        
                    except TimeoutError:
                        signal.alarm(0)  # Cancel timeout
                        progress_stopped.set()  # Stop progress updates
                        raise Exception("Tokenizer download timed out after 5 minutes. Please check your internet connection.")
                    except Exception as e:
                        signal.alarm(0)  # Cancel timeout
                        progress_stopped.set()  # Stop progress updates
                        print(f"DEBUG: Tokenizer download failed with error: {str(e)}")
                        raise e
                    if tokenizer.pad_token is None:
                        tokenizer.pad_token = tokenizer.eos_token
                    
                    progress_data = {
                        "stage": "Loading tokenizer",
                        "percentage": 35,
                        "message": "Tokenizer download completed successfully!"
                    }
                    print(f"PROGRESS_UPDATE: {json.dumps(progress_data)}")
                    break
                except Exception as e:
                    if attempt < max_retries - 1:
                        progress_data = {
                            "stage": "Loading tokenizer",
                            "percentage": 30,
                            "message": f"Download attempt {attempt + 1} failed, retrying in 5 seconds... ({str(e)[:100]})"
                        }
                        print(f"PROGRESS_UPDATE: {json.dumps(progress_data)}")
                        time.sleep(5)  # Wait before retry
                    else:
                        raise e
            
            # Send progress update
            progress_data = {
                "stage": "Loading model",
                "percentage": 40,
                "message": f"Loading model {huggingface_model}..."
            }
            print(f"PROGRESS_UPDATE: {json.dumps(progress_data)}")
            
            # Check GPU availability and type
            gpu_available, gpu_memory_gb = self._check_gpu()
            gpu_type = self._check_gpu_type()
            
            # Check if bitsandbytes has GPU support
            bnb_gpu_support = False
            try:
                import bitsandbytes as bnb
                # Try to create a small tensor on GPU to test if bnb has GPU support
                if gpu_available and torch.cuda.is_available():
                    test_tensor = torch.zeros(1, device='cuda')
                    bnb_gpu_support = True
            except Exception:
                bnb_gpu_support = False
            
            # For Intel/AMD GPUs or CPU-only, use CPU mode
            if gpu_type in ["intel", "amd"] or not gpu_available:
                progress_data = {
                    "stage": "Loading model",
                    "percentage": 45,
                    "message": f"Loading model with CPU (GPU type: {gpu_type.upper() if gpu_type != 'none' else 'CPU-only'})..."
                }
                print(f"PROGRESS_UPDATE: {json.dumps(progress_data)}")
                
                # CPU-only loading
                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        progress_data = {
                            "stage": "Loading model",
                            "percentage": 45,
                            "message": f"Downloading model... (attempt {attempt + 1}/{max_retries})"
                        }
                        print(f"PROGRESS_UPDATE: {json.dumps(progress_data)}")
                        
                        # Start background progress updates for model download
                        progress_stopped = threading.Event()
                        
                        def model_progress_updater():
                            progress = 45
                            while not progress_stopped.is_set() and progress < 48:
                                progress_data = {
                                    "stage": "Loading model",
                                    "percentage": progress,
                                    "message": f"Downloading model files... ({progress - 45}%)"
                                }
                                print(f"PROGRESS_UPDATE: {json.dumps(progress_data)}")
                                progress += 1
                                time.sleep(5)  # Update every 5 seconds for model download
                        
                        model_progress_thread = threading.Thread(target=model_progress_updater, daemon=True)
                        model_progress_thread.start()
                        
                        # Add timeout for model download
                        def timeout_handler(signum, frame):
                            progress_stopped.set()
                            raise TimeoutError("Model download timed out")
                        
                        # Set timeout to 10 minutes for model download
                        signal.signal(signal.SIGALRM, timeout_handler)
                        signal.alarm(600)
                        
                        try:
                            print(f"DEBUG: Starting model download for {huggingface_model}")
                            model = AutoModelForCausalLM.from_pretrained(
                                huggingface_model,
                                torch_dtype=torch.float32,
                                device_map="cpu",
                                trust_remote_code=True  # Allow custom model code
                            )
                            print(f"DEBUG: Model download completed successfully")
                            signal.alarm(0)  # Cancel timeout
                            progress_stopped.set()  # Stop progress updates
                            
                            progress_data = {
                                "stage": "Loading model",
                                "percentage": 48,
                                "message": "Model download completed successfully!"
                            }
                            print(f"PROGRESS_UPDATE: {json.dumps(progress_data)}")
                            break
                            
                        except TimeoutError:
                            signal.alarm(0)  # Cancel timeout
                            progress_stopped.set()  # Stop progress updates
                            raise Exception("Model download timed out after 10 minutes. Please check your internet connection.")
                        except Exception as e:
                            signal.alarm(0)  # Cancel timeout
                            progress_stopped.set()  # Stop progress updates
                            print(f"DEBUG: Model download failed with error: {str(e)}")
                            raise e
                    except Exception as e:
                        if attempt < max_retries - 1:
                            progress_data = {
                                "stage": "Loading model",
                                "percentage": 45,
                                "message": f"Model download attempt {attempt + 1} failed, retrying in 10 seconds... ({str(e)[:100]})"
                            }
                            print(f"PROGRESS_UPDATE: {json.dumps(progress_data)}")
                            time.sleep(10)  # Wait before retry
                        else:
                            raise e
            elif gpu_available and gpu_memory_gb >= 4 and bnb_gpu_support:
                # Use 4-bit quantization for GPU with proper bnb support
                progress_data = {
                    "stage": "Loading model",
                    "percentage": 45,
                    "message": f"Loading model with 4-bit quantization (GPU: {gpu_memory_gb:.1f}GB available)..."
                }
                print(f"PROGRESS_UPDATE: {json.dumps(progress_data)}")
                
                from transformers import BitsAndBytesConfig
                quantization_config = BitsAndBytesConfig(
                    load_in_4bit=True,
                    bnb_4bit_compute_dtype=torch.float16,
                    bnb_4bit_quant_type="nf4",
                    bnb_4bit_use_double_quant=True,
                )
                
                # Retry mechanism for model loading
                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        progress_data = {
                            "stage": "Loading model",
                            "percentage": 45,
                            "message": f"Downloading model with 4-bit quantization... (attempt {attempt + 1}/{max_retries})"
                        }
                        print(f"PROGRESS_UPDATE: {json.dumps(progress_data)}")
                        
                        # Start background progress updates for model download
                        progress_stopped = threading.Event()
                        
                        def model_progress_updater():
                            progress = 45
                            while not progress_stopped.is_set() and progress < 48:
                                progress_data = {
                                    "stage": "Loading model",
                                    "percentage": progress,
                                    "message": f"Downloading model files... ({progress - 45}%)"
                                }
                                print(f"PROGRESS_UPDATE: {json.dumps(progress_data)}")
                                progress += 1
                                time.sleep(5)  # Update every 5 seconds for model download
                        
                        model_progress_thread = threading.Thread(target=model_progress_updater, daemon=True)
                        model_progress_thread.start()
                        
                        # Add timeout for model download
                        def timeout_handler(signum, frame):
                            progress_stopped.set()
                            raise TimeoutError("Model download timed out")
                        
                        # Set timeout to 10 minutes for model download
                        signal.signal(signal.SIGALRM, timeout_handler)
                        signal.alarm(600)
                        
                        try:
                            print(f"DEBUG: Starting model download for {huggingface_model}")
                            model = AutoModelForCausalLM.from_pretrained(
                                huggingface_model,
                                torch_dtype=torch.float16,
                                device_map="auto",
                                quantization_config=quantization_config,
                                trust_remote_code=True  # Allow custom model code
                            )
                            print(f"DEBUG: Model download completed successfully")
                            signal.alarm(0)  # Cancel timeout
                            progress_stopped.set()  # Stop progress updates
                            
                            progress_data = {
                                "stage": "Loading model",
                                "percentage": 48,
                                "message": "Model download completed successfully!"
                            }
                            print(f"PROGRESS_UPDATE: {json.dumps(progress_data)}")
                            break
                            
                        except TimeoutError:
                            signal.alarm(0)  # Cancel timeout
                            progress_stopped.set()  # Stop progress updates
                            raise Exception("Model download timed out after 10 minutes. Please check your internet connection.")
                        except Exception as e:
                            signal.alarm(0)  # Cancel timeout
                            progress_stopped.set()  # Stop progress updates
                            print(f"DEBUG: Model download failed with error: {str(e)}")
                            raise e
                    except Exception as e:
                        if attempt < max_retries - 1:
                            progress_data = {
                                "stage": "Loading model",
                                "percentage": 45,
                                "message": f"Model download attempt {attempt + 1} failed, retrying in 10 seconds... ({str(e)[:100]})"
                            }
                            print(f"PROGRESS_UPDATE: {json.dumps(progress_data)}")
                            time.sleep(10)  # Wait before retry
                        else:
                            raise e
            else:
                # Fallback to CPU or lower precision for limited GPU/no bnb GPU support
                if gpu_available and not bnb_gpu_support:
                    progress_data = {
                        "stage": "Loading model",
                        "percentage": 45,
                        "message": f"Loading model with GPU but no 4-bit quantization (bitsandbytes GPU support not available)..."
                    }
                elif gpu_available:
                    progress_data = {
                        "stage": "Loading model",
                        "percentage": 45,
                        "message": f"Loading model with GPU fallback (GPU: {gpu_memory_gb:.1f}GB available)..."
                    }
                else:
                    progress_data = {
                        "stage": "Loading model",
                        "percentage": 45,
                        "message": "Loading model with CPU (GPU not available)..."
                    }
                print(f"PROGRESS_UPDATE: {json.dumps(progress_data)}")
                
                # Try to load with lower precision if GPU is available but limited
                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        progress_data = {
                            "stage": "Loading model",
                            "percentage": 45,
                            "message": f"Downloading model... (attempt {attempt + 1}/{max_retries})"
                        }
                        print(f"PROGRESS_UPDATE: {json.dumps(progress_data)}")
                        
                        # Start background progress updates for model download
                        progress_stopped = threading.Event()
                        
                        def model_progress_updater():
                            progress = 45
                            while not progress_stopped.is_set() and progress < 48:
                                progress_data = {
                                    "stage": "Loading model",
                                    "percentage": progress,
                                    "message": f"Downloading model files... ({progress - 45}%)"
                                }
                                print(f"PROGRESS_UPDATE: {json.dumps(progress_data)}")
                                progress += 1
                                time.sleep(5)  # Update every 5 seconds for model download
                        
                        model_progress_thread = threading.Thread(target=model_progress_updater, daemon=True)
                        model_progress_thread.start()
                        
                        # Add timeout for model download
                        def timeout_handler(signum, frame):
                            progress_stopped.set()
                            raise TimeoutError("Model download timed out")
                        
                        # Set timeout to 10 minutes for model download
                        signal.signal(signal.SIGALRM, timeout_handler)
                        signal.alarm(600)
                        
                        try:
                            print(f"DEBUG: Starting model download for {huggingface_model}")
                            if gpu_available:
                                model = AutoModelForCausalLM.from_pretrained(
                                    huggingface_model,
                                    torch_dtype=torch.float16,
                                    device_map="auto",
                                    trust_remote_code=True  # Allow custom model code
                                )
                            else:
                                # CPU-only loading
                                model = AutoModelForCausalLM.from_pretrained(
                                    huggingface_model,
                                    torch_dtype=torch.float32,
                                    device_map="cpu",
                                    trust_remote_code=True  # Allow custom model code
                                )
                            print(f"DEBUG: Model download completed successfully")
                            signal.alarm(0)  # Cancel timeout
                            progress_stopped.set()  # Stop progress updates
                            
                            progress_data = {
                                "stage": "Loading model",
                                "percentage": 48,
                                "message": "Model download completed successfully!"
                            }
                            print(f"PROGRESS_UPDATE: {json.dumps(progress_data)}")
                            break
                            
                        except TimeoutError:
                            signal.alarm(0)  # Cancel timeout
                            progress_stopped.set()  # Stop progress updates
                            raise Exception("Model download timed out after 10 minutes. Please check your internet connection.")
                        except Exception as e:
                            signal.alarm(0)  # Cancel timeout
                            progress_stopped.set()  # Stop progress updates
                            print(f"DEBUG: Model download failed with error: {str(e)}")
                            raise e
                    except Exception as e:
                        if attempt < max_retries - 1:
                            progress_data = {
                                "stage": "Loading model",
                                "percentage": 45,
                                "message": f"Model download attempt {attempt + 1} failed, retrying in 10 seconds... ({str(e)[:100]})"
                            }
                            print(f"PROGRESS_UPDATE: {json.dumps(progress_data)}")
                            time.sleep(10)  # Wait before retry
                        else:
                            raise e
            
            # Send progress update
            progress_data = {
                "stage": "Preparing model for training",
                "percentage": 50,
                "message": "Preparing model for k-bit training..."
            }
            print(f"PROGRESS_UPDATE: {json.dumps(progress_data)}")
            
            # Prepare model for k-bit training
            model = prepare_model_for_kbit_training(model)
            
            # Send final progress update
            progress_data = {
                "stage": "Model preparation complete",
                "percentage": 60,
                "message": "Model loaded and prepared successfully for fine-tuning!"
            }
            print(f"PROGRESS_UPDATE: {json.dumps(progress_data)}")
            
            return model, tokenizer
            
        except Exception as e:
            self.logger.error(f"Error preparing model: {e}")
            error_str = str(e).lower()
            
            if "gated repo" in error_str:
                raise Exception(
                    f"Model '{model_name}' requires Hugging Face authentication.\n"
                    f"For testing, try using a public model like 'phi3:mini'.\n"
                    f"Or set up Hugging Face authentication for gated models."
                )
            elif "not found" in error_str:
                raise Exception(
                    f"Model '{model_name}' not found.\n"
                    f"Please make sure it's installed in Ollama using: ollama pull {model_name}"
                )
            elif "timeout" in error_str or "connection" in error_str:
                raise Exception(
                    f"Network timeout while downloading model '{model_name}'.\n"
                    f"This might be due to:\n"
                    f"• Slow internet connection\n"
                    f"• Firewall blocking the connection\n"
                    f"• Hugging Face servers being temporarily unavailable\n\n"
                    f"Please try again in a few minutes."
                )
            elif "disk space" in error_str or "no space" in error_str:
                raise Exception(
                    f"Insufficient disk space to download model '{model_name}'.\n"
                    f"Please free up at least 5GB of disk space and try again."
                )
            elif "memory" in error_str or "ram" in error_str:
                raise Exception(
                    f"Insufficient memory to load model '{model_name}'.\n"
                    f"Please close other applications and try again, or use a smaller model."
                )
            elif "cuda" in error_str or "gpu" in error_str:
                gpu_type = self._check_gpu_type()
                if gpu_type == "intel":
                    raise Exception(
                        f"GPU acceleration not available for Intel graphics.\n"
                        f"Fine-tuning will continue with CPU, which may be slower.\n"
                        f"Error: {str(e)}"
                    )
                else:
                    raise Exception(
                        f"GPU acceleration error: {str(e)}\n"
                        f"Fine-tuning will continue with CPU."
                )
            else:
                raise Exception(f"Error loading model '{model_name}': {str(e)}")

    def _check_ollama_model_exists(self, model_name: str) -> bool:
        """Check if a model exists in Ollama"""
        try:
            result = subprocess.run(['ollama', 'list'], capture_output=True, text=True)
            if result.returncode != 0:
                return False
            
            # Parse the output to check if model exists
            models = result.stdout.strip().split('\n')[1:]  # Skip header
            return any(model_name in line for line in models)
        except Exception as e:
            self.logger.error(f"Error checking Ollama models: {e}")
            return False

    def _get_huggingface_equivalent(self, ollama_model: str) -> str:
        """Dynamically detect Hugging Face equivalent for an Ollama model"""
        
        # Normalize model name for pattern matching
        model_lower = ollama_model.lower().replace('-', '').replace('_', '')
        
        # Dynamic pattern matching for different model families
        hf_model = self._detect_model_family(model_lower, ollama_model)
        
        if hf_model:
            return hf_model
        
        # If dynamic detection fails, try to get model info from Ollama
        hf_model = self._get_model_from_ollama_info(ollama_model)
        
        if hf_model:
            return hf_model
        
        # Fallback: provide helpful error with detected patterns
        return self._generate_helpful_error(ollama_model)
    
    def _detect_model_family(self, model_lower: str, original_model: str) -> str:
        """Dynamically detect model family and return HF equivalent"""
        
        # Llama 3 family detection
        if 'llama3' in model_lower or 'llama3.2' in model_lower:
            return self._detect_llama3_variant(model_lower, original_model)
        
        # Llama 2 family detection
        elif 'llama2' in model_lower or 'llama2' in model_lower:
            return self._detect_llama2_variant(model_lower, original_model)
        
        # Phi family detection
        elif 'phi3' in model_lower or 'phi' in model_lower:
            return self._detect_phi_variant(model_lower, original_model)
        
        # Mistral family detection
        elif 'mistral' in model_lower:
            return self._detect_mistral_variant(model_lower, original_model)
        
        # CodeLlama family detection
        elif 'codellama' in model_lower or 'code' in model_lower:
            return self._detect_codellama_variant(model_lower, original_model)
        
        # Gemma family detection
        elif 'gemma' in model_lower:
            return self._detect_gemma_variant(model_lower, original_model)
        
        # Qwen family detection
        elif 'qwen' in model_lower:
            return self._detect_qwen_variant(model_lower, original_model)
        
        return None
    
    def _detect_llama3_variant(self, model_lower: str, original_model: str) -> str:
        """Detect Llama 3 variant and return appropriate HF model"""
        
        # Extract size information
        if '3b' in model_lower or '3b' in original_model:
            return "meta-llama/Llama-3.2-3B-Instruct"
        elif '8b' in model_lower or '8b' in original_model:
            return "meta-llama/Llama-3.2-8B-Instruct"
        elif '70b' in model_lower or '70b' in original_model:
            return "meta-llama/Llama-3.2-70B-Instruct"
        else:
            # Default to 3B for Llama 3
            return "meta-llama/Llama-3.2-3B-Instruct"
    
    def _detect_llama2_variant(self, model_lower: str, original_model: str) -> str:
        """Detect Llama 2 variant and return appropriate HF model"""
        
        # Extract size information
        if '7b' in model_lower or '7b' in original_model:
            return "meta-llama/Llama-2-7b-chat-hf"
        elif '13b' in model_lower or '13b' in original_model:
            return "meta-llama/Llama-2-13b-chat-hf"
        elif '70b' in model_lower or '70b' in original_model:
            return "meta-llama/Llama-2-70b-chat-hf"
        else:
            # Default to 7B for Llama 2
            return "meta-llama/Llama-2-7b-chat-hf"
    
    def _detect_phi_variant(self, model_lower: str, original_model: str) -> str:
        """Detect Phi variant and return appropriate HF model"""
        
        if 'mini' in model_lower:
            return "microsoft/Phi-3-mini-4k-instruct"
        elif 'small' in model_lower:
            return "microsoft/Phi-3-small-8k-instruct"
        elif 'medium' in model_lower:
            return "microsoft/Phi-3-medium-4k-instruct"
        else:
            # Default to mini for Phi
            return "microsoft/Phi-3-mini-4k-instruct"
    
    def _detect_mistral_variant(self, model_lower: str, original_model: str) -> str:
        """Detect Mistral variant and return appropriate HF model"""
        
        if '7b' in model_lower or '7b' in original_model:
            return "mistralai/Mistral-7B-Instruct-v0.2"
        else:
            # Default to 7B for Mistral
            return "mistralai/Mistral-7B-Instruct-v0.2"
    
    def _detect_codellama_variant(self, model_lower: str, original_model: str) -> str:
        """Detect CodeLlama variant and return appropriate HF model"""
        
        if '7b' in model_lower or '7b' in original_model:
            return "codellama/CodeLlama-7b-Instruct-hf"
        elif '13b' in model_lower or '13b' in original_model:
            return "codellama/CodeLlama-13b-Instruct-hf"
        elif '34b' in model_lower or '34b' in original_model:
            return "codellama/CodeLlama-34b-Instruct-hf"
        else:
            # Default to 7B for CodeLlama
            return "codellama/CodeLlama-7b-Instruct-hf"
    
    def _detect_gemma_variant(self, model_lower: str, original_model: str) -> str:
        """Detect Gemma variant and return appropriate HF model"""
        
        if '2b' in model_lower or '2b' in original_model:
            return "google/gemma-2b-it"
        elif '7b' in model_lower or '7b' in original_model:
            return "google/gemma-7b-it"
        else:
            # Default to 2B for Gemma
            return "google/gemma-2b-it"
    
    def _detect_qwen_variant(self, model_lower: str, original_model: str) -> str:
        """Detect Qwen variant and return appropriate HF model"""
        
        if '7b' in model_lower or '7b' in original_model:
            return "Qwen/Qwen2-7B-Instruct"
        elif '14b' in model_lower or '14b' in original_model:
            return "Qwen/Qwen2-14B-Instruct"
        elif '72b' in model_lower or '72b' in original_model:
            return "Qwen/Qwen2-72B-Instruct"
        else:
            # Default to 7B for Qwen
            return "Qwen/Qwen2-7B-Instruct"
    
    def _get_model_from_ollama_info(self, ollama_model: str) -> str:
        """Try to get model information from Ollama API to find HF equivalent"""
        try:
            # This would require implementing Ollama API calls
            # For now, return None to use fallback
            return None
        except Exception as e:
            self.logger.warning(f"Could not get model info from Ollama: {e}")
            return None
    
    def _generate_helpful_error(self, ollama_model: str) -> str:
        """Generate helpful error message with detected patterns"""
        
        # Analyze the model name for patterns
        model_lower = ollama_model.lower()
        detected_family = "Unknown"
        
        if 'llama' in model_lower:
            detected_family = "Llama"
        elif 'phi' in model_lower:
            detected_family = "Phi"
        elif 'mistral' in model_lower:
            detected_family = "Mistral"
        elif 'code' in model_lower:
            detected_family = "CodeLlama"
        elif 'gemma' in model_lower:
            detected_family = "Gemma"
        elif 'qwen' in model_lower:
            detected_family = "Qwen"
        
        # Extract size information
        size_info = ""
        if '3b' in model_lower:
            size_info = "3B"
        elif '7b' in model_lower:
            size_info = "7B"
        elif '13b' in model_lower:
            size_info = "13B"
        elif '70b' in model_lower:
            size_info = "70B"
        
        error_msg = f"Model '{ollama_model}' doesn't have a known Hugging Face equivalent.\n"
        error_msg += f"Detected family: {detected_family}"
        if size_info:
            error_msg += f", Size: {size_info}"
        error_msg += "\n\n"
        error_msg += "Please use one of these supported models:\n"
        error_msg += "• phi3:mini (recommended for testing)\n"
        error_msg += "• llama3.2:3b (you have this installed)\n"
        error_msg += "• llama3.2:8b\n"
        error_msg += "• mistral:7b\n"
        error_msg += "• llama2:7b (requires Hugging Face authentication)\n"
        error_msg += "• codellama:7b\n"
        error_msg += "• gemma:2b\n"
        error_msg += "• qwen2:7b"
        
        raise Exception(error_msg)
    
    def _create_training_dataset(self, training_data_path: str, tokenizer) -> object:
        """Create training dataset from prepared data"""
        try:
            with open(training_data_path, 'r', encoding='utf-8') as f:
                training_data = json.load(f)
            
            # Format data for instruction-following training
            formatted_data = []
            for item in training_data:
                text = item.get("text", "")
                if text:
                    formatted_data.append({"text": text})
            
            # Create dataset
            dataset = Dataset.from_list(formatted_data)
            
            # Tokenize dataset
            def tokenize_function(examples):
                return tokenizer(
                    examples["text"],
                    truncation=True,
                    padding=True,
                    max_length=512,
                    return_tensors="pt"
                )
            
            tokenized_dataset = dataset.map(
                tokenize_function,
                batched=True,
                remove_columns=dataset.column_names
            )
            
            return tokenized_dataset
            
        except Exception as e:
            self.logger.error(f"Error creating training dataset: {e}")
            raise
    
    def start_fine_tuning(self, base_model: str, model_name: str, 
                         learning_rate: float = 0.0003, epochs: int = 3, 
                         batch_size: int = 2, files: List[dict] = None) -> Dict:
        """Start the fine-tuning process with LoRA"""
        
        if not FINE_TUNING_AVAILABLE:
            return {
                "success": False,
                "error": "Fine-tuning dependencies not available. Please install: torch, transformers, peft, accelerate, datasets, trl, bitsandbytes"
            }
        
        try:
            self.logger.info(f"Starting fine-tuning for {base_model} -> {model_name}")
            
            # Check system requirements
            requirements = self.check_system_requirements()
            if not requirements.get("can_fine_tune", False):
                return {
                    "success": False,
                    "error": f"System requirements not met. RAM: {requirements.get('ram_gb', 0):.1f}GB, Storage: {requirements.get('storage_gb', 0):.1f}GB"
                }
            
            # Pre-flight check: Verify model availability
            progress_data = {
                "stage": "Pre-flight check",
                "percentage": 5,
                "message": f"Verifying model '{base_model}' availability..."
            }
            print(f"PROGRESS_UPDATE: {json.dumps(progress_data)}")
            
            # Check if base model exists in Ollama
            if not self._check_ollama_model_exists(base_model):
                return {
                    "success": False,
                    "error": f"Base model '{base_model}' not found in Ollama. Please install it first using: ollama pull {base_model}"
                }
            
            # Check if Hugging Face equivalent is available
            try:
                huggingface_model = self._get_huggingface_equivalent(base_model)
                progress_data = {
                    "stage": "Pre-flight check",
                    "percentage": 8,
                    "message": f"Found Hugging Face equivalent: {huggingface_model}"
                }
                print(f"PROGRESS_UPDATE: {json.dumps(progress_data)}")
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Model '{base_model}' is not supported for fine-tuning: {str(e)}"
                }
            
            # Prepare model and tokenizer
            model, tokenizer = self._prepare_model_for_training(base_model)
            
            # Prepare training data from uploaded files
            training_data_path = self.prepare_training_data(files)
            
            # Create training dataset
            dataset = self._create_training_dataset(training_data_path, tokenizer)
            
            # Setup LoRA configuration
            lora_config = LoraConfig(**self.setup_lora_config())
            
            # Apply LoRA to model
            model = get_peft_model(model, lora_config)
            
            # Setup training arguments with progress tracking
            training_args = TrainingArguments(
                output_dir=f"./fine_tuned_models/{model_name}",
                num_train_epochs=epochs,
                per_device_train_batch_size=batch_size,
                gradient_accumulation_steps=4,
                learning_rate=learning_rate,
                fp16=True,
                logging_steps=1,  # Log every step for real-time updates
                save_steps=100,
                eval_steps=100,
                evaluation_strategy="steps",
                save_strategy="steps",
                load_best_model_at_end=True,
                report_to=None,  # Disable wandb
                remove_unused_columns=False,
                push_to_hub=False,
            )
            
            # Custom progress callback for real-time updates
            class ProgressCallback(TrainerCallback):
                def __init__(self, start_time, total_steps):
                    self.start_time = start_time
                    self.step_count = 0
                    self.total_steps = total_steps
                
                def on_step_end(self, args, state, control, **kwargs):
                    self.step_count += 1
                    elapsed = time.time() - self.start_time
                    elapsed_str = f"{int(elapsed//60)}:{int(elapsed%60):02d}"
                    
                    # Calculate progress
                    progress = min(100, (self.step_count / self.total_steps) * 100)
                    
                    # Estimate ETA
                    if self.step_count > 0:
                        avg_time_per_step = elapsed / self.step_count
                        remaining_steps = self.total_steps - self.step_count
                        eta_seconds = remaining_steps * avg_time_per_step
                        eta_str = f"{int(eta_seconds//60)}:{int(eta_seconds%60):02d}"
                    else:
                        eta_str = "Calculating..."
                    
                    # Get current loss
                    current_loss = state.log_history[-1].get('loss', 0) if state.log_history else 0
                    
                    # Send progress update
                    progress_data = {
                        "percentage": round(progress, 1),
                        "currentEpoch": f"Epoch {state.epoch:.1f}",
                        "timeElapsed": elapsed_str,
                        "currentLoss": f"{current_loss:.4f}",
                        "eta": eta_str,
                        "log": f"Step {self.step_count}/{self.total_steps} - Loss: {current_loss:.4f}"
                    }
                    
                    # Print progress (will be captured by main.js)
                    print(f"PROGRESS_UPDATE: {json.dumps(progress_data)}")
            
            # Calculate total steps
            total_steps = len(dataset) // batch_size * epochs
            
            # Setup trainer with progress callback
            trainer = SFTTrainer(
                model=model,
                train_dataset=dataset,
                tokenizer=tokenizer,
                args=training_args,
                max_seq_length=512,
                dataset_text_field="text",
            )
            
            # Add progress callback
            start_time = time.time()
            trainer.add_callback(ProgressCallback(start_time, total_steps))
            
            # Start training
            self.logger.info("Starting training...")
            trainer.train()
            
            # Save the fine-tuned model
            model_save_path = f"./fine_tuned_models/{model_name}"
            trainer.save_model(model_save_path)
            tokenizer.save_pretrained(model_save_path)
            
            # Save model info
            model_info = {
                "base_model": base_model,
                "fine_tuned_name": model_name,
                "created_at": datetime.now().isoformat(),
                "training_params": {
                    "learning_rate": learning_rate,
                    "epochs": epochs,
                    "batch_size": batch_size
                }
            }
            
            with open(f"{model_save_path}/model_info.json", 'w') as f:
                json.dump(model_info, f, indent=2)
            
            self.logger.info(f"Fine-tuning completed successfully. Model saved to {model_save_path}")
            
            return {
                "success": True,
                "message": f"Fine-tuning completed successfully. Model saved as {model_name}",
                "model_path": model_save_path
            }
            
        except Exception as e:
            self.logger.error(f"Error during fine-tuning: {e}")
            return {
                "success": False,
                "error": f"Fine-tuning failed: {str(e)}"
            }
    
    def get_fine_tuned_models(self) -> List[str]:
        """Get list of available fine-tuned models"""
        models = []
        if self.fine_tuned_models_dir.exists():
            for model_dir in self.fine_tuned_models_dir.iterdir():
                if model_dir.is_dir() and (model_dir / "adapter_config.json").exists():
                    models.append(model_dir.name)
        return models
    
    def export_to_ollama(self, fine_tuned_model_name: str) -> Dict:
        """Export fine-tuned model to Ollama format"""
        try:
            model_path = self.fine_tuned_models_dir / fine_tuned_model_name
            
            if not model_path.exists():
                return {
                    "success": False,
                    "error": f"Fine-tuned model {fine_tuned_model_name} not found"
                }
            
            # Check if the model has the required files
            required_files = ["adapter_config.json", "adapter_model.bin"]
            missing_files = [f for f in required_files if not (model_path / f).exists()]
            
            if missing_files:
                return {
                    "success": False,
                    "error": f"Fine-tuned model is incomplete. Missing files: {', '.join(missing_files)}"
                }
            
            # Load model info to get base model
            model_info_path = model_path / "model_info.json"
            base_model = "unknown"
            if model_info_path.exists():
                try:
                    with open(model_info_path, 'r') as f:
                        model_info = json.load(f)
                        base_model = model_info.get("base_model", "unknown")
                except Exception as e:
                    self.logger.warning(f"Could not load model info: {e}")
            
            # Create Ollama Modelfile with proper configuration
            template_part = """{{{{ if .System }}}}{{{{ .System }}}}{{{{ end }}}

{{{{ .Prompt }}}}"""
            
            modelfile_content = f"""# Fine-tuned model: {fine_tuned_model_name}
# Base model: {base_model}
# Created with ACE UI for Ollama

FROM {base_model}

# Load the fine-tuned adapter
ADAPTER {fine_tuned_model_name}

# System prompt template
SYSTEM "You are a helpful AI assistant that has been fine-tuned for specific tasks."

# Chat template
TEMPLATE "{template_part}"

# Parameters for better performance
PARAMETER temperature 0.7
PARAMETER top_p 0.9
PARAMETER top_k 40
PARAMETER num_ctx 4096
PARAMETER repeat_penalty 1.1
PARAMETER stop "### Instruction:"
PARAMETER stop "### Response:"
"""
            
            modelfile_path = model_path / "Modelfile"
            with open(modelfile_path, 'w') as f:
                f.write(modelfile_content)
            
            self.logger.info(f"Created Modelfile for {fine_tuned_model_name}")
            
            # Create Ollama model
            self.logger.info(f"Creating Ollama model: {fine_tuned_model_name}")
            result = subprocess.run(
                ['ollama', 'create', fine_tuned_model_name, str(modelfile_path)],
                capture_output=True,
                text=True,
                timeout=120  # Increased timeout for model creation
            )
            
            if result.returncode == 0:
                self.logger.info(f"Successfully exported {fine_tuned_model_name} to Ollama")
                return {
                    "success": True,
                    "message": f"Fine-tuned model '{fine_tuned_model_name}' exported to Ollama successfully!\n\nYou can now use it in the chat by selecting it from the model dropdown."
                }
            else:
                error_msg = result.stderr.strip() if result.stderr else "Unknown error"
                self.logger.error(f"Failed to export to Ollama: {error_msg}")
                return {
                    "success": False,
                    "error": f"Failed to export to Ollama:\n{error_msg}\n\nThis might be because:\n• The base model isn't available in Ollama\n• There's insufficient disk space\n• Ollama service is not running"
                }
                
        except Exception as e:
            self.logger.error(f"Error exporting model to Ollama: {e}")
            return {
                "success": False,
                "error": f"Export failed: {str(e)}\n\nPlease ensure:\n• Ollama is running\n• You have sufficient disk space\n• The base model is available in Ollama"
            }

# Create global instance
fine_tuning_manager = FineTuningManager()