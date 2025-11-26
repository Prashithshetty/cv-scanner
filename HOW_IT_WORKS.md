# CV Scanner - How It Works

## Table of Contents
1. [Overview](#overview)
2. [System Architecture](#system-architecture)
3. [Core Components](#core-components)
4. [Workflow & Data Flow](#workflow--data-flow)
5. [Technical Implementation](#technical-implementation)
6. [Performance Optimizations](#performance-optimizations)
7. [User Interfaces](#user-interfaces)

---

## Overview

The CV Scanner is a sophisticated AI-powered application designed to analyze curriculum vitae (CVs) against job descriptions. It combines **local Large Language Model (LLM) inference** with **deterministic Python-based scoring** to rank candidates efficiently and accurately.

### Key Characteristics
- **Privacy-First**: Uses local GGUF models (no cloud APIs)
- **Hybrid Approach**: AI for data extraction + Python for scoring
- **High Performance**: Parallel processing with GPU acceleration
- **Dual Interface**: CLI and modern GUI options
- **Deterministic Results**: Reproducible scoring using Python rules

---

## System Architecture

The application follows a modular, layered architecture:

```
┌─────────────────────────────────────────────────┐
│          User Interface Layer                   │
│  ┌──────────────┐      ┌──────────────┐         │
│  │   CLI Mode   │      │   GUI Mode   │         │
│  │  (main.py)   │      │   (gui.py)   │         │
│  └──────────────┘      └──────────────┘         │
└────────────┬─────────────────┬──────────────────┘
             │                 │
┌────────────▼─────────────────▼──────────────────┐
│        Core Analysis Engine (CVAnalyzer)        │
│                                                 │
│  • Orchestrates entire analysis workflow        │
│  • Manages parallel processing                  │
│  • Coordinates all sub-components               │
└────────────┬──────────────────────────────┬─────┘
             │                              │
      ┌──────▼───────┐           ┌─────────▼──────┐
      │              │           │                │
┌─────▼─────┐  ┌────▼────┐  ┌───▼────┐  ┌────────▼──────┐
│  PDF      │  │   AI    │  │ Scorer │  │ Config Manager│
│ Extractor │  │  Model  │  │ Engine │  │               │
└───────────┘  └─────────┘  └────────┘  └───────────────┘
```

### Component Responsibilities

1. **Interface Layer**: Handles user input and displays results
2. **Analysis Engine**: Orchestrates the complete CV analysis workflow
3. **Support Modules**: 
   - PDF extraction
   - AI model inference
   - Deterministic scoring
   - Configuration management

---

## Core Components

### 1. Main Analysis Engine (`main.py`)

**Class**: `CVAnalyzer`

The heart of the system that orchestrates the entire CV analysis workflow.

#### Key Responsibilities:
- Initialize AI model and scoring engine
- Manage parallel processing workers
- Extract text from CVs (parallel)
- Extract structured data using AI
- Calculate scores using Python
- Generate summaries (optional)
- Rank and display results

#### Critical Methods:

**`__init__(config_path)`**
```python
# Initialization flow:
1. Load configuration from config.json
2. Initialize GGUF model runner
3. Load AI model into memory (GPU)
4. Initialize deterministic scorer
5. Set up thread safety (model_lock)
```

**`process_all_cvs(cv_directory, job_description)`**
```python
# Main workflow:
1. Get all PDF files from directory
2. Extract text in parallel (ThreadPoolExecutor)
3. For each CV:
   a. Extract data with AI (JSON format)
   b. Calculate score with Python
   c. Generate summary (optional)
4. Return ranked results
```

**`extract_cv_data(cv_text, job_description, cv_name)`**
```python
# AI extraction:
1. Build structured JSON extraction prompt
2. Send to LLM via chat interface
3. Parse JSON response
4. Return structured data:
   - required_skills: [{skill, found, evidence}]
   - preferred_skills: [{skill, found, evidence}]
   - projects: [{title, technologies, relevance}]
   - transferable_skills: [{skill, evidence}]
   - issues: [{type, description}]
```

**`_process_single_cv(cv_name, cv_text, job_description)`**
```python
# Thread-safe single CV processing:
1. Extract structured data (AI)
2. Calculate score (Python)
3. Generate summary (optional AI)
4. Compile result dictionary
```

---

### 2. AI Model Runner (`ai_gguf.py`)

**Class**: `GGUFModelRunner`

Manages the local Large Language Model (LLM) using the GGUF format.

#### Purpose:
- Load and manage GGUF models via `llama-cpp-python`
- Handle GPU offloading for acceleration
- Provide text generation and chat interfaces
- Support both streaming and non-streaming outputs

#### Key Methods:

**`load_model(model_name)`**
```python
# Model loading:
1. Locate GGUF file in model/ directory
2. Configure model parameters:
   - Context length (4096 tokens)
   - GPU layers (-1 = all layers on GPU)
   - Thread count, batch size, mmap settings
3. Initialize Llama model
4. Model stays loaded for entire session
```

**`chat(messages, max_tokens, temperature)`**
```python
# Chat completion:
1. Accept message history format
2. Generate response using model
3. Return assistant's reply
4. Used for structured data extraction
```

**`generate(prompt, max_tokens, temperature)`**
```python
# Direct text generation:
1. Accept raw text prompt
2. Generate continuation
3. Return generated text
4. Used for summaries
```

#### Configuration Parameters:
- `gpu_layers`: Number of layers on GPU (-1 = all)
- `context_length`: Maximum token context (4096)
- `temperature`: Randomness control (0.3 = deterministic)
- `batch_size`: GPU batch processing (1024)
- `max_tokens`: Maximum output length (1024)

---

### 3. PDF Text Extractor (`pdf_extractor.py`)

**Class**: `PDFTextExtractor`
2. Iterate through all pages
3. Extract text per page
4. Concatenate with page markers
5. Return full text content
```

#### Features:
- Page-by-page extraction
- Auto-detection of best method
- Error handling and logging
- Text quality validation

---

### 4. Scoring Engine (`scorer.py`)

**Class**: `CVScorer`

Calculates deterministic, reproducible scores based on AI-extracted data.

#### Why Deterministic Scoring?
- **Accuracy**: No AI mathematical errors
- **Reproducibility**: Same data = same score always
- **Transparency**: Clear breakdown of score calculation
- **Customizable**: Easy to modify rules in Python
- **Fast**: No AI inference needed for scoring

#### Scoring Algorithm:

**Base Score**: 50 points

**Additions**:
```python
required_skills:     +15 points each (max +45 for 3 skills)
relevant_projects:   +10 points each (max +20 for 2 projects)
deployment_proof:    +5 points each  (max +10 for 2 proofs)
preferred_skills:    +5 points each  (max +10 for 2 skills)
transferable_skills: +5 points each  (max +10 for 2 skills)
```

**Deductions**:
```python
missing_required:    -20 points per skill
contradiction:       -10 points
ambiguous:          -5 points
weak_evidence:      -3 points
```

**Recommendations**:
```python
SHORTLIST: score >= 75
REVIEW:    score >= 60 and < 75
REJECT:    score < 60
```

#### Process:
```python
def calculate_score(extracted_data):
    1. Start with base_score (50)
    2. Add points for required_skills found
    3. Add points for preferred_skills
    4. Add points for relevant projects
    5. Add points for deployment proofs
    6. Add points for transferable_skills
    7. Deduct points for missing required skills
    8. Deduct points for issues/contradictions
    9. Clamp final score to 0-100
    10. Determine recommendation
    11. Return {score, breakdown, recommendation, details}
```

---

### 5. GUI Components (`gui.py` + `components/`)

The application features a modular, component-based GUI built with `customtkinter`.

#### Architecture:

**Main Application**: `CVScannerModular` (gui.py)
- Coordinates all components
- Handles events and state
- Manages analysis workflow

**Component Modules**:

1. **`ThemeManager`** (`components/theme_manager.py`)
   - Centralized color schemes
   - Font definitions
   - Button styles
   - Light/dark mode support

2. **`Sidebar`** (`components/sidebar.py`)
   - Directory selection
   - Run analysis button
   - Progress tracking
   - Performance settings (workers, summaries)
   - Theme switcher
   - Statistics display

3. **`MainPanel`** (`components/main_panel.py`)
   - Job description input
   - Character counter
   - Results header with controls
   - Search, sort, filter options
   - Export button
   - Scrollable results display

4. **`CandidateCard`** (`components/candidate_card.py`)
   - Individual candidate display
   - Score visualization
   - Key skills summary
   - View details button
   - Color-coded by recommendation

5. **`DetailsModal`** (`components/details_modal.py`)
   - Full candidate information
   - Score breakdown
   - All extracted data
   - CV text preview

6. **`ExportDialog`** (`components/export_dialog.py`)
   - Export format selection (JSON, CSV, Excel, TXT)
   - File name input
   - Export confirmation

---

## Workflow & Data Flow

### Complete Analysis Workflow

```
1. USER INPUT
   └─> CV Directory Path
   └─> Job Description Text

2. INITIALIZATION
   └─> Load AI Model (one-time, cached)
   └─> Initialize Scorer

3. PDF EXTRACTION (Parallel)
   └─> Find all PDF files
   └─> Extract text from each PDF
       └─> Worker Pool (4 workers)
       └─> Use pdfplumber/PyPDF2
   └─> Output: {cv_name: text_content}

4. AI DATA EXTRACTION (Parallel)
   └─> For each CV (3 workers):
       a. Build JSON extraction prompt
       b. Include job description + CV text
       c. Send to AI model (thread-safe)
       d. Parse JSON response
       e. Validate structure
   └─> Output: {required_skills, preferred_skills, projects, ...}

5. PYTHON SCORING (Fast)
   └─> For each extracted data:
       a. Apply scoring rules
       b. Calculate points
       c. Generate breakdown
       d. Determine recommendation
   └─> Output: {final_score, breakdown, recommendation}

6. SUMMARY GENERATION (Optional)
   └─> If enabled:
       a. Create summary prompt
       b. Send to AI model
       c. Get human-readable summary
   └─> Otherwise: Generate quick summary from data

7. RESULT COMPILATION
   └─> Combine all results
   └─> Sort by score (descending)
   └─> Return top candidates

8. DISPLAY
   └─> CLI: Print formatted results
   └─> GUI: Show candidate cards
```

### Data Structures

**Input**:
```python
cv_directory: str         # Path to folder with PDFs
job_description: str      # Job requirements text
```

**Extracted Data** (from AI):
```python
{
  "required_skills": [
    {
      "skill": "Python",
      "found": True,
      "evidence": "5 years Python development..."
    }
  ],
  "preferred_skills": [...],
  "projects": [
    {
      "title": "E-commerce Platform",
      "technologies": ["Django", "PostgreSQL"],
      "deployment_proof": True,
      "relevance": "high"
    }
  ],
  "transferable_skills": [...],
  "experience_years": 5,
  "issues": [
    {
      "type": "ambiguous",
      "description": "Education dates unclear"
    }
  ]
}
```

**Score Result** (from Python):
```python
{
  "final_score": 82,
  "breakdown": [
    "Base score: 50",
    "+45 for 3 required skill(s) found",
    "  ✓ Python: \"5 years Python development...\"",
    "+10 for 1 highly relevant project(s)",
    "+5 for 1 deployment proof(s)"
  ],
  "recommendation": "SHORTLIST",
  "details": {
    "required_skills": [...],
    "projects": [...]
  }
}
```

**Final Output**:
```python
{
  "cv_file": "john_doe.pdf",
  "fit_score": 82,
  "recommendation": "SHORTLIST",
  "summary": "Strong Python developer with relevant projects...",
  "breakdown": [...],
  "extracted_data": {...},
  "details": {...},
  "cv_text_preview": "first 500 chars..."
}
```

---

## Technical Implementation

### 1. Parallel Processing

The system uses Python's `ThreadPoolExecutor` for concurrent operations:

**PDF Extraction** (4 workers):
```python
with ThreadPoolExecutor(max_workers=4) as executor:
    futures = {executor.submit(extract_cv_text, cv): cv for cv in cv_files}
    for future in as_completed(futures):
        text = future.result()
```

**CV Analysis** (3 workers, configurable):
```python
with ThreadPoolExecutor(max_workers=parallel_workers) as executor:
    futures = {
        executor.submit(_process_single_cv, name, text, jd): name
        for name, text in cv_texts.items()
    }
    for future in as_completed(futures):
        result = future.result()
        results.append(result)
```

### 2. Thread Safety

AI model access is protected with threading locks:

```python
# In __init__
self.model_lock = threading.Lock()

# In extract_cv_data and generate_summary
with self.model_lock:
    response = self.ai_runner.chat(messages, ...)
```

**Why?** The `llama-cpp` model is not thread-safe for concurrent inference calls.

### 3. GPU Offloading

Configuration for GPU acceleration:

```json
{
  "gpu_layers": -1,        // -1 = all layers on GPU
  "batch_size": 1024,      // Larger batches for GPU
  "context_length": 4096,  // Larger context window
  "use_mmap": true,        // Memory-mapped file I/O
  "use_mlock": false       // Don't lock memory
}
```

The AI model loads once at startup and remains in GPU memory throughout the session.

### 4. Error Handling

**Robust fallbacks at every level**:

1. **PDF Extraction**: 
   - Try pdfplumber → PyPDF2 → skip CV

2. **AI Extraction**: 
   - JSON parsing errors → return empty structure
   - Model errors → log and continue

3. **Scoring**: 
   - Missing data → apply defaults
   - Invalid values → clamp to valid range

4. **GUI**: 
   - Analysis errors → display error message
   - Invalid inputs → show validation warnings

### 5. Progress Tracking

The GUI implements real-time progress updates:

```python
def progress_callback(current, total, elapsed_time):
    # Calculate percentage
    percentage = (current / total) * 100
    
    # Estimate remaining time
    avg_time_per_cv = elapsed_time / current
    remaining = (total - current) * avg_time_per_cv
    
    # Update UI
    update_progress_bar(percentage)
    update_time_estimate(remaining)
```

---

## Performance Optimizations

### 1. Model Caching
- AI model loaded **once** at startup
- Stays in GPU memory for entire session
- Eliminates repeated loading overhead

### 2. Parallel Processing
- **PDF extraction**: 4 concurrent workers
- **CV analysis**: 3 concurrent workers (configurable)
- **Speed gain**: 3-5x faster than sequential

### 3. Optional AI Summaries
- **Disabled by default** for 2x speedup
- Enable when detailed explanations needed
- Controlled by `enable_summaries` flag

### 4. Deterministic Scoring
- Scoring happens in pure Python (no AI)
- Instant calculations (milliseconds)
- No GPU/model overhead

### 5. Smart Batching
- Process CVs as they complete (streaming results)
- No waiting for entire batch
- Better user feedback

### 6. Efficient PDF Processing
- Text extraction parallelized
- Multiple fallback methods
- Skips failed extractions gracefully

---

## User Interfaces

### Command Line Interface (CLI)

**Entry Point**: `main.py`

**Workflow**:
```
1. User provides CV directory path
2. User enters job description (multi-line)
3. System processes all CVs
4. Displays top 10 candidates
5. Saves results to JSON file
```

**Output**:
```
============================================================
TOP 10 CANDIDATES - CV ANALYSIS RESULTS
============================================================

RANK #1
CV File: alice_johnson.pdf
Fit Score: 87/100
Recommendation: SHORTLIST

Summary: Excellent Python developer with 5+ years experience...

Score Breakdown:
  Base score: 50
  +45 for 3 required skill(s) found
    ✓ Python: "5 years Python development..."
    ✓ Django: "Built multiple Django applications..."
    ✓ PostgreSQL: "Experienced with PostgreSQL databases..."
  +10 for 1 highly relevant project(s)
    ✓ E-commerce Platform
  ...
```

### Graphical User Interface (GUI)

**Entry Point**: `gui.py`

**Layout**:

```
┌─────────────────────────────────────────────────────────┐
│                   CV Analysis Tool                      │
├─────────────┬───────────────────────────────────────────┤
│             │                                            │
│  SIDEBAR    │         MAIN PANEL                        │
│             │                                            │
│  • Logo     │  📝 Job Description                       │
│  • Browse   │  ┌─────────────────────────────┐         │
│  • CV Dir   │  │ Enter job description...    │         │
│  • Run      │  │                             │         │
│             │  └─────────────────────────────┘         │
│  Progress:  │                                            │
│  [====] 60% │  🏆 Top Candidates                        │
│             │  [Search] [Sort ↓] [Filter] [Export]     │
│  Stats:     │                                            │
│  • Total: 5 │  ┌───────────────────────────────┐       │
│  • Best: 87 │  │ #1 Alice Johnson         87%  │       │
│             │  │ SHORTLIST                     │       │
│  Settings:  │  │ Python, Django, PostgreSQL    │       │
│  Workers: 3 │  │ [View Details]                │       │
│  Summary:   │  └───────────────────────────────┘       │
│  [ ] OFF    │                                            │
│             │  ┌───────────────────────────────┐       │
│  Appearance │  │ #2 Bob Smith             75%  │       │
│  ○ System   │  │ SHORTLIST                     │       │
│  • Light    │  └───────────────────────────────┘       │
│  ○ Dark     │                                            │
│             │                                            │
└─────────────┴────────────────────────────────────────────┘
```

**Component Interaction**:

1. **User clicks "Browse"** → Sidebar calls callback → GUI opens file dialog
2. **User clicks "Run Analysis"** → Sidebar triggers → GUI starts background thread
3. **Analysis progress** → Callback updates sidebar progress bar
4. **Results ready** → GUI calls MainPanel.display_results()
5. **User searches** → MainPanel filters candidates → Updates display
6. **User clicks "View Details"** → Opens DetailsModal with full data
7. **User clicks "Export"** → Opens ExportDialog → Saves to file

---

## Configuration Reference

### `config.json`

```json
{
  // Model settings
  "model_folder": "model",
  "model_name": "Qwen3-4B.gguf",
  
  // GPU/Performance
  "context_length": 4096,      // Max tokens in context
  "batch_size": 1024,          // GPU batch size
  "cpu_threads": 4,            // CPU thread count
  "gpu_layers": -1,            // -1 = all layers on GPU
  "use_mmap": true,            // Memory-mapped I/O
  "use_mlock": false,          // Lock memory pages
  
  // Generation parameters
  "max_tokens": 1024,          // Max output length
  "temperature": 0.3,          // Low = deterministic
  "top_p": 0.9,                // Nucleus sampling
  "top_k": 40,                 // Top-k sampling
  "repeat_penalty": 1.1,       // Repetition penalty
  
  // Application settings
  "parallel_workers": 3,       // Concurrent CV analysis
  "enable_summaries": false,   // AI summaries (slower)
  "pdf_extraction_workers": 4, // PDF extraction workers
  
  // Interface
  "stream": false,             // Streaming output
  "echo": false,               // Echo input
  "verbose": false,            // Verbose logging
  "use_chat_format": true      // Use chat completion
}
```

---

## Summary

The CV Scanner is a **high-performance, privacy-focused AI application** that combines:

1. **Local LLM inference** for intelligent data extraction
2. **Deterministic Python scoring** for accurate, reproducible results
3. **Parallel processing** for 3-5x speed improvements
4. **Modern GUI** with real-time feedback
5. **Flexible configuration** to balance speed vs. quality

The hybrid approach (AI + Python) provides the best of both worlds:
- AI understands unstructured CV text and extracts relevant data
- Python ensures mathematical accuracy and consistent scoring
- GPU acceleration makes local inference practical
- Modular architecture enables easy customization

**Result**: A fast, accurate, transparent CV analysis system that respects privacy and runs entirely on local hardware.
