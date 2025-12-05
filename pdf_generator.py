"""
Modulo per la generazione di PDF dei biglietti
"""

def debug_image_paths(image_path):
    """Debug function per controllare i percorsi delle immagini"""
    import os
    print(f"=== DEBUG PERCORSO IMMAGINE ===")
    print(f"Path richiesto: {image_path}")
    print(f"Working directory: {os.getcwd()}")
    print(f"Script directory: {os.path.dirname(__file__)}")
    
    possible_paths = [
        os.path.join(os.path.dirname(__file__), image_path.lstrip('/')),
        os.path.join(os.getcwd(), image_path.lstrip('/')),
        image_path.lstrip('/'),
        os.path.join('static', image_path.lstrip('/static/'))
    ]
    
    for i, path in enumerate(possible_paths):
        exists = os.path.exists(path)
        print(f"Percorso {i+1}: {path} - {'ESISTE' if exists else 'NON ESISTE'}")
    print("==============================")
    return possible_paths

from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import cm, inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
import os
import io
import requests
from datetime import datetime
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import cm, inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from urllib.parse import urlparse

def generate_email_ticket_pdf(booking, event):
    """
    Genera un PDF del biglietto ottimizzato per email con logo e poster
    
    Args:
        booking: Dict con i dati della prenotazione
        event: Dict con i dati dell'evento
    
    Returns:
        bytes: Contenuto del PDF generato
    """
    
    buffer = io.BytesIO()
    
    # Crea documento PDF in formato biglietto elegante
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=0.4*inch,
        leftMargin=0.4*inch,
        topMargin=0.4*inch,
        bottomMargin=0.4*inch
    )
    
    # Stili
    styles = getSampleStyleSheet()
    
    # Stili eleganti per biglietto teatrale - senza cornici
    title_style = ParagraphStyle(
        'TicketTitle',
        parent=styles['Title'],
        fontSize=28,
        textColor=colors.HexColor('#2B4C8C'),  # Blu elegante
        alignment=TA_CENTER,
        spaceAfter=15,
        fontName='Helvetica-Bold',
        backColor=colors.HexColor('#F8F9FA'),  # Grigio molto chiaro
        borderWidth=0,  # Nessuna cornice
        borderPadding=10
    )
    
    # Stile per l'evento elegante - senza cornice
    event_style = ParagraphStyle(
        'EventTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#8B0000'),  # Rosso scuro teatrale
        alignment=TA_CENTER,
        spaceAfter=18,
        fontName='Helvetica-Bold',
        backColor=colors.HexColor('#F0F0F0'),  # Grigio chiaro
        borderWidth=0,  # Nessuna cornice
        borderPadding=12
    )
    
    # Stile per dettagli eleganti - più grandi e senza cornici
    detail_style = ParagraphStyle(
        'TicketDetails',
        parent=styles['Normal'],
        fontSize=16,  # Aumentato da 12 a 16
        textColor=colors.HexColor('#2d3748'),
        alignment=TA_CENTER,
        spaceAfter=12,
        fontName='Helvetica-Bold',
        backColor=colors.HexColor('#FFFFFF'),  # Bianco pulito
        borderWidth=0,  # Nessuna cornice
        borderPadding=10
    )
    
    # Lista elementi del documento
    story = []
    
    # Header con logo se esiste
    try:
        import os
        # Prova diversi percorsi possibili per il logo
        base_dir = os.environ.get('APP_BASE_DIR', os.path.dirname(__file__))
        logo_paths = [
            os.path.join(base_dir, 'static', 'img', 'logo.png'),
            os.path.join(os.path.dirname(__file__), 'static', 'img', 'logo.png'),
            os.path.join(os.getcwd(), 'static', 'img', 'logo.png'),
            'static/img/logo.png',
            './static/img/logo.png'
        ]
        
        logo_loaded = False
        for logo_path in logo_paths:
            if os.path.exists(logo_path):
                logo = Image(logo_path, width=1.2*inch, height=1.2*inch)
                logo.hAlign = 'CENTER'
                story.append(logo)
                story.append(Spacer(1, 0.1*inch))
                logo_loaded = True
                break
        
        if not logo_loaded:
            # Fallback: aggiungi spazio per il logo mancante
            print("Warning: Logo non trovato in nessun percorso")
            story.append(Spacer(1, 0.3*inch))
            
    except Exception as e:
        # Log dell'errore ma continua
        print(f"Errore caricamento logo: {e}")
        story.append(Spacer(1, 0.3*inch))
    
    # Titolo principale del teatro
    story.append(Paragraph("🎭 BIGLIETTO D'INGRESSO 🎭", title_style))
    story.append(Spacer(1, 0.15*inch))
    
    # Titolo evento in evidenza con bordo dorato
    story.append(Paragraph(f"<b>🎪 {event['title']} 🎪</b>", event_style))
    story.append(Spacer(1, 0.15*inch))
    
    # Poster dell'evento (più piccolo ma elegante)
    if event['poster_url']:
        try:
            poster_added = False
            if event['poster_url'].startswith('http'):
                # URL esterno
                import requests
                response = requests.get(event['poster_url'], timeout=10, headers={
                    'User-Agent': 'Mozilla/5.0 (compatible; TSR-PDF-Generator/1.0)'
                })
                if response.status_code == 200:
                    img_buffer = io.BytesIO(response.content)
                    poster = Image(img_buffer, width=1.8*inch, height=2.2*inch)
                    poster.hAlign = 'CENTER'
                    story.append(poster)
                    story.append(Spacer(1, 0.1*inch))
                    poster_added = True
            else:
                # File locale - prova diversi percorsi
                base_dir = os.environ.get('APP_BASE_DIR', os.path.dirname(__file__))
                poster_paths = [
                    os.path.join(base_dir, event['poster_url'].lstrip('/')),
                    os.path.join(os.path.dirname(__file__), event['poster_url'].lstrip('/')),
                    os.path.join(os.getcwd(), event['poster_url'].lstrip('/')),
                    event['poster_url'].lstrip('/'),
                    os.path.join('static', event['poster_url'].lstrip('/static/'))
                ]
                
                for poster_path in poster_paths:
                    if os.path.exists(poster_path):
                        poster = Image(poster_path, width=1.8*inch, height=2.2*inch)
                        poster.hAlign = 'CENTER'
                        story.append(poster)
                        story.append(Spacer(1, 0.1*inch))
                        poster_added = True
                        break
                        
            if not poster_added:
                # Fallback: placeholder testuale pulito
                placeholder_style = ParagraphStyle(
                    'PlaceholderStyle',
                    parent=styles['Normal'],
                    fontSize=16,
                    textColor=colors.HexColor('#2B4C8C'),
                    alignment=TA_CENTER,
                    backColor=colors.HexColor('#F8F9FA'),
                    borderWidth=0,  # Nessuna cornice
                    borderPadding=25
                )
                story.append(Paragraph("🎭<br/>POSTER<br/>NON DISPONIBILE", placeholder_style))
                story.append(Spacer(1, 0.1*inch))
                
        except Exception as e:
            print(f"Errore caricamento poster: {e}")
            # Aggiungi placeholder pulito in caso di errore
            placeholder_style = ParagraphStyle(
                'PlaceholderStyle',
                parent=styles['Normal'],
                fontSize=16,
                textColor=colors.HexColor('#8B0000'),
                alignment=TA_CENTER,
                backColor=colors.HexColor('#F8F9FA'),
                borderWidth=0,  # Nessuna cornice
                borderPadding=25
            )
            story.append(Paragraph("🎭<br/>ERRORE CARICAMENTO<br/>POSTER", placeholder_style))
            story.append(Spacer(1, 0.1*inch))
    
    # Tabella con dettagli biglietto
    seats_count = len(booking['seats'].split(','))
    total_price = event['price'] * seats_count
    
    # Dati per la tabella - layout migliorato
    data = [
        ['👤 Intestatario', booking['name']],
        ['📧 Contatto', booking['email']],
        ['📅 Data Spettacolo', event['date']],
        ['⏰ Orario', event['time']],
        ['🎫 Posti Riservati', booking['seats']],
        ['💰 Totale Pagato', f"€ {total_price:.2f}"],
        ['🎟️ Codice Biglietto', f"#{booking['id']:05d}"]
    ]
    
    # Crea tabella pulita senza cornici
    table = Table(data, colWidths=[2.5*inch, 3.5*inch])
    table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 14),  # Aumentato da 11 a 14
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),  # Prima colonna
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica-Bold'),  # Anche i valori in bold
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#2B4C8C')),  # Blu elegante
        ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#8B0000')),  # Rosso teatrale
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        # Nessuna griglia/cornice
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#F8F9FA')),  # Grigio chiaro per etichette
        ('BACKGROUND', (1, 0), (1, -1), colors.HexColor('#FFFFFF')),  # Bianco per valori
        ('ROWBACKGROUNDS', (1, 0), (1, -1), [colors.HexColor('#FFFFFF'), colors.HexColor('#F0F0F0')]),
        ('PADDING', (0, 0), (-1, -1), 12),  # Aumentato padding
        ('LINEBELOW', (0, 0), (-1, -2), 1, colors.HexColor('#E0E0E0')),  # Solo linee sottili tra righe
    ]))
    
    story.append(table)
    story.append(Spacer(1, 0.2*inch))
    
    # Box istruzioni pulito - senza cornici
    important_style = ParagraphStyle(
        'ImportantBox',
        parent=styles['Normal'],
        fontSize=14,  # Più grande
        textColor=colors.HexColor('#8B0000'),
        alignment=TA_CENTER,
        fontName='Helvetica-Bold',
        backColor=colors.HexColor('#F8F9FA'),  # Grigio chiaro
        borderWidth=0,  # Nessuna cornice
        borderPadding=12
    )
    
    story.append(Paragraph("⚠️ ISTRUZIONI IMPORTANTI ⚠️<br/>Presentare questo biglietto all'ingresso • Arrivare 20 minuti prima", important_style))
    story.append(Spacer(1, 0.15*inch))
    
    # Footer elegante - senza giallo
    footer_style = ParagraphStyle(
        'FooterElegant',
        parent=styles['Normal'],
        fontSize=11,  # Più grande
        textColor=colors.HexColor('#2B4C8C'),
        alignment=TA_CENTER,
        fontName='Helvetica-Oblique',
        backColor=colors.HexColor('#F8F9FA'),  # Grigio chiaro
        borderColor=colors.HexColor('#2B4C8C'),
        borderWidth=1,
        borderPadding=8
    )
    
    story.append(Paragraph("🏛️ TEATRO SAN RAFFAELE 🏛️<br/>📧 info@teatrosanraffaele.it", footer_style))
    story.append(Spacer(1, 0.05*inch))
    story.append(Paragraph(f"Biglietto generato il {datetime.now().strftime('%d/%m/%Y alle %H:%M')}", 
                          ParagraphStyle('FooterDate', parent=styles['Normal'], fontSize=8, 
                                       textColor=colors.HexColor('#718096'), alignment=TA_CENTER)))
    
    # Genera il PDF
    doc.build(story)
    
    buffer.seek(0)
    return buffer.getvalue()

