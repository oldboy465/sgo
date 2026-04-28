import pandas as pd
import pdfkit
import io
from flask import render_template, current_app

class ExportService:
    """
    Serviço responsável por gerar arquivos binários (Excel e PDF)
    a partir dos dados do banco de dados.
    """

    @staticmethod
    def generate_excel(oficios_list):
        """
        Gera um arquivo Excel (.xlsx) a partir de uma lista de objetos Oficio.
        Retorna: BytesIO object contendo o arquivo.
        """
        # 1. Transformar objetos SQLAlchemy em lista de dicionários
        data = []
        for of in oficios_list:
            item = {
                'Nº Ofício': of.numero_oficio,
                'Processo SEI': of.processo_sei,
                'Título': of.titulo,
                'Tipo': of.tipo_processo.nome if of.tipo_processo else '-',
                'Status': of.status,
                'Data Envio': of.data_envio.strftime('%d/%m/%Y') if of.data_envio else '-',
                'Emissor (Setor)': of.setor_emissor.sigla if of.setor_emissor else '-',
                'Emissor (Nome)': of.emissor_nome,
                'Setor Atual': of.setor_atual.sigla if of.setor_atual else '-',
                'Objeto Resumido': of.objeto_resumido,
                'Último Despacho': of.ultimo_despacho
            }
            data.append(item)

        # 2. Criar DataFrame do Pandas
        df = pd.DataFrame(data)

        # 3. Salvar em memória (BytesIO)
        output = io.BytesIO()
        
        # Requer 'openpyxl' instalado
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Relatório de Ofícios')
            
            # Ajuste automático de largura de coluna (Opcional/Estético)
            worksheet = writer.sheets['Relatório de Ofícios']
            for column in df:
                column_width = max(df[column].astype(str).map(len).max(), len(column))
                col_idx = df.columns.get_loc(column)
                worksheet.column_dimensions[chr(65 + col_idx)].width = column_width + 2

        output.seek(0)
        return output

    @staticmethod
    def generate_pdf(template_name, context_data):
        """
        Gera um arquivo PDF a partir de um template HTML.
        
        IMPORTANTE: Requer o software 'wkhtmltopdf' instalado no Windows.
        Baixe em: https://wkhtmltopdf.org/downloads.html
        """
        
        # Renderiza o HTML com os dados (Jinja2)
        html_content = render_template(template_name, **context_data)
        
        # Configurações do PDF
        options = {
            'page-size': 'A4',
            'encoding': 'UTF-8',
            'margin-top': '20mm',
            'margin-right': '20mm',
            'margin-bottom': '20mm',
            'margin-left': '20mm',
            'no-outline': None
        }

        try:
            # Tenta gerar o PDF
            # Se der erro de "No wkhtmltopdf executable found", você precisa
            # apontar o caminho do executável aqui:
            # config = pdfkit.configuration(wkhtmltopdf=r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe')
            # pdf = pdfkit.from_string(html_content, False, configuration=config, options=options)
            
            pdf = pdfkit.from_string(html_content, False, options=options)
            return pdf
            
        except OSError as e:
            print(f"ERRO CRÍTICO PDFKIT: {e}")
            print("Verifique se o wkhtmltopdf está instalado e no PATH do sistema.")
            return None