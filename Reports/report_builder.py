import os
from reportlab.lib.pagesizes import letter, A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
import datetime
# from portfolio_management.Reports.image_builder import CandlestickChartGenerator
from PIL import Image


class ReportGenerator:
    """
    # Esempio d'uso:
    # report = ReportGenerator()
    # report.add_title('Analisi dei Dati 2023')
    # report.add_to_left_column('Introduzione al report.')
    # report.add_to_right_column('Osservazioni importanti.')
    # report.image_path('path/to/graph1.png')
    # report.save_report('report.txt')
    """
    def __init__(self):
        self.title = ""
        self.contents = []
        self.report_path = '/home/dp/PycharmProjects/portfolio_management/portfolio_management/Reports/Data/tmp'
        # self.toggle = True
        self.date = datetime.datetime.now().strftime("%Y-%m-%d")

    def add_title(self, title):
        self.title = f"{title} - Date {self.date}"
    
    def add_content(self, content):
        self.contents.append(('text', content))

    def add_commented_image(self, df, comment = None, image_path= None):
        if image_path is not None:
            # Carica l'immagine
            with Image.open(image_path) as img:
                # Calcola le nuove dimensioni (90% delle dimensioni originali)
                new_width = int(img.width * 0.8)
                new_height = int(img.height * 0.8)

                # Ridimensiona l'immagine
                img = img.resize((new_width, new_height))

                # Salva l'immagine ridimensionata (puoi sovrascrivere o salvare come nuovo file)
                img.save(image_path)  # Sovrascrive l'immagine originale

        # Aggiungi l'immagine (ora ridimensionata) e il commento ai contenuti del report
        self.contents.append(('commented_image', (comment, image_path)))



    def save_report(self, filename):
        c = canvas.Canvas(f"{self.report_path}/{filename}_{self.date}.pdf", pagesize=A4)
        width, height = A4

        # Riduci lo spazio in alto
        offset_top = 50  # Riduci questo valore per diminuire lo spazio in alto

        # Titolo
        c.setFont("Helvetica-Bold", 16)
        c.drawString(72, height - offset_top, self.title)

        # Contenuti
        c.setFont("Helvetica", 12)
        y = height - offset_top - 72  # Modifica anche qui per lo spazio in alto

        for content_type, content in self.contents:
            if y < 100:  # Assicurati di avere spazio per il contenuto
                c.showPage()
                y = height - offset_top - 72  # Aggiorna lo spazio in alto

            if content_type == 'text':
                c.drawString(72, y, content)
                y -= 18  # Decrementa y per la prossima linea
            elif content_type == 'commented_image':
                comment, image_path = content
                c.drawString(72, y, comment)
                y -= 18  # Decrementa y per il commento

                img = ImageReader(image_path)
                img_width, img_height = img.getSize()
                scale = (width - 144) / float(img_width)  # Scala per riempire la larghezza
                img_width = width - 144
                img_height *= scale

                c.drawImage(image_path, 72, y - img_height, width=img_width, height=img_height)
                y -= (img_height + 24)

        c.save()
# report = ReportGenerator()
# report.add_title('Analisi dei Dati 2023')
# report.add_content('Introduzione al report.')
# report.add_content('Osservazioni importanti.')
# report.add_commented_image('Commento sull\'immagine', image_path = "portfolio_management/Trading/testing/stock_analysis_chart.png")
# report.save_report('report')