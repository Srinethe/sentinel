#!/usr/bin/env python3
"""
Generate a realistic "dirty" denial PDF for testing the Intake agent.
This creates a document that looks like it came from a fax machine.
"""

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib.colors import black, darkblue, darkred
import random
from pathlib import Path

def add_text_noise(c, x, y, text, font_name="Helvetica", font_size=10, color=black):
    """Add text with random variations to simulate scan artifacts and misalignment"""
    # More pronounced random offset to simulate scan misalignment and skew
    offset_x = random.uniform(-1.5, 1.5)
    offset_y = random.uniform(-1.5, 1.5)
    
    # Occasionally make text slightly faded (like poor scan quality)
    if random.random() < 0.15:  # 15% chance
        color_factor = random.uniform(0.6, 0.8)
        # Handle both RGB tuples and Color objects
        if isinstance(color, tuple):
            c.setFillColorRGB(color[0] * color_factor, color[1] * color_factor, color[2] * color_factor)
        else:
            # For Color objects, use a grayish faded version
            c.setFillColorRGB(0.4 * color_factor, 0.4 * color_factor, 0.4 * color_factor)
    else:
        c.setFillColor(color)
    
    c.setFont(font_name, font_size)
    c.drawString(x + offset_x, y + offset_y, text)

def generate_denial_pdf(output_path: str):
    """Generate a realistic "dirty" denial PDF with heavy fax-like artifacts"""
    c = canvas.Canvas(output_path, pagesize=letter)
    width, height = letter
    
    # Add heavy background "noise" - light gray rectangles to simulate scan artifacts
    c.setFillColorRGB(0.92, 0.92, 0.92)
    for _ in range(15):
        x = random.uniform(0, width)
        y = random.uniform(0, height)
        w = random.uniform(20, 120)
        h = random.uniform(10, 35)
        c.rect(x, y, w, h, fill=1, stroke=0)
    
    # Add "smudges" - darker gray spots (like coffee stains or dirt)
    c.setFillColorRGB(0.80, 0.80, 0.80)
    for _ in range(5):
        x = random.uniform(50, width - 50)
        y = random.uniform(50, height - 50)
        c.circle(x, y, random.uniform(15, 40), fill=1, stroke=0)
    
    # Add some darker "marks" (like pen marks or creases)
    c.setFillColorRGB(0.70, 0.70, 0.70)
    for _ in range(3):
        x = random.uniform(100, width - 100)
        y = random.uniform(100, height - 100)
        c.ellipse(x, y, x + random.uniform(30, 60), y + random.uniform(5, 15), fill=1, stroke=0)
    
    # Header - Blue Cross Shield (with slight rotation to simulate misalignment)
    c.saveState()
    # Slight rotation to make it look scanned crooked
    c.translate(50, height - 50)
    c.rotate(random.uniform(-0.5, 0.5))
    c.setFillColor(darkblue)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(0, 0, "BLUECROSS SHIELD OF CALIFORNIA")
    c.restoreState()
    
    c.setFillColor(black)
    c.setFont("Helvetica", 10)
    c.drawString(50, height - 70, "Utilization Management Department")
    c.drawString(50, height - 85, "PO Box 9000, San Francisco, CA 94105")
    
    # Date
    c.setFont("Helvetica-Bold", 11)
    c.drawString(50, height - 110, "DATE: January 10, 2026")
    
    # Title
    c.setFillColor(darkred)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, height - 140, "NOTICE OF MEDICAL NECESSITY DENIAL")
    
    # Patient Information Section
    c.setFillColor(black)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, height - 170, "PATIENT INFORMATION:")
    
    y_pos = height - 190
    c.setFont("Helvetica", 10)
    patient_info = [
        "* Patient Name: DOE, JONATHAN",
        "Account Number: #AH-88291-00",
        "Date of Birth: 05/12/1978",
        "Provider: AGI House General Hospital",
        "Claim ID: BXS-99210-X"
    ]
    
    for info in patient_info:
        add_text_noise(c, 50, y_pos, info, "Helvetica", 10)
        y_pos -= 18
    
    # Determination
    y_pos -= 10
    c.setFont("Helvetica-Bold", 12)
    c.setFillColor(darkred)
    add_text_noise(c, 50, y_pos, "DETERMINATION:", "Helvetica-Bold", 12, darkred)
    
    y_pos -= 20
    c.setFont("Helvetica", 11)
    c.setFillColor(black)
    determination = "Your request for Inpatient Hospitalization (Level of Care: Acute) has been DENIED."
    # Wrap text
    words = determination.split()
    line = ""
    for word in words:
        if len(line + word) < 80:
            line += word + " "
        else:
            add_text_noise(c, 50, y_pos, line.strip(), "Helvetica", 11)
            y_pos -= 16
            line = word + " "
    if line:
        add_text_noise(c, 50, y_pos, line.strip(), "Helvetica", 11)
    
    # Clinical Reasoning
    y_pos -= 25
    c.setFont("Helvetica-Bold", 12)
    add_text_noise(c, 50, y_pos, "CLINICAL REASONING:", "Helvetica-Bold", 12)
    
    y_pos -= 20
    c.setFont("Helvetica", 10)
    reasoning_paragraphs = [
        "Upon review of the clinical documentation submitted via fax on 01/09/2026, it has been",
        "determined that the criteria for Acute Inpatient Care were not met. The physician notes",
        "indicate a diagnosis of Hyperkalemia (ICD-10: E87.5) with a serum potassium level of 5.4 mmol/L.",
        "",
        "Per Payer Policy Manual (Section 4.2.1), Acute Inpatient Admission for Hyperkalemia requires:",
        "",
        "  • Serum potassium ≥ 6.0 mmol/L OR",
        "  • Documented EKG changes (Peaked T-waves, QRS widening) OR",
        "  • Acute Renal Failure.",
        "",
        "As the submitted labs show 5.4 mmol/L and no EKG documentation was provided, the stay",
        "is considered Medically Unnecessary. This patient could have been managed in an",
        "Observation or Outpatient setting."
    ]
    
    for para in reasoning_paragraphs:
        if para.strip():
            add_text_noise(c, 50, y_pos, para, "Helvetica", 10)
        y_pos -= 16
    
    # Peer-to-Peer Section
    y_pos -= 15
    c.setFont("Helvetica-Bold", 12)
    c.setFillColor(darkred)
    add_text_noise(c, 50, y_pos, "PEER-TO-PEER REVIEW WINDOW:", "Helvetica-Bold", 12, darkred)
    
    y_pos -= 20
    c.setFont("Helvetica", 10)
    c.setFillColor(black)
    p2p_text = [
        "You have a window of 24 HOURS from the receipt of this notice to request a",
        "Peer-to-Peer (P2P) review with a Medical Director. Failure to request review by",
        "01/11/2026 17:00 PST will result in a final administrative denial."
    ]
    
    for line in p2p_text:
        add_text_noise(c, 50, y_pos, line, "Helvetica", 10)
        y_pos -= 16
    
    # Contact Info
    y_pos -= 20
    c.setFont("Helvetica-Bold", 11)
    add_text_noise(c, 50, y_pos, "CONTACT FOR APPEALS:", "Helvetica-Bold", 11)
    
    y_pos -= 18
    c.setFont("Helvetica", 10)
    add_text_noise(c, 50, y_pos, "Phone: (800) 555-0199 | Fax: (800) 555-0100 (Attn: Appeals Dept)", "Helvetica", 10)
    
    # Add "fax artifacts" - horizontal lines (common in faxes)
    c.setStrokeColorRGB(0.5, 0.5, 0.5)
    c.setLineWidth(0.4)
    for _ in range(8):
        x1 = random.uniform(30, width - 30)
        y1 = random.uniform(100, height - 200)
        x2 = x1 + random.uniform(150, 400)
        y2 = y1 + random.uniform(-3, 3)
        c.line(x1, y1, x2, y2)
    
    # Add vertical "scan lines" (like fax transmission errors)
    c.setLineWidth(0.3)
    for _ in range(5):
        x = random.uniform(50, width - 50)
        c.line(x, 80, x, height - 80)
    
    # Add some diagonal "streaks" (like paper creases or fold marks)
    c.setStrokeColorRGB(0.65, 0.65, 0.65)
    c.setLineWidth(0.2)
    for _ in range(4):
        x1 = random.uniform(100, width - 100)
        y1 = random.uniform(200, height - 200)
        angle = random.uniform(-30, 30)
        length = random.uniform(50, 150)
        x2 = x1 + length * (1 if random.random() > 0.5 else -1)
        y2 = y1 + length * 0.3 * (1 if random.random() > 0.5 else -1)
        c.line(x1, y1, x2, y2)
    
    # Add some "dots" and "specks" (like dust or ink spots)
    c.setFillColorRGB(0.4, 0.4, 0.4)
    for _ in range(20):
        x = random.uniform(0, width)
        y = random.uniform(0, height)
        size = random.uniform(1, 3)
        c.circle(x, y, size, fill=1, stroke=0)
    
    # Footer
    y_pos = 50
    c.setFont("Helvetica", 8)
    c.setFillColorRGB(0.5, 0.5, 0.5)
    c.drawString(50, y_pos, "This is an automated notice. Please retain for your records.")
    
    c.save()
    print(f"✅ Generated denial PDF: {output_path}")

if __name__ == "__main__":
    output_dir = Path(__file__).parent / "app" / "data" / "sample_denials"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "denial_bluecross_hyperkalemia.pdf"
    
    generate_denial_pdf(str(output_path))
    print(f"\n📄 PDF saved to: {output_path}")
    print(f"   You can now use this file to test the Intake agent!")
