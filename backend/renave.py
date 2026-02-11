from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4

def gerar_pdf(veiculo):
    file_name = f"renave_{veiculo.id}.pdf"
    doc = SimpleDocTemplate(file_name, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()

    elements.append(Paragraph("Documento RENAVE", styles["Title"]))
    elements.append(Spacer(1, 20))
    elements.append(Paragraph(f"Veículo: {veiculo.marca} {veiculo.modelo}", styles["Normal"]))
    elements.append(Paragraph(f"Placa: {veiculo.placa}", styles["Normal"]))
    elements.append(Paragraph(f"Status: {veiculo.status}", styles["Normal"]))

    doc.build(elements)
    return file_name
