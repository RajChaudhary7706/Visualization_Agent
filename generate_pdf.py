from fpdf import FPDF

# Read the markdown documentation
with open("Visualization_Agent_Project_Documentation.md", "r", encoding="utf-8") as f:
    lines = f.readlines()

pdf = FPDF()
pdf.add_page()
pdf.set_auto_page_break(auto=True, margin=15)
pdf.set_font("Arial", size=12)

for line in lines:
    # Simple markdown to PDF: treat '#' as title, '-' as bullet, else normal text
    if line.startswith('# '):
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(0, 10, line[2:].strip(), ln=True)
        pdf.set_font("Arial", size=12)
    elif line.startswith('## '):
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(0, 10, line[3:].strip(), ln=True)
        pdf.set_font("Arial", size=12)
    elif line.startswith('- '):
        pdf.cell(10)
        pdf.cell(0, 10, u"• " + line[2:].strip(), ln=True)
    elif line.startswith('```'):
        continue  # skip code block markers
    elif line.strip() == '':
        pdf.ln(5)
    else:
        pdf.multi_cell(0, 10, line.strip())

pdf.output("Visualization_Agent_Project_Documentation.pdf")
print("PDF generated: Visualization_Agent_Project_Documentation.pdf")
