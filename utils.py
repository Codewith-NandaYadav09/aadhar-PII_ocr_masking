import os
import re
import cv2
import pytesseract
from pathlib import Path
from PIL import Image
from pdf2image import convert_from_path
from pytesseract import Output


def extract_text_from_image(image_path):
    """
    Extract text from an image using Tesseract OCR.
    
    Args:
        image_path (str): Path to the image file
        
    Returns:
        str: Extracted text from the image
    """
    try:
        # Read the image
        img = cv2.imread(image_path)
        if img is None:
            return ""
        
        # Preprocess image for better OCR accuracy
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Scale image to 300 DPI equivalent for better OCR accuracy
        scale_factor = 2
        scaled = cv2.resize(gray, None, fx=scale_factor, fy=scale_factor, 
                           interpolation=cv2.INTER_CUBIC)
        
        # Apply thresholding to improve contrast
        _, thresh = cv2.threshold(scaled, 150, 255, cv2.THRESH_BINARY)
        
        # Extract text using Tesseract
        text = pytesseract.image_to_string(thresh)
        return text
    except Exception as e:
        print(f"Error extracting text from {image_path}: {e}")
        return ""


def convert_pdf_to_images(pdf_path):
    """
    Convert PDF pages to images.
    
    Args:
        pdf_path (str): Path to the PDF file
        
    Returns:
        list: List of PIL Image objects
    """
    try:
        images = convert_from_path(pdf_path)
        return images
    except Exception as e:
        print(f"Error converting PDF {pdf_path}: {e}")
        return []


def detect_and_mask_aadhaar(text):
    """
    Detect Aadhaar numbers in text and return masked version.
    Aadhaar format: 12 digits, optionally with spaces (e.g., 1234 5678 9012 or 123456789012)
    Masking rule: Replace first 8 digits with X (e.g., XXXX XXXX 9012)
    
    Args:
        text (str): Text containing potential Aadhaar numbers
        
    Returns:
        tuple: (text_with_masked_aadhaar, list_of_found_aadhaar_numbers)
    """
    found_aadhaar = []
    
    # Pattern 1: 12 digits with spaces (XXXX XXXX XXXX)
    pattern_with_spaces = r'\b(\d{4}\s\d{4}\s\d{4})\b'
    
    def mask_spaced(match):
        aadhaar = match.group(1)
        found_aadhaar.append(aadhaar)
        # Replace first 8 digits (including space) with X
        return 'XXXX XXXX ' + aadhaar[-4:]
    
    text = re.sub(pattern_with_spaces, mask_spaced, text)
    
    # Pattern 2: 12 consecutive digits (XXXXXXXXXXXX)
    pattern_no_spaces = r'\b(\d{12})\b'
    
    def mask_consecutive(match):
        aadhaar = match.group(1)
        found_aadhaar.append(aadhaar)
        # Replace first 8 digits with X
        return 'XXXX XXXX' + aadhaar[-4:]
    
    text = re.sub(pattern_no_spaces, mask_consecutive, text)
    
    return text, found_aadhaar


