from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
class User(AbstractUser):
    ROLE_CHOICES = (('admin', 'Admin'), ('donor', 'Donor'), ('hospital', 'Hospital'))
    BLOOD_GROUP_CHOICES = (('A+', 'A+'), ('A-', 'A-'), ('B+', 'B+'), ('B-', 'B-'), 
                           ('AB+', 'AB+'), ('AB-', 'AB-'), ('O+', 'O+'), ('O-', 'O-'))
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='donor')
    blood_group = models.CharField(max_length=5, blank=True, null=True, choices=BLOOD_GROUP_CHOICES)
    location = models.CharField(max_length=100, blank=True, null=True)
    phone = models.CharField(max_length=15, blank=True, null=True)
    is_available = models.BooleanField(default=True)  # For donor availability
    donation_count = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.username} ({self.role})"

class BloodBank(models.Model):
    name = models.CharField(max_length=200)
    location = models.CharField(max_length=100)
    contact = models.CharField(max_length=15)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

class BloodInventory(models.Model):
    BLOOD_GROUPS = (('A+', 'A+'), ('A-', 'A-'), ('B+', 'B+'), ('B-', 'B-'), 
                    ('AB+', 'AB+'), ('AB-', 'AB-'), ('O+', 'O+'), ('O-', 'O-'))
    
    blood_bank = models.ForeignKey(BloodBank, on_delete=models.CASCADE)
    blood_group = models.CharField(max_length=3, choices=BLOOD_GROUPS)
    units_available = models.IntegerField(default=0)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.blood_bank.name} - {self.blood_group}: {self.units_available}"

from django.db import models
from django.utils import timezone

class DonationRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('completed', 'Completed'),
        ('rejected', 'Rejected'),
    ]
    donor = models.ForeignKey(User, on_delete=models.CASCADE)
    blood_bank = models.ForeignKey(BloodBank, on_delete=models.CASCADE)
    blood_group = models.CharField(max_length=5) # Increased to 5 for groups like 'AB-ve'
    units = models.IntegerField(default=1)
    
    # ADD THIS FIELD:
    date = models.DateField(default=timezone.now) 
    
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.donor.username} - {self.status}"
class BloodRequest(models.Model):
    STATUS_CHOICES = (('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected'))
    hospital = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'hospital'}, related_name='blood_requests')
    blood_bank = models.ForeignKey(BloodBank, on_delete=models.CASCADE)
    blood_group = models.CharField(max_length=3)
    units_needed = models.IntegerField()
    urgency = models.CharField(max_length=20, choices=(('normal', 'Normal'), ('urgent', 'Urgent')), default='normal')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.hospital.username} needs {self.units_needed} {self.blood_group}"
    
    
class EmergencyPost(models.Model):
    BLOOD_GROUPS = (('A+', 'A+'), ('A-', 'A-'), ('B+', 'B+'), ('B-', 'B-'), 
                    ('AB+', 'AB+'), ('AB-', 'AB-'), ('O+', 'O+'), ('O-', 'O-'))
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    patient_name = models.CharField(max_length=100)
    blood_group = models.CharField(max_length=5, choices=BLOOD_GROUPS) # Use your existing choices
    disease_name = models.CharField(max_length=200)
    location = models.CharField(max_length=255)
    needed_by = models.DateTimeField()
    description = models.TextField(blank=True)
    is_managed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Emergency {self.blood_group} for {self.patient_name}"

class PostComment(models.Model):
    post = models.ForeignKey(EmergencyPost, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)    