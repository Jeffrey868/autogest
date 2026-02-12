import requests
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4


# --- PARTE 1: COMUNICAÇÃO COM SERPRO ---
class SerproAPI:
    def __init__(self, cert_path, cert_pass):
        self.base_url = "https://api.serpro.gov.br/renave/v1"
        self.cert = (cert_path, cert_pass)  # Certificado .pfx do seu cliente

    def registrar_entrada(self, dados_veiculo):
        """
        Envia os dados para o SERPRO. 
        O retorno 'res' contém o PDF oficial ou o protocolo.
        """
        # Exemplo de endpoint real do SERPRO
        endpoint = f"{self.base_url}/estoque/entrada"
        # Aqui enviamos o certificado digital para autenticar
        # res = requests.post(endpoint, json=dados_veiculo, cert=self.cert)
        # return res.json()
        return {"status": "sucesso", "protocolo": "12345ABC"}  # Simulação


# --- PARTE 2: GERAÇÃO DE DOCUMENTO (Sua função atualizada) ---
def gerar_pdf_renave(dados_serpro, veiculo):
    """
    Usa o seu código ReportLab para criar um espelho do registro
    """
    file_name = f"comprovante_renave_{veiculo.id}.pdf"
    doc = SimpleDocTemplate(file_name, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()

    elements.append(Paragraph("REGISTRO NACIONAL DE VEÍCULOS EM ESTOQUE", styles["Title"]))
    elements.append(Spacer(1, 12))
    elements.append(Paragraph(f"<b>Protocolo Governo:</b> {dados_serpro['protocolo']}", styles["Normal"]))
    elements.append(Spacer(1, 10))
    elements.append(Paragraph(f"Veículo: {veiculo.marca} {veiculo.modelo}", styles["Normal"]))
    elements.append(Paragraph(f"Placa: {veiculo.placa}", styles["Normal"]))
    elements.append(Paragraph(f"Valor Declarado: R$ {veiculo.valor}", styles["Normal"]))

    doc.build(elements)
    return file_name