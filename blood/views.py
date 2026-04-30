
        
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q, Sum
from django.core.mail import send_mail
from django.conf import settings
from django.http import JsonResponse
from .forms import *
from .models import *
from django.contrib.admin.views.decorators import staff_member_required
from .utils import send_status_email

# --- AUTH LOGIC ---
@login_required
def profile_management(request):
    if request.method == 'POST':
        form = DonorProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, '✅ Your profile has been updated successfully!')
            return redirect('profile')
    else:
        form = DonorProfileForm(instance=request.user)
    
    return render(request, 'blood/profile.html', {'form': form})

def custom_logout(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('login')

def register(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    # Determine the role from POST or default to donor
    role = request.POST.get('role', 'donor')
    
    if request.method == 'POST':
        if role == 'hospital':
            form = HospitalRegistrationForm(request.POST)
        else:
            form = DonorRegistrationForm(request.POST)
            
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Welcome {user.username}! Account created successfully.')
            return redirect('dashboard')
        else:
            # This will now show the specific field errors in the terminal or UI
            print(form.errors) 
            messages.error(request, 'Please correct the errors below.')
    else:
        form = DonorRegistrationForm()

    return render(request, 'blood/register.html', {
        'form': form,
        'role': role  # Pass the role back to the template
    })
# --- DASHBOARD LOGIC ---
from datetime import date as python_date

@login_required
def donor_dashboard(request):
    # Auto-complete passed appointments and increment count
    passed_requests = DonationRequest.objects.filter(
        donor=request.user,
        status='approved',
        date__lt=python_date.today()
    )

    if passed_requests.exists():
        for req in passed_requests:
            req.status = 'completed'
            req.save()
            request.user.donation_count += 1 # Ensure this field is in your User model
        request.user.save()
    urgent_appeal = EmergencyPost.objects.order_by('-created_at').first()
    context = {
        'urgent_appeal': urgent_appeal,
        'available_blood_banks': BloodBank.objects.all()[:3],
        'my_donations': DonationRequest.objects.filter(donor=request.user).order_by('-created_at'),
    }
    return render(request, 'blood/donor_dashboard.html', context)
@login_required
def dashboard(request):
    """One view to rule them all: Redirects based on role"""
    role = request.user.role
    
    # Inside views.py -> dashboard function
    if role == 'admin' or request.user.is_staff:
    # Calculate stats first
        total_inventory = BloodInventory.objects.aggregate(Sum('units_available'))['units_available__sum'] or 0
        pending_req_count = BloodRequest.objects.filter(status='pending').count()
        pending_don_count = DonationRequest.objects.filter(status='pending').count()

        context = {
        'total_donors': User.objects.filter(role='donor').count(),
        'total_hospitals': User.objects.filter(role='hospital').count(),
        'inventory': BloodInventory.objects.all(),
        'recent_requests': BloodRequest.objects.filter(status='pending')[:10],
        'pending_donations': DonationRequest.objects.filter(status='pending')[:10],
        # Create the 'stats' dictionary that the template is looking for
        'stats': {
            'total_inventory': total_inventory,
            'pending_requests': pending_req_count,
            'pending_donations': pending_don_count,
        }
    }
        return render(request, 'blood/admin_dashboard.html', context)
        
    elif role == 'donor':
        # Donor Context
        context = {
            'my_donations': DonationRequest.objects.filter(donor=request.user).order_by('-created_at'),
            'approved_donations': DonationRequest.objects.filter(donor=request.user, status='approved'),
            'available_blood_banks': BloodBank.objects.all()[:5]
        }
        return render(request, 'blood/donor_dashboard.html', context)
        
    elif role == 'hospital':
        # Use .all() or a very broad filter to ensure approved/rejected aren't hidden
        my_requests = BloodRequest.objects.filter(hospital=request.user).order_by('-created_at')
        
        # DEBUG PRINT: Check your terminal after refreshing the page
        print(f"DEBUG: Found {my_requests.count()} requests for user {request.user.username}")
        
        context = {
            'my_requests': my_requests,
            'blood_banks': BloodBank.objects.all()
        }
        return render(request, 'blood/hospital_dashboard.html', context)

# --- FUNCTIONAL VIEWS ---

@login_required
def search_donors(request):
    query = request.GET.get('q', '')
    blood_group = request.GET.get('blood_group', '')
    location = request.GET.get('location', '')
    
    donors = User.objects.filter(role='donor', is_available=True)
    if query: 
        donors = donors.filter(Q(username__icontains=query) | Q(location__icontains=query))
    if blood_group: 
        donors = donors.filter(blood_group=blood_group)
    if location: 
        donors = donors.filter(location__icontains=location)
    
    return render(request, 'blood/search_donors.html', {'donors': donors})

@login_required
def create_blood_request(request):
    if request.user.role != 'hospital':
        messages.error(request, "Only hospitals can request blood inventory.")
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = BloodRequestForm(request.POST)
        if form.is_valid():
            blood_request = form.save(commit=False)
            blood_request.hospital = request.user
            blood_request.save()
            messages.success(request, "✅ Blood request submitted successfully!")
            return redirect('dashboard')
    else:
        form = BloodRequestForm()
    return render(request, 'blood/create_blood_request.html', {'form': form})



@login_required
def admin_reject_donation(request, pk):
    """Rejects a donation request."""
    if not request.user.is_staff:
        return redirect('dashboard')
        
    donation = get_object_or_404(DonationRequest, pk=pk)
    donation.status = 'rejected'
    donation.save()
    
    messages.error(request, f'❌ Rejected donation for {donation.donor.username}')
    return redirect('dashboard')


# --- CONSOLIDATED ADMIN ACTIONS ---
def admin_approve_donation(request, pk):
    if not request.user.is_staff:
        return redirect('dashboard')
        
    donation = get_object_or_404(DonationRequest, pk=pk)
    donation.status = 'approved'
    donation.save()
    
    inv, _ = BloodInventory.objects.get_or_create(
        blood_bank=donation.blood_bank, 
        blood_group=donation.blood_group,
        defaults={'units_available': 0}
    )
    inv.units_available += donation.units
    inv.save()
    
    # EMAIL NOTIFICATION
    send_status_email(
        donation.donor.email,
        "Donation Approved! 🩸",
        f"Hi {donation.donor.username}, your donation at {donation.blood_bank.name} on {donation.date} is approved. See you there!"
    )
    
    messages.success(request, f'✅ Approved & Email sent to {donation.donor.username}')
    return redirect('dashboard')
@login_required
def approve_blood_request(request, pk):
    if not request.user.is_staff:
        return redirect('dashboard')
        
    blood_req = get_object_or_404(BloodRequest, pk=pk)
    inventory = BloodInventory.objects.filter(
        blood_bank=blood_req.blood_bank, 
        blood_group=blood_req.blood_group
    ).first()

    units = getattr(blood_req, 'units_needed', getattr(blood_req, 'units', 0))

    if inventory and inventory.units_available >= units:
        inventory.units_available -= units
        inventory.save()
        blood_req.status = 'approved'
        blood_req.save()
        
        # EMAIL NOTIFICATION
        send_status_email(
            blood_req.hospital.email,
            "Blood Request Approved! 🚚",
            f"Your request for {units} units of {blood_req.blood_group} has been approved and dispatched."
        )
        messages.success(request, "✅ Request approved and hospital notified.")
    else:
        messages.error(request, "❌ Insufficient inventory!")
    return redirect('dashboard')
@login_required
def create_donation_request(request):
    if request.user.role != 'donor':
        messages.error(request, "Only donors can schedule appointments.")
        return redirect('dashboard')
        
    if request.method == 'POST':
        # 1. Try to get data from the Form first
        form = DonationRequestForm(request.POST)
        if form.is_valid():
            donation = form.save(commit=False)
            donation.donor = request.user
            donation.status = 'pending'
            donation.save()
            messages.success(request, '✅ Appointment scheduled! Awaiting admin approval.')
            return redirect('dashboard')
        else:
            # 2. Fallback if the Form failed but data was sent manually
            blood_bank_id = request.POST.get('blood_bank')
            donation_date = request.POST.get('date')
            
            if blood_bank_id and donation_date:
                DonationRequest.objects.create(
                    donor=request.user,
                    blood_bank_id=blood_bank_id,
                    date=donation_date,
                    status='pending'
                )
                messages.success(request, '✅ Appointment scheduled successfully!')
                return redirect('dashboard')
            else:
                messages.error(request, "Please select a blood bank and a valid date.")
    
    # 3. Handle GET request
    banks = BloodBank.objects.all()
    form = DonationRequestForm()
    return render(request, 'blood/create_donation.html', {
        'form': form,
        'banks': banks
    })
def home(request):
    return render(request, 'blood/home.html')
    
@login_required
def reject_blood_request(request, pk):
    if not request.user.is_staff and request.user.role != 'admin':
        return redirect('dashboard')
        
    blood_req = get_object_or_404(BloodRequest, pk=pk)
    blood_req.status = 'rejected'
    blood_req.save()
    messages.info(request, "Blood request has been rejected.")
    return redirect('dashboard')


@login_required
def emergency_feed(request):
    # Just show the posts
    posts = EmergencyPost.objects.all().order_by('-created_at')
    return render(request, 'blood/emergency_feed.html', {'posts': posts})

@login_required
def create_emergency_post(request):
    if request.method == 'POST':
        # Get data manually or via form
        form = EmergencyPostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            messages.success(request, "Emergency broadcast sent!")
            return redirect('emergency_feed')
    else:
        form = EmergencyPostForm()
    
    return render(request, 'blood/create_emergency_post.html', {'form': form})


@login_required
def add_comment(request, post_id):
    if request.method == 'POST':
        post = get_object_or_404(EmergencyPost, id=post_id)
        content = request.POST.get('content')
        if content:
            PostComment.objects.create(post=post, author=request.user, content=content)
    return redirect('emergency_feed')

@login_required
def mark_managed(request, post_id):
    post = get_object_or_404(EmergencyPost, id=post_id, author=request.user)
    post.is_managed = True
    post.save()
    return redirect('emergency_feed')


@login_required
def request_history(request):
    if request.user.role != 'hospital':
        return redirect('dashboard')
        
    # Get all requests (pending, approved, rejected) for this hospital
    all_requests = BloodRequest.objects.filter(hospital=request.user).order_by('-created_at')
    
    return render(request, 'blood/request_history.html', {'requests': all_requests})

@staff_member_required # Or your custom admin check
def admin_donation_history(request):
    donations = DonationRequest.objects.all().order_by('-created_at')
    return render(request, 'blood/admin_donation_history.html', {'donations': donations})

@staff_member_required
def admin_blood_request_history(request):
    requests = BloodRequest.objects.all().order_by('-created_at')
    return render(request, 'blood/admin_request_history.html', {'requests': requests})

import io
from django.http import FileResponse
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet

@staff_member_required
def generate_report_pdf(request):
    # Create a file-like buffer to receive PDF data.
    buffer = io.BytesIO()

    # Create the PDF object, using the buffer as its "file."
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()

    # Title
    elements.append(Paragraph("Blood Bank System - Status Report", styles['Title']))
    elements.append(Paragraph(f"Generated on: {python_date.today()}", styles['Normal']))
    elements.append(Paragraph("<br/><br/>", styles['Normal']))

    # --- Section 1: Inventory ---
    elements.append(Paragraph("Current Inventory Levels", styles['Heading2']))
    inventory_data = [['Bank', 'Blood Group', 'Units Available']]
    for item in BloodInventory.objects.all():
        inventory_data.append([item.blood_bank.name, item.blood_group, item.units_available])

    t1 = Table(inventory_data)
    t1.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.red),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    elements.append(t1)
    elements.append(Paragraph("<br/><br/>", styles['Normal']))

    # --- Section 2: Recent Approved Requests ---
    elements.append(Paragraph("Approved Requests (Distribution)", styles['Heading2']))
    request_data = [['Hospital', 'Group', 'Units', 'Date']]
    recent_reqs = BloodRequest.objects.filter(status='approved').order_by('-created_at')[:20]
    
    for r in recent_reqs:
        request_data.append([r.hospital.username, r.blood_group, r.units_needed, r.created_at.strftime('%Y-%m-%d')])

    t2 = Table(request_data)
    t2.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    elements.append(t2)

    # Build PDF
    doc.build(elements)

    # FileResponse sets the Content-Disposition header so the browser downloads it.
    buffer.seek(0)
    return FileResponse(buffer, as_attachment=True, filename=f'blood_report_{python_date.today()}.pdf')