#PEPPE
def generate_tickets_summary_pdf(bookings, event):
    """
    Genera un PDF riassuntivo con tutti i biglietti di un evento
    
    Args:
        bookings: Lista di prenotazioni
        event: Dict con i dati dell'evento
    
    Returns:
        BytesIO: Buffer contenente il PDF generato
    """
    
    buffer = io.BytesIO()
    
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=0.5*inch,
        leftMargin=0.5*inch,
        topMargin=0.5*inch,
        bottomMargin=0.5*inch
    )
    
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Title'],
        fontSize=20,
        textColor=colors.HexColor('#2d3748'),
        alignment=TA_CENTER,
        spaceAfter=20,
        fontName='Helvetica-Bold'
    )
    
    story = []
    
    # Header
    story.append(Paragraph("🎭 TEATRO SAN RAFFAELE", title_style))
    story.append(Paragraph(f"<b>Riepilogo Prenotazioni - {event['title']}</b>", title_style))
    story.append(Paragraph(f"Data: {event['date']} - Ore: {event['time']}", styles['Normal']))
    story.append(Spacer(1, 0.3*inch))
    
    # Tabella riassuntiva
    headers = ['ID', 'Nome', 'Email', 'Posti', 'Stato', 'Totale €']
    data = [headers]
    
    total_revenue = 0
    total_tickets = 0
    
    for booking in bookings:
        seats_count = len(booking['seats'].split(','))
        booking_total = event['price'] * seats_count
        total_revenue += booking_total
        total_tickets += seats_count
        
        status_map = {
            1: 'Pending',
            2: 'Pagato',
            3: 'Cassa'
        }
        
        data.append([
            str(booking['id']),
            booking['name'],
            booking['email'],
            booking['seats'],
            status_map.get(booking['status'], 'Sconosciuto'),
            f"€ {booking_total:.2f}"
        ])
    
    # Riga totale
    data.append(['', '', '', f'Tot. {total_tickets} posti', '', f'€ {total_revenue:.2f}'])
    
    table = Table(data)
    table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),  # Header
        ('FONTNAME', (0, 1), (-1, -2), 'Helvetica'),     # Dati
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'), # Totale
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2d3748')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#f7fafc')),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e2e8f0')),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    
    story.append(table)
    
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()


def generate_event_summary_pdf(event, transactions):
    """Genera un PDF di riepilogo con tutti i biglietti per un evento"""
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.lib import colors
    from datetime import datetime
    import io
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=2*cm, bottomMargin=2*cm)
    
    # Stili
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=30,
        alignment=1,  # Centrato
        textColor=colors.HexColor('#2d3748')
    )
    
    header_style = ParagraphStyle(
        'CustomHeader',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=20,
        textColor=colors.HexColor('#744210')
    )
    
    # Contenuto del documento
    story = []
    
    # Titolo
    story.append(Paragraph(f"RIEPILOGO BIGLIETTI - {event['title'].upper()}", title_style))
    story.append(Spacer(1, 0.5*cm))
    
    # Informazioni evento
    event_info = [
        ['Data:', event['date']],
        ['Orario:', event['time']],
        ['Prezzo:', f"€ {event['price']:.2f}"],
        ['Data stampa:', datetime.now().strftime('%d/%m/%Y %H:%M')]
    ]
    
    event_table = Table(event_info, colWidths=[4*cm, 8*cm])
    event_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8fafc')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#2d3748')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    
    story.append(event_table)
    story.append(Spacer(1, 1*cm))
    
    # Statistiche generali
    total_tickets = 0
    total_amount = 0
    status_counts = {'In attesa': 0, 'Pagato': 0, 'Prenotato': 0}
    
    for t in transactions:
        seats_count = len(t['seats'].split(',')) if t['seats'] else 0
        total_tickets += seats_count
        total_amount += seats_count * event['price']
        
        if t['status'] == 1:
            status_counts['In attesa'] += 1
        elif t['status'] == 2:
            status_counts['Pagato'] += 1
        elif t['status'] == 3:
            status_counts['Prenotato'] += 1
    
    story.append(Paragraph("STATISTICHE GENERALI", header_style))
    
    stats_data = [
        ['Totale transazioni:', str(len(transactions))],
        ['Totale biglietti:', str(total_tickets)],
        ['Importo totale:', f"€ {total_amount:.2f}"],
        ['Transazioni pagate:', str(status_counts['Pagato'])],
        ['Transazioni prenotate:', str(status_counts['Prenotato'])],
        ['Transazioni in attesa:', str(status_counts['In attesa'])]
    ]
    
    stats_table = Table(stats_data, colWidths=[5*cm, 4*cm])
    stats_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f0fff4')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#2d3748')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#38a169')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    
    story.append(stats_table)
    story.append(Spacer(1, 1*cm))
    
    # Elenco dettagliato transazioni
    story.append(Paragraph("ELENCO DETTAGLIATO TRANSAZIONI", header_style))
    
    # Intestazione tabella
    table_data = [['ID', 'Nome', 'Email', 'Stato', 'N° Posti', 'Posti Assegnati', 'Importo']]
    
    for t in transactions:
        seats_count = len(t['seats'].split(',')) if t['seats'] else 0
        amount = seats_count * event['price']
        
        # Stato descrittivo
        status_text = {
            1: 'In attesa',
            2: 'Pagato', 
            3: 'Prenotato'
        }.get(t['status'], 'Sconosciuto')
        
        # Formatta posti (max 50 caratteri per riga)
        seats_text = t['seats'] if t['seats'] else 'Nessuno'
        if len(seats_text) > 50:
            seats_text = seats_text[:47] + '...'
        
        table_data.append([
            str(t['id']),
            t['name'][:20] + '...' if len(t['name']) > 20 else t['name'],
            t['email'][:25] + '...' if len(t['email']) > 25 else t['email'],
            status_text,
            str(seats_count),
            seats_text,
            f"€ {amount:.2f}"
        ])
    
    # Crea tabella transazioni
    transactions_table = Table(table_data, colWidths=[1*cm, 3*cm, 4*cm, 2*cm, 1.5*cm, 4*cm, 1.5*cm])
    transactions_table.setStyle(TableStyle([
        # Intestazione
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2d3748')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        
        # Righe dati
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor('#2d3748')),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        
        # Bordi e allineamento
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        
        # Allineamento colonne specifiche
        ('ALIGN', (1, 1), (2, -1), 'LEFT'),  # Nome, Email a sinistra
        ('ALIGN', (5, 1), (5, -1), 'LEFT'),  # Posti a sinistra
    ]))
    
    story.append(transactions_table)
    
    # Genera il PDF
    doc.build(story)
    
    return buffer.getvalue()

