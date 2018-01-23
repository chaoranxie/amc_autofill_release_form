import csv
import io
import re
import pdfrw
from reportlab.pdfgen import canvas
import sys
import os

def get_emergency_contact(contact):
    contact = contact.replace('\n', ' ')
    if len(contact) >= 35:
        contact = re.sub('[()-]', '', contact)

    return contact

def get_overlay_canvas(participants):
    data = io.BytesIO()
    pdf = canvas.Canvas(data)
    for idx, participant in enumerate(participants):
        y = y_start - y_increment * idx
        emergency_contact = get_emergency_contact(participant['EMERGENCY CONTACT'])
        pdf.drawString(x=participant_name_x, y=y, text=participant['NAME'])
        pdf.drawString(x=emergency_contact_x, y=y,
                       text=emergency_contact)
    pdf.save()
    data.seek(0)
    return data


def merge(overlay_canvas, template_path):
    template_pdf = pdfrw.PdfReader(template_path)
    overlay_pdf = pdfrw.PdfReader(overlay_canvas)
    for page, data in zip(template_pdf.pages, overlay_pdf.pages):
        overlay = pdfrw.PageMerge().add(data)[0]
        pdfrw.PageMerge(page).add(overlay).render()
    form = io.BytesIO()
    pdfrw.PdfWriter().write(form, template_pdf)
    form.seek(0)
    return form


def save(form, filename):
    with open(filename, 'wb') as f:
        f.write(form.read())


participant_name_x = 65
emergency_contact_x = 400
y_start = 215
y_increment = 17
chunk_size = 10

release_pdf = 'release.pdf'
filled_release_base = 'release_filled_'
csv_file = '1668.csv'

release_pdf = sys.argv[1]
csv_file = sys.argv[2]
filled_release_base = os.path.splitext(release_pdf)[0] + '_filled_'


def get_approved_participants(csv_file):
    with open(csv_file) as csvfile:
        reader = csv.DictReader(csvfile)
        participants = list(reader)

    approved_participants = [
        participant for participant in participants if participant['REGISTER STATUS'] == 'APPROVED']
    return approved_participants


def generate_pdfs(approved_participants, chunk_size):
    for i in range(0, len(approved_participants), chunk_size):
        chunk_index = i / chunk_size + 1
        filled_release_pdf = filled_release_base + str(chunk_index) + ".pdf"
        participants = approved_participants[i:i + chunk_size]
        canvas_data = get_overlay_canvas(participants)
        form = merge(canvas_data, template_path=release_pdf)
        save(form, filename=filled_release_pdf)


generate_pdfs(get_approved_participants(csv_file), chunk_size)
