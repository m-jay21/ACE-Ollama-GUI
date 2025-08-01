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
    
    def _prepare_model_for_training(self, model_name: str) -> Tuple[AutoModelForCausalLM, AutoTokenizer]:
        """Load and prepare model for LoRA fine-tuning"""
        try:
            # Get local Ollama model path
            model_path = self._get_ollama_model_path(model_name)
            
            # Load tokenizer and model from local path
            tokenizer = AutoTokenizer.from_pretrained(model_path)
            if tokenizer.pad_token is None:
                tokenizer.pad_token = tokenizer.eos_token
            
            # Load model with 4-bit quantization for memory efficiency
            model = AutoModelForCausalLM.from_pretrained(
                model_path,
                torch_dtype=torch.float16,
                device_map="auto",
                load_in_4bit=True,
                bnb_4bit_compute_dtype=torch.float16,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_use_double_quant=True,
            )
            
            # Prepare model for k-bit training
            model = prepare_model_for_kbit_training(model)
            
            return model, tokenizer
            
        except FileNotFoundError as e:
            self.logger.error(f"Model not found: {e}")
            raise Exception(f"Model '{model_name}' not found in your local Ollama installation. Please make sure the model is downloaded using 'ollama pull {model_name}'")
        except Exception as e:
            self.logger.error(f"Error preparing model: {e}")
            if "gated repo" in str(e).lower():
                raise Exception(f"Model '{model_name}' requires authentication. Please use a locally downloaded model instead.")
            elif "not found" in str(e).lower():
                raise Exception(f"Model '{model_name}' not found. Please make sure it's installed in Ollama.")
            else:
                raise Exception(f"Error loading model '{model_name}': {str(e)}")

    def _get_ollama_model_path(self, ollama_model: str) -> str:
        """Get the local path to an Ollama model"""
        try:
            # Check if the model exists in Ollama
            import subprocess
            result = subprocess.run(['ollama', 'list'], capture_output=True, text=True)
            if result.returncode != 0:
                raise Exception("Failed to list Ollama models")
            
            # Parse the output to check if model exists
            models = result.stdout.strip().split('\n')[1:]  # Skip header
            model_exists = any(ollama_model in line for line in models)
            
            if not model_exists:
                raise FileNotFoundError(f"Model {ollama_model} not found in Ollama. Use 'ollama pull {ollama_model}' to download it.")
            
            # For now, we need to use Hugging Face models because Ollama stores models in a proprietary format
            # that's not directly compatible with Hugging Face transformers
            # TODO: Implement proper Ollama model extraction and conversion
            
            # Use a fallback approach - try to find a publicly available equivalent
            if "phi3" in ollama_model:
                return "microsoft/Phi-3-mini-4k-instruct"  # Public model
            elif "mistral" in ollama_model:
                return "mistralai/Mistral-7B-Instruct-v0.2"  # Public model
            else:
                # For gated models like Llama, we need to inform the user
                raise Exception(
                    f"Model {ollama_model} requires Hugging Face authentication. "
                    f"Please either:\n"
                    f"1. Use a public model like 'phi3:mini' for testing\n"
                    f"2. Set up Hugging Face authentication for gated models\n"
                    f"3. Wait for local Ollama model extraction to be implemented"
                )
            
        except Exception as e:
            self.logger.error(f"Error finding model for {ollama_model}: {e}")
            raise
    
    def _create_training_dataset(self, training_data_path: str, tokenizer: AutoTokenizer) -> Dataset:
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
            
            # Create Ollama Modelfile
            modelfile_content = f"""FROM {fine_tuned_model_name}
TEMPLATE "{{{{ .System }}}}"

{{{{ .Prompt }}}}

PARAMETER stop "### Instruction:"
PARAMETER stop "### Response:"
PARAMETER temperature 0.7
PARAMETER top_p 0.9
PARAMETER top_k 40
PARAMETER num_ctx 4096
"""
            
            modelfile_path = model_path / "Modelfile"
            with open(modelfile_path, 'w') as f:
                f.write(modelfile_content)
            
            # Create Ollama model
            result = subprocess.run(
                ['ollama', 'create', fine_tuned_model_name, str(modelfile_path)],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                return {
                    "success": True,
                    "message": f"Fine-tuned model {fine_tuned_model_name} exported to Ollama successfully"
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to export to Ollama: {result.stderr}"
                }
                
        except Exception as e:
            self.logger.error(f"Error exporting model to Ollama: {e}")
            return {
                "success": False,
                "error": f"Export failed: {str(e)}"
            }

# Create global instance
fine_tuning_manager = FineTuningManager() 