def mask_aadhaar_in_image(image_path, output_path):
    """
    Extract text from image, detect Aadhaar numbers, and create masked version.
    Masks only the first 8 digits, leaving the last 4 visible.
    
    Args:
        image_path (str): Path to input image
        output_path (str): Path to save masked image
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Read the image with OpenCV
        img = cv2.imread(image_path)
        if img is None:
            return False
        
        # Get OCR data with bounding boxes
        data = pytesseract.image_to_data(img, output_type=Output.DICT)
        
        # Find bounding boxes for Aadhaar numbers
        full_mask_boxes = []  # boxes to mask completely
        partial_mask = []     # (idx, mask_chars, total_chars) for partial masking
        i = 0
        n_boxes = len(data['text'])
        while i < n_boxes:
            text = data['text'][i].strip()
            if text.isdigit():
                if len(text) == 12:
                    # 12 consecutive digits: mask first 8 chars
                    partial_mask.append((i, 8, 12))
                    i += 1
                    continue
                elif len(text) == 4 and i + 2 < n_boxes:
                    # Check for spaced Aadhaar: 4 digits, space, 4 digits, space, 4 digits
                    text1 = data['text'][i+1].strip()
                    text2 = data['text'][i+2].strip()
                    if text1.isdigit() and len(text1) == 4 and text2.isdigit() and len(text2) == 4:
                        total_digits = text + text1 + text2
                        if len(total_digits) == 12:
                            # Mask first two boxes (first 8 digits), leave third visible
                            full_mask_boxes.extend([i, i+1])
                            i += 3
                            continue
            i += 1
        
        # Mask the detected regions with 'X' symbols
        masked = False
        font = cv2.FONT_HERSHEY_SIMPLEX
        thickness = 2
        
        for idx in full_mask_boxes:
            x = data['left'][idx]
            y = data['top'][idx]
            w = data['width'][idx]
            h = data['height'][idx]
            # Draw black background
            cv2.rectangle(img, (x, y), (x + w, y + h), (0, 0, 0), -1)
            # Draw white 'XXXX'
            font_scale = h / 20.0
            text_size = cv2.getTextSize('XXXX', font, font_scale, thickness)[0]
            text_x = x + (w - text_size[0]) // 2
            text_y = y + (h + text_size[1]) // 2
            cv2.putText(img, 'XXXX', (text_x, text_y), font, font_scale, (255, 255, 255), thickness)
            masked = True
        
        for idx, mask_chars, total_chars in partial_mask:
            x = data['left'][idx]
            y = data['top'][idx]
            w = data['width'][idx]
            h = data['height'][idx]
            mask_w = int(w * mask_chars / total_chars)
            # Draw black over left part
            cv2.rectangle(img, (x, y), (x + mask_w, y + h), (0, 0, 0), -1)
            # Draw white 'XXXXXXXX'
            font_scale = h / 20.0
            text = 'X' * mask_chars
            text_size = cv2.getTextSize(text, font, font_scale, thickness)[0]
            text_x = x + (mask_w - text_size[0]) // 2
            text_y = y + (h + text_size[1]) // 2
            cv2.putText(img, text, (text_x, text_y), font, font_scale, (255, 255, 255), thickness)
            masked = True
        
        if masked:
            print(f"Masked Aadhaar in {image_path}")
        
        # Save the image
        cv2.imwrite(output_path, img)
        return True
    except Exception as e:
        print(f"Error processing image {image_path}: {e}")
        return False


def process_document(file_path, output_dir):
    """
    Main document processing function called by multiprocessing pool.
    Handles JPG, PNG, and PDF documents.
    
    Args:
        file_path (str): Path to input document
        output_dir (str): Directory to save processed documents
        
    Returns:
        bool: True if processing successful, False otherwise
    """
    try:
        file_path = Path(file_path)
        output_dir = Path(output_dir)
        
        # Ensure output directory exists
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Get file extension
        ext = file_path.suffix.lower()
        
        if ext in ['.jpg', '.jpeg', '.png']:
            # Process image directly
            output_path = output_dir / file_path.name
            return mask_aadhaar_in_image(str(file_path), str(output_path))
        
        elif ext == '.pdf':
            # Convert PDF to images and process each page
            images = convert_pdf_to_images(str(file_path))
            if not images:
                return False
            
            # Save processed PDF pages as images
            base_name = file_path.stem
            for idx, image in enumerate(images):
                output_path = output_dir / f"{base_name}_page_{idx + 1}.png"
                
                # Save image temporarily for processing
                temp_path = output_dir / f"temp_{idx}.png"
                image.save(str(temp_path))
                
                # Process the image
                mask_aadhaar_in_image(str(temp_path), str(output_path))
                
                # Clean up temporary file
                if temp_path.exists():
                    temp_path.unlink()
            
            return True
        else:
            print(f"Unsupported file format: {ext}")
            return False
    
    except Exception as e:
        print(f"Error processing document {file_path}: {e}")
        return False
