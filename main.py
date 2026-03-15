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

    print(f"Processed {len(files)} documents in {total_time:.2f} seconds")
    print(f"Throughput: {throughput:.2f} documents/hour")

def scan_and_produce(input_dir):
    """Producer process: Scan dir and send paths to Kafka."""
    supported_extensions = ['.jpg', '.jpeg', '.png', '.pdf']
    files = []
    for ext in supported_extensions:
        files.extend(Path(input_dir).glob(f'**/*{ext}'))
    
    print(f"Producer found {len(files)} documents to send.")
    
    for file in files:
        from utils import send_document_path
        send_document_path(str(file))


def run_kafka_pipeline(input_dir, output_dir, num_producers=2, num_consumers=8):
    """Run Kafka-based pipeline with multiprocessing producers/consumers."""
    from multiprocessing import Process
    from utils import process_kafka_document
    import os
    os.makedirs(output_dir, exist_ok=True)
    
    processes = []
    
    # Start producers
    for _ in range(num_producers):
        p = Process(target=scan_and_produce, args=(input_dir,))
        p.start()
        processes.append(p)
    
    # Start consumers
    for _ in range(num_consumers):
        p = Process(target=process_kafka_document, args=(output_dir,))
        p.start()
        processes.append(p)
    
    try:
        for p in processes:
            p.join()
    except KeyboardInterrupt:
        print("Shutting down...")
        for p in processes:
            p.terminate()
            p.join()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Document processing pipeline")
    parser.add_argument('input_dir', help="Input directory")
    parser.add_argument('output_dir', help="Output directory")
    parser.add_argument('--kafka', action='store_true', help="Use Kafka pipeline")
    parser.add_argument('--num-producers', type=int, default=2, help="Number of producer processes")
    parser.add_argument('--num-consumers', type=int, default=8, help="Number of consumer processes")
    
    args = parser.parse_args()
    
    if args.kafka:
        print("Starting Kafka pipeline...")
        run_kafka_pipeline(args.input_dir, args.output_dir, args.num_producers, args.num_consumers)
    else:
        process_documents_parallel(args.input_dir, args.output_dir)