def generate_individual_tickets_pdf(bookings, event):
    """
    Genera un PDF con biglietti individuali per ogni transazione.
    Massimo 3 biglietti per foglio A4 per permettere il taglio e la consegna ai clienti.
    
    Args:
        bookings: Lista di prenotazioni
        event: Dict con i dati dell'evento
    
    Returns:
        bytes: Contenuto del PDF generato
    """
    
    buffer = io.BytesIO()
    
    # Documento A4 con margini ridotti per massimizzare lo spazio
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=0.3*inch,
        leftMargin=0.3*inch,
        topMargin=0.3*inch,
        bottomMargin=0.3*inch
    )
    
    styles = getSampleStyleSheet()
    
    # Stili ottimizzati per biglietti piccoli
    ticket_title_style = ParagraphStyle(
        'TicketTitleSmall',
        parent=styles['Title'],
        fontSize=16,
        textColor=colors.HexColor('#2B4C8C'),
        alignment=TA_CENTER,
        spaceAfter=8,
        fontName='Helvetica-Bold',
        backColor=colors.HexColor('#F8F9FA'),
        borderWidth=1,
        borderColor=colors.HexColor('#2B4C8C'),
        borderPadding=6
    )
    
    event_title_style = ParagraphStyle(
        'EventTitleSmall',
        parent=styles['Normal'],
        fontSize=14,
        textColor=colors.HexColor('#8B0000'),
        alignment=TA_CENTER,
        spaceAfter=6,
        fontName='Helvetica-Bold'
    )
    
    detail_style = ParagraphStyle(
        'DetailSmall',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#2d3748'),
        alignment=TA_LEFT,
        fontName='Helvetica'
    )
    
    code_style = ParagraphStyle(
        'CodeStyle',
        parent=styles['Normal'],
        fontSize=12,
        textColor=colors.HexColor('#8B0000'),
        alignment=TA_CENTER,
        fontName='Helvetica-Bold',
        backColor=colors.HexColor('#F0F0F0'),
        borderWidth=1,
        borderColor=colors.HexColor('#8B0000'),
        borderPadding=4
    )
    
    story = []
    
    # Genera biglietti per ogni prenotazione
    tickets_per_page = 0
    
    for i, booking in enumerate(bookings):
        # Calcola prezzo totale per questa prenotazione
        seats_count = len(booking['seats'].split(','))
        total_price = event['price'] * seats_count
        
        # Contenuto del singolo biglietto
        ticket_elements = []
        
        # Header biglietto
        ticket_elements.append(Paragraph("🎭 TEATRO SAN RAFFAELE 🎭", ticket_title_style))
        ticket_elements.append(Spacer(1, 6))
        ticket_elements.append(Paragraph(f"<b>{event['title']}</b>", event_title_style))
        ticket_elements.append(Spacer(1, 8))
        
        # Informazioni essenziali in tabella compatta
        ticket_data = [
            ['👤 Nome:', booking['name'][:25] + '...' if len(booking['name']) > 25 else booking['name']],
            ['📅 Data:', event['date']],
            ['⏰ Orario:', event['time']],
            ['🎫 Posti:', booking['seats']],
            ['💰 Totale:', f"€ {total_price:.2f}"],
        ]
        
        ticket_table = Table(ticket_data, colWidths=[1.2*inch, 2.8*inch])
        ticket_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#2B4C8C')),
            ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#2d3748')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('PADDING', (0, 0), (-1, -1), 4),
            ('LINEBELOW', (0, 0), (-1, -2), 0.5, colors.HexColor('#E0E0E0')),
        ]))
        
        ticket_elements.append(ticket_table)
        ticket_elements.append(Spacer(1, 8))
        
        # Codice biglietto prominente
        ticket_elements.append(Paragraph(f"Codice: #{booking['id']:05d}", code_style))
        ticket_elements.append(Spacer(1, 6))
        
        # Note per il controllo
        note_style = ParagraphStyle(
            'NoteStyle',
            parent=styles['Normal'],
            fontSize=8,
            textColor=colors.HexColor('#666666'),
            alignment=TA_CENTER,
            fontName='Helvetica-Oblique'
        )
        ticket_elements.append(Paragraph("Presentare all'ingresso • Arrivare 20 min prima", note_style))
        
        # Crea un frame per ogni biglietto con bordo
        from reportlab.platypus import KeepTogether
        ticket_frame = KeepTogether(ticket_elements)
        
        # Aggiungi il biglietto alla storia
        story.append(ticket_frame)
        
        tickets_per_page += 1
        
        # Aggiungi spazio tra i biglietti o nuova pagina
        if tickets_per_page < 3 and i < len(bookings) - 1:
            # Spazio tra biglietti sulla stessa pagina
            story.append(Spacer(1, 0.8*inch))
        elif tickets_per_page == 3 and i < len(bookings) - 1:
            # Nuova pagina dopo 3 biglietti
            from reportlab.platypus import PageBreak
            story.append(PageBreak())
            tickets_per_page = 0
    
    # Genera il PDF
    doc.build(story)
    
    buffer.seek(0)
    return buffer.getvalue()