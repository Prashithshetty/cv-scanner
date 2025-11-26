#!/usr/bin/env python3
"""
GGUF Model Runner with GPU Offloading Support
Customizable script for running AI models in GGUF format
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import Optional, Dict, Any
import logging

try:
    from llama_cpp import Llama
except ImportError:
    print("Error: llama-cpp-python not installed.")
    print("Install it with: pip install llama-cpp-python")
    print("For GPU support (CUDA): CMAKE_ARGS=\"-DLLAMA_CUBLAS=on\" pip install llama-cpp-python --force-reinstall --upgrade --no-cache-dir")
    print("For GPU support (Metal/Mac): CMAKE_ARGS=\"-DLLAMA_METAL=on\" pip install llama-cpp-python --force-reinstall --upgrade --no-cache-dir")
    sys.exit(1)

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class GGUFModelRunner:
    """Main class for running GGUF models with customizable parameters"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the model runner with configuration
        
        Args:
            config: Dictionary containing model and runtime configuration
        """
        self.config = config
        self.model = None
        self.model_path = None
        
    def load_model(self, model_name: Optional[str] = None) -> None:
        """
        Load a GGUF model from the models folder
        
        Args:
            model_name: Name of the model file (optional, uses config if not provided)
        """
        model_folder = Path(self.config['model_folder'])
        
        if not model_folder.exists():
            raise FileNotFoundError(f"Model folder '{model_folder}' not found")
        
        # Use provided model name or fall back to config
        if model_name:
            self.config['model_name'] = model_name
        
        model_file = model_folder / self.config['model_name']
        
        if not model_file.exists():
            # Try to find any GGUF file in the folder
            gguf_files = list(model_folder.glob("*.gguf"))
            if not gguf_files:
                raise FileNotFoundError(f"No GGUF models found in '{model_folder}'")
            
            print(f"Model '{model_file}' not found. Available models:")
            for i, f in enumerate(gguf_files):
                print(f"  {i+1}. {f.name}")
            
            choice = input("Enter model number to load (or 'q' to quit): ")
            if choice.lower() == 'q':
                sys.exit(0)
            
            try:
                model_file = gguf_files[int(choice) - 1]
            except (ValueError, IndexError):
                raise ValueError("Invalid selection")
        
        self.model_path = str(model_file)
        logger.info(f"Loading model: {model_file.name}")
        
        # Prepare model parameters
        model_params = {
            'model_path': self.model_path,
            'n_ctx': self.config['context_length'],
            'n_threads': self.config['cpu_threads'],
            'n_batch': self.config['batch_size'],
            'use_mmap': self.config['use_mmap'],
            'use_mlock': self.config['use_mlock'],
            'verbose': self.config['verbose']
        }
        
        # Add GPU offloading if configured
        if self.config['gpu_layers'] > 0:
            model_params['n_gpu_layers'] = self.config['gpu_layers']
            logger.info(f"GPU offloading enabled: {self.config['gpu_layers']} layers")
        else:
            model_params['n_gpu_layers'] = 0
            logger.info("Running on CPU only")
        
        # Initialize the model
        try:
            self.model = Llama(**model_params)
            logger.info("Model loaded successfully!")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise
    
    def generate(self, 
                 prompt: str,
                 max_tokens: Optional[int] = None,
                 temperature: Optional[float] = None,
                 top_p: Optional[float] = None,
                 top_k: Optional[int] = None,
                 repeat_penalty: Optional[float] = None,
                 stream: Optional[bool] = None) -> str:
        """
        Generate text from a prompt
        
        Args:
            prompt: Input text prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            top_p: Nucleus sampling parameter
            top_k: Top-k sampling parameter
            repeat_penalty: Repetition penalty
            stream: Whether to stream output
            
        Returns:
            Generated text
        """
        if not self.model:
            raise RuntimeError("Model not loaded. Call load_model() first.")
        
        # Use provided parameters or fall back to config
        generation_params = {
            'prompt': prompt,
            'max_tokens': max_tokens or self.config['max_tokens'],
            'temperature': temperature or self.config['temperature'],
            'top_p': top_p or self.config['top_p'],
            'top_k': top_k or self.config['top_k'],
            'repeat_penalty': repeat_penalty or self.config['repeat_penalty'],
            'echo': self.config['echo'],
            'stop': self.config['stop_sequences']
        }
        
        stream = stream if stream is not None else self.config['stream']
        
        if stream:
            # Stream the output
            response = self.model(**generation_params, stream=True)
            full_response = ""
            for chunk in response:
                text = chunk['choices'][0]['text']
                print(text, end='', flush=True)
                full_response += text
            print()  # New line at the end
            return full_response
        else:
            # Return complete response
            response = self.model(**generation_params)
            return response['choices'][0]['text']
    
    def chat(self, 
             messages: list,
             max_tokens: Optional[int] = None,
             temperature: Optional[float] = None,
             stream: Optional[bool] = None) -> str:
        """
        Chat completion with message history
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            stream: Whether to stream output
            
        Returns:
            Generated response
        """
        if not self.model:
            raise RuntimeError("Model not loaded. Call load_model() first.")
        
        generation_params = {
            'messages': messages,
            'max_tokens': max_tokens or self.config['max_tokens'],
            'temperature': temperature or self.config['temperature'],
            'top_p': self.config['top_p'],
            'top_k': self.config['top_k'],
            'repeat_penalty': self.config['repeat_penalty'],
            'stop': self.config['stop_sequences']
        }
        
        stream = stream if stream is not None else self.config['stream']
        
        if stream:
            response = self.model.create_chat_completion(**generation_params, stream=True)
            full_response = ""
            for chunk in response:
                if 'content' in chunk['choices'][0]['delta']:
                    text = chunk['choices'][0]['delta']['content']
                    print(text, end='', flush=True)
                    full_response += text
            print()
            return full_response
        else:
            response = self.model.create_chat_completion(**generation_params)
            return response['choices'][0]['message']['content']
    
    def interactive_mode(self):
        """Run an interactive chat session"""
        print("\n" + "="*50)
        print("Interactive Mode - Type 'quit' or 'exit' to stop")
        print("Type 'clear' to clear conversation history")
        print("Type 'save' to save conversation to file")
        print("="*50 + "\n")
        
        messages = []
        
        if self.config['use_chat_format']:
            print("Using chat format (with message history)")
        else:
            print("Using completion format (no message history)")
        
        while True:
            try:
                user_input = input("\nYou: ").strip()
                
                if user_input.lower() in ['quit', 'exit']:
                    print("Goodbye!")
                    break
                
                if user_input.lower() == 'clear':
                    messages = []
                    print("Conversation history cleared.")
                    continue
                
                if user_input.lower() == 'save':
                    filename = input("Enter filename to save (default: conversation.json): ").strip()
                    filename = filename or "conversation.json"
                    with open(filename, 'w') as f:
                        json.dump(messages, f, indent=2)
                    print(f"Conversation saved to {filename}")
                    continue
                
                if not user_input:
                    continue
                
                print("\nAssistant: ", end='')
                
                if self.config['use_chat_format']:
                    messages.append({"role": "user", "content": user_input})
                    response = self.chat(messages)
                    messages.append({"role": "assistant", "content": response})
                else:
                    response = self.generate(user_input)
                
            except KeyboardInterrupt:
                print("\n\nInterrupted by user. Goodbye!")
                break
            except Exception as e:
                logger.error(f"Error during generation: {e}")
                print(f"\nError: {e}")


def load_config(config_file: Optional[str] = None) -> Dict[str, Any]:
    """
    Load configuration from file or use defaults
    
    Args:
        config_file: Path to JSON configuration file
        
    Returns:
        Configuration dictionary
    """
    default_config = {
        'model_folder': 'model',
        'model_name': 'model.gguf',
        
        # Model loading parameters
        'context_length': 2048,
        'batch_size': 512,
        'cpu_threads': 4,
        'gpu_layers': -1,  # -1 for auto (all layers), 0 for CPU only, or specific number
        'use_mmap': True,
        'use_mlock': False,
        
        # Generation parameters
        'max_tokens': 512,
        'temperature': 0.7,
        'top_p': 0.9,
        'top_k': 40,
        'repeat_penalty': 1.1,
        'stop_sequences': [],
        
        # Interface options
        'stream': True,
        'echo': False,
        'verbose': False,
        'use_chat_format': True
    }
    
    if config_file and os.path.exists(config_file):
        logger.info(f"Loading configuration from {config_file}")
        with open(config_file, 'r') as f:
            user_config = json.load(f)
        default_config.update(user_config)
    
    return default_config


def save_config(config: Dict[str, Any], filename: str = "config.json"):
    """Save configuration to a JSON file"""
    with open(filename, 'w') as f:
        json.dump(config, f, indent=2)
    logger.info(f"Configuration saved to {filename}")


def main():
    parser = argparse.ArgumentParser(description='Run GGUF models with GPU offloading support')
    parser.add_argument('--model', '-m', type=str, help='Model filename in the model folder')
    parser.add_argument('--config', '-c', type=str, help='Configuration JSON file')
    parser.add_argument('--prompt', '-p', type=str, help='Direct prompt for single generation')
    parser.add_argument('--gpu-layers', '-g', type=int, help='Number of layers to offload to GPU')
    parser.add_argument('--ctx', type=int, help='Context length')
    parser.add_argument('--threads', '-t', type=int, help='Number of CPU threads')
    parser.add_argument('--max-tokens', type=int, help='Maximum tokens to generate')
    parser.add_argument('--temperature', type=float, help='Sampling temperature')
    parser.add_argument('--interactive', '-i', action='store_true', help='Interactive mode')
    parser.add_argument('--save-config', action='store_true', help='Save current config to file')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    # Load configuration
    config = load_config(args.config)
    
    # Override config with command-line arguments
    if args.gpu_layers is not None:
        config['gpu_layers'] = args.gpu_layers
    if args.ctx:
        config['context_length'] = args.ctx
    if args.threads:
        config['cpu_threads'] = args.threads
    if args.max_tokens:
        config['max_tokens'] = args.max_tokens
    if args.temperature:
        config['temperature'] = args.temperature
    if args.verbose:
        config['verbose'] = True
    
    # Save config if requested
    if args.save_config:
        save_config(config)
    
    # Initialize runner
    runner = GGUFModelRunner(config)
    
    try:
        # Load model
        runner.load_model(args.model)
        
        if args.prompt:
            # Single generation mode
            print("\nGenerating response...")
            response = runner.generate(args.prompt)
            if not config['stream']:
                print(f"\nResponse:\n{response}")
        else:
            # Interactive mode (default)
            runner.interactive_mode()
    
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()