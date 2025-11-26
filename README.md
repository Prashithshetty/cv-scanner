# CV Scanner

A local LLM-based tool for analyzing and scoring Curriculum Vitae (CVs) against job descriptions. This application uses a local GGUF model to extract information and a deterministic Python engine to score candidates, ensuring privacy and consistency.

## 🚀 Features

*   **Local Processing:** Uses local LLMs (GGUF format) for privacy and offline capability.
*   **Dual Interface:** Run analysis via Command Line Interface (CLI) or a modern GUI.
*   **Deterministic Scoring:** Python-based scoring engine for accurate and reproducible results.
*   **PDF Parsing:** robust extraction from PDF documents.
*   **GPU Acceleration:** Optimized for GPU usage with `llama-cpp-python`.

## 📋 Prerequisites

*   Python 3.8+
*   A GGUF model file (placed in the `model/` directory)

## 🛠️ Installation

1.  **Clone the repository**
    ```bash
    git clone <repository-url>
    cd cv-scanner
    ```

2.  **Install dependencies**
    ```bash
    pip install -r requirements.txt
    ```

    > **Note for GPU Users:** To enable GPU acceleration with `llama-cpp-python`, you may need to install it with specific flags. For example, for NVIDIA GPUs:
    > ```bash
    > CMAKE_ARGS="-DLLAMA_CUBLAS=on" pip install llama-cpp-python --force-reinstall --no-cache-dir
    > ```

3.  **Setup Model**
    Place your GGUF model file in the `model/` directory. Update `config.json` if necessary to point to the specific model filename if the code doesn't auto-detect it (or ensure the code is configured to find it).

## 💻 Usage

### Command Line Interface (CLI)
Run the main script to process CVs:
```bash
python main.py
```

### Graphical User Interface (GUI)
Launch the user-friendly interface:
```bash
python gui.py
```

## ⚙️ Configuration

You can customize the application behavior in `config.json`:

*   `context_length`: 4096 (Increase for longer CVs)
*   `batch_size`: 1024 (Adjust based on VRAM)
*   `gpu_layers`: -1 (Offloads all layers to GPU)
*   `temperature`: 0.3 (Controls generation randomness)

## 📊 Scoring System

The system uses a deterministic scoring engine defined in `scorer.py`.

*   **Base Score:** 50 points
*   **Bonuses:**
    *   Required Skills: +15 points
    *   Relevant Projects: +10 points
    *   Deployment Proof: +5 points
*   **Deductions:**
    *   Missing Requirements: -20 points
    *   Contradictions: -10 points

You can modify `scorer.py` to adjust these rules.

## 📄 License

See the [LICENSE](LICENSE) file for details.
