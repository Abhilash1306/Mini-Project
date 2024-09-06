from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.contrib.auth.models import User
from .forms import RegisterForm, BusPassForm, PaymentForm
from .models import BusPass, Payment
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponse
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
import qrcode
import datetime
from datetime import timedelta, datetime
import os
import tempfile
import pandas as pd
from django.db.models import Q
import pdfkit
from django.template.loader import render_to_string
import csv
from io import BytesIO

def home(request):
    return render(request, 'buspass/home.html')

def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Registration successful. Please log in.')
            return redirect('login')
    else:
        form = RegisterForm()
    return render(request, 'buspass/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            if user.is_staff:
                return redirect('auth_dashboard')
            else:
                return redirect('user_dashboard')
        else:
            messages.error(request, 'Invalid username or password.')

    return render(request, 'buspass/login.html')

@login_required
def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out.')
    return redirect('home')

@login_required
def user_dashboard(request):
    user = request.user
    try:
        bus_pass = BusPass.objects.get(user=user)
        if bus_pass.status == 'Accepted':
            can_download = True
        else:
            can_download = False
    except BusPass.DoesNotExist:
        bus_pass = None
        can_download = False
    return render(request, 'buspass/user_dashboard.html', {'bus_pass': bus_pass, 'can_download': can_download, 'user': user})

@login_required
def apply_pass_instruction(request):
    user = request.user
    if BusPass.objects.filter(user=user).exists():
        return redirect('view_user_pass')
    if request.method == 'POST':
        return redirect('apply_pass_form')
    return render(request, 'buspass/apply_pass_instruction.html')

@login_required
def apply_pass_form(request):
    user = request.user
    if BusPass.objects.filter(user=user).exists():
        return redirect('view_user_pass')

    if request.method == 'POST':
        form = BusPassForm(request.POST, request.FILES)
        if form.is_valid():
            bus_pass = form.save(commit=False)
            bus_pass.user = user
            bus_pass.save()
            return redirect('payment')
    else:
        form = BusPassForm()
    return render(request, 'buspass/apply_pass_form.html', {'form': form})

@login_required
def payment_view(request):
    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.user = request.user
            payment.save()
            return redirect('user_dashboard')
    else:
        form = PaymentForm()
    return render(request, 'buspass/payment.html', {'form': form})

@login_required
def view_user_pass(request):
    user = request.user
    passes = BusPass.objects.filter(user=user)
    return render(request, 'buspass/view_user_pass.html', {'passes': passes})

@login_required
def download_pass(request):
    user = request.user
    try:
        bus_pass = BusPass.objects.get(user=user, status='Accepted')
    except BusPass.DoesNotExist:
        messages.error(request, 'No valid bus pass found.')
        return redirect('user_dashboard')

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="bus_pass.pdf"'

    width, height = 85.60 * mm, 53.98 * mm
    p = canvas.Canvas(response, pagesize=(width, height))

    # QR Code generation
    qr_data = f"Name: {user.username}\nFrom: {bus_pass.from_place}\nTo: {bus_pass.to_place}\nStatus: Accepted"
    qr = qrcode.QRCode(box_size=2)
    qr.add_data(qr_data)
    qr.make(fit=True)
    img = qr.make_image(fill='black', back_color='white')

    # Save the QR code image to a temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_file:
        img.save(tmp_file, format="PNG")
        tmp_file_path = tmp_file.name

    # Draw the QR code image on the PDF at the right bottom of the card
    p.drawImage(tmp_file_path, width - 40 * mm, 10, 30 * mm, 30 * mm)

    # Calculate the validity date
    validity_date = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')

    # Draw additional text on the PDF
    p.drawString(10, height - 40, f"Name: {user.username}")
    p.drawString(10, height - 60, f"From: {bus_pass.from_place}")
    p.drawString(10, height - 80, f"To: {bus_pass.to_place}")
    p.drawString(10, height - 100, f"Status: Accepted")
    p.drawString(10, height - 120, f"Valid Until: {validity_date}")

    p.showPage()
    p.save()

    # Clean up the temporary file
    os.remove(tmp_file_path)

    return response

@staff_member_required
def auth_dashboard(request):
    query = request.GET.get('q')
    order = request.GET.get('order', 'user')
    pending_passes = BusPass.objects.filter(status='Pending')
    viewed_passes = BusPass.objects.filter(status__in=['Accepted', 'Rejected'])

    if query:
        pending_passes = pending_passes.filter( 
            Q(user__first_name__icontains=query) |
            Q(user__last_name__icontains=query)
        )
        viewed_passes = viewed_passes.filter( 
            Q(user__first_name__icontains=query) |
            Q(user__last_name__icontains=query)
        )

    pending_passes = pending_passes.order_by(order)
    viewed_passes = viewed_passes.order_by(order)

    return render(request, 'buspass/auth_dashboard.html', {
        'pending_passes': pending_passes,
        'viewed_passes': viewed_passes,
        'query': query,
        'order': order,
    })

@staff_member_required
def update_pass_status(request, pass_id, status):
    try:
        bus_pass = BusPass.objects.get(id=pass_id)
        bus_pass.status = status
        bus_pass.save()
        messages.success(request, 'Status updated successfully.')
    except BusPass.DoesNotExist:
        messages.error(request, 'Bus pass not found.')
    return redirect('auth_dashboard')

@staff_member_required
def view_all_passes(request):
    passes = BusPass.objects.all()
    return render(request, 'buspass/view_all_passes.html', {'passes': passes})

@staff_member_required
def export_passes(request):
    bus_passes = BusPass.objects.all().values('user__username', 'user__first_name', 'user__last_name', 'status', 'created_at')
    df = pd.DataFrame(bus_passes)
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=bus_passes.xlsx'
    df.to_excel(response, index=False)
    return response

def generate_pdf_pass(request, pass_id):
    bus_pass = BusPass.objects.get(id=pass_id)
    html = render_to_string('bus_pass_pdf_template.html', {'bus_pass': bus_pass})
    pdf = pdfkit.from_string(html, False)
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="bus_pass_{bus_pass.pass_id}.pdf"'
    return response

from io import BytesIO
from django.http import HttpResponse
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
import csv

def export_pass_data(request, format):
    bus_passes = BusPass.objects.all()
    if format == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="bus_passes.csv"'

        writer = csv.writer(response)
        writer.writerow(['Pass ID', 'Full Name', 'From Place', 'To Place', 'College Name', 'Status'])

        for bus_pass in bus_passes:
            writer.writerow([bus_pass.pass_id, bus_pass.full_name, bus_pass.from_place, bus_pass.to_place, bus_pass.college, bus_pass.status])

        return response
    elif format == 'pdf':
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="bus_passes.pdf"'

        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = []

        styles = getSampleStyleSheet()
        style = styles['Normal']
        
        data = [
            ['Pass ID', 'Full Name', 'From Place', 'To Place', 'College Name', 'Status']
        ]
        
        for bus_pass in bus_passes:
            data.append([
                str(bus_pass.pass_id),
                Paragraph(bus_pass.full_name, style),
                bus_pass.from_place,
                bus_pass.to_place,
                bus_pass.college,
                bus_pass.status
            ])
        
        table = Table(data, colWidths=[50, 150, 100, 100, 100, 100])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), '#d0d0d0'),
            ('TEXTCOLOR', (0, 0), (-1, 0), (0, 0, 0)),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), '#f0f0f0'),
            ('GRID', (0, 0), (-1, -1), 1, (0, 0, 0)),
        ]))
        
        elements.append(table)
        doc.build(elements)

        buffer.seek(0)
        response.write(buffer.getvalue())
        buffer.close()

        return response
    else:
        return HttpResponse("Invalid format", status=400)
