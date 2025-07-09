from django.db import models
from django.utils import timezone


class AnalysisSession(models.Model):
    """Model to store analysis sessions"""
    session_id = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(default=timezone.now)
    file_name = models.CharField(max_length=255)
    file_size = models.IntegerField()
    
    def __str__(self):
        return f"Analysis {self.session_id} - {self.file_name}"


class Transaction(models.Model):
    """Model to store parsed transactions"""
    session = models.ForeignKey(AnalysisSession, on_delete=models.CASCADE, related_name='transactions')
    date = models.DateField()
    description = models.TextField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_type = models.CharField(max_length=20, choices=[
        ('CREDIT', 'Credit'),
        ('DEBIT', 'Debit'),
    ])
    category = models.CharField(max_length=50, blank=True, null=True)
    confidence = models.FloatField(default=0.0)
    
    class Meta:
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.date} - {self.description} - {self.amount}"


class AnalysisResult(models.Model):
    """Model to store analysis insights"""
    session = models.OneToOneField(AnalysisSession, on_delete=models.CASCADE, related_name='analysis_result')
    total_income = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_expenses = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    net_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    category_breakdown = models.JSONField(default=dict)
    anomaly_transactions = models.JSONField(default=list)
    insights = models.JSONField(default=dict)
    created_at = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return f"Analysis Result for {self.session.session_id}" 