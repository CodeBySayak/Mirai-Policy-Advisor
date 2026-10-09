from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet

def create_pdf(input_file, output_file):
    doc = SimpleDocTemplate(output_file, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    with open(input_file, "r") as f:
        for line in f:
            if line.strip():
                story.append(Paragraph(line.strip(), styles['Normal']))
                
    doc.build(story)

create_pdf("handbook.txt", "handbook.pdf")
print("handbook.pdf created!")
