import os
import sys
import time
from pathlib import Path
from multiprocessing import Pool, cpu_count
from utils import process_document

def process_documents_parallel(input_dir, output_dir, num_processes=None):
    """Process documents in parallel using multiprocessing."""
    if num_processes is None:
        num_processes = min(cpu_count(), 8)  # Limit to 8 processes

    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Get list of files to process
    supported_extensions = ['.jpg', '.jpeg', '.png', '.pdf']
    files = []
    for ext in supported_extensions:
        files.extend(Path(input_dir).glob(f'**/*{ext}'))

    if not files:
        print(f"No supported files found in {input_dir}")
        return

    print(f"Found {len(files)} documents to process.")

    # Prepare arguments for multiprocessing
    args = [(str(file), output_dir) for file in files]

    start_time = time.time()

    with Pool(processes=num_processes) as pool:
        pool.starmap(process_document, args)

    end_time = time.time()
    total_time = end_time - start_time
    throughput = len(files) / total_time * 3600  # documents per hour

    print(".2f")
    print(".2f")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python main.py <input_directory> <output_directory>")
        sys.exit(1)

    input_dir = sys.argv[1]
    output_dir = sys.argv[2]

    process_documents_parallel(input_dir, output_dir)
