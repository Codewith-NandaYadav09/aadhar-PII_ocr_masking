from PIL import Image, ImageDraw, ImageFont
import os

def create_sample_image_with_aadhaar(filename, text, aadhaar_number):
    # Create a blank image
    img = Image.new('RGB', (800, 600), color='white')
    draw = ImageDraw.Draw(img)

    # Try to use a default font
    try:
        font = ImageFont.truetype("arial.ttf", 20)
    except:
        font = ImageFont.load_default()

    # Draw the text
    draw.text((50, 50), text, fill='black', font=font)
    draw.text((50, 100), f"Aadhaar Number: {aadhaar_number}", fill='black', font=font)

    # Save the image
    img.save(filename)
    print(f"Sample image saved as {filename}")

if __name__ == "__main__":
    # Create sample directory
    os.makedirs("sample_documents", exist_ok=True)

    # Create sample images with Aadhaar numbers
    samples = [
        ("sample_documents/sample1.jpg", "This is a sample Aadhaar document.", "1234 5678 9012"),
        ("sample_documents/sample2.jpg", "Another document with Aadhaar.", "9876 5432 1098"),
        ("sample_documents/sample3.jpg", "Loan agreement document.", "1111 2222 3333"),
    ]

    for filename, text, aadhaar in samples:
        create_sample_image_with_aadhaar(filename, text, aadhaar)

    print("Sample documents generated.")
