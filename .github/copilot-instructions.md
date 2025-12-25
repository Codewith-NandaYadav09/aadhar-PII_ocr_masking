# Copilot Instructions: Document Processing & Aadhaar Masking

## Project Overview
A high-performance document processing solution that detects and masks Aadhaar numbers in large-scale document batches (200,000+ documents/hour target). Operates on CPU-only hardware (thin infrastructure). Processes diverse document types: Aadhaar cards, PAN cards, loan agreements, account opening forms, credit card applications.

## Architecture & Key Components

### Core Modules
- **`main.py`**: Entry point managing parallel document processing
  - Multiprocessing pool (capped at 8 processes) for CPU-bound OCR/image processing
  - Recursive file discovery for supported formats (`.jpg`, `.jpeg`, `.png`, `.pdf`)
  - Performance metrics tracking (throughput calculation in documents/hour)
  - **Key decision**: `min(cpu_count(), 8)` prevents resource exhaustion on high-core systems

- **`utils.py`**: Document processing pipeline (currently empty - needs implementation)
  - Should contain `process_document(file_path, output_dir)` function called by multiprocessing pool
  - Expected to orchestrate: image extraction → OCR → Aadhaar detection → masking → output

### Data Flow
```
Input Directory (recursively scanned)
    ↓ [File discovery: .jpg/.jpeg/.png/.pdf]
    ↓
Multiprocessing Pool (8 workers)
    ↓ [process_document(file, output_dir)]
    ↓
Output Directory (processed documents saved)
```

## Critical Patterns & Conventions

### Parallel Processing Strategy
- **Approach**: Multiprocessing (not threading) due to Python GIL and CPU-bound nature of OCR
- **Pool size**: Hardcoded to 8-process maximum despite system core count
- **Implication**: Performance optimization targets moderate hardware; larger systems don't gain additional benefit
- **When adding tasks**: Use `Pool.starmap()` with pre-prepared argument tuples

### Supported Document Formats
- Images: `.jpg`, `.jpeg`, `.png` (via PIL/OpenCV)
- PDFs: `.pdf` (via pdf2image for image extraction)
- Strategy: Convert all formats to images before OCR (consistent pipeline)

### Performance Metrics
- **Target throughput**: 200,000 documents/hour (~18ms per document on 8 workers)
- **Calculation**: `throughput = num_documents / elapsed_seconds * 3600`
- **Hardware constraint**: CPU-only (no GPU acceleration available)
- **OCR strategy**: Use lightweight OCR libraries; Tesseract preferred for CPU efficiency

### Aadhaar Detection & Masking Pattern
- **Format**: 12-digit number with optional spaces (e.g., `1234 5678 9012`, `123456789012`)
- **Masking rule**: First 8 digits replaced with `X` (e.g., `XXXX XXXX 9012`)
- **Implementation location**: `utils.py` (to be implemented)
- **Detection method**: Regex pattern with optional spaces + OCR extraction from document images

## Development Workflows

### Running the Application
```powershell
# Basic usage
python main.py <input_directory> <output_directory>

# Example with sample documents
python test_generate_samples.py
python main.py sample_documents output_documents
```

### Generating Test Data
- **Script**: `test_generate_samples.py` creates 3 sample images with embedded Aadhaar numbers
- **Purpose**: Local testing before processing real documents
- **Output directory**: `sample_documents/` (created automatically)
- **Font handling**: Falls back to default font if Arial unavailable (cross-platform compatibility)

### Testing & Validation
- No formal test framework yet; validation is manual
- **Suggested approach**: Verify masked Aadhaar format in output (first 8 digits should be `X`)
- **Performance validation**: Monitor throughput calculation output against 200,000 doc/hour target

## Dependencies & Environment

### Core Libraries (from `requirements.txt`)
- **`pytesseract`**: OCR extraction from images (wraps Tesseract binary)
- **`opencv-python`**: Image processing (scaling, contrast adjustment for OCR accuracy)
- **`pdf2image`**: Convert PDFs to images before OCR
- **`Pillow`**: Image manipulation and creation
- **`regex`**: Advanced regex patterns for flexible Aadhaar format detection
- **`tesseract`**: System dependency (binary, not Python package)

### Critical Setup Note
- Tesseract-OCR must be installed separately on system (not via pip)
- PyTesseract requires system `tesseract` binary in PATH
- Typical installation: `choco install tesseract` (Windows) or `apt-get install tesseract-ocr` (Linux)

## Performance Optimization Principles

### Design Constraints
- **No GPU**: All processing CPU-bound; optimize for single-core efficiency
- **Batch operation**: Multiprocessing enables horizontal scaling across cores
- **Memory-efficient OCR**: Tesseract is lightweight compared to deep learning models

### Implementation Guidelines
1. **Image preprocessing**: Minimal steps only (scale to 300 DPI+ for OCR accuracy, but avoid expensive filters)
2. **Regex over ML**: Use pattern matching for Aadhaar detection instead of training models (lightweight, deterministic)
3. **Early filtering**: Skip non-image documents before entering OCR pipeline
4. **Streaming output**: Write masked documents immediately rather than batching in memory

## Known Issues & Future Work
- **`main.py` incomplete**: Print statements missing format arguments (lines with `".2f"`)
- **`utils.py` stub**: Needs full implementation of `process_document()` function
- **No error handling**: Missing try-catch for corrupted images, OCR failures, PDF extraction errors
- **TODO tracker**: `TODO.md` documents main.py as done; utils.py and testing remain

## Code Examples & Patterns

### Proper Multiprocessing Usage (from main.py)
```python
args = [(str(file), output_dir) for file in files]
with Pool(processes=num_processes) as pool:
    pool.starmap(process_document, args)  # Pass tuples of arguments
```
*Always pre-format arguments as tuples; starmap unpacks them into function parameters.*

### File Discovery Pattern
```python
supported_extensions = ['.jpg', '.jpeg', '.png', '.pdf']
files = []
for ext in supported_extensions:
    files.extend(Path(input_dir).glob(f'**/*{ext}'))  # Recursive search
```
*Use pathlib for cross-platform path handling; glob with `**/*` for recursive traversal.*
