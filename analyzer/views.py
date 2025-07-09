import json
import uuid
import os
import decimal
from datetime import datetime
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.conf import settings
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework import status

from .models import AnalysisSession, Transaction, AnalysisResult
from .services.pdf_parser import PDFParser
from .services.ml_analyzer import MLAnalyzer


def index(request):
    """Main upload page"""
    return render(request, 'analyzer/index.html')


@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def upload_statement(request):
    """Handle PDF statement upload and analysis"""
    try:
        if 'file' not in request.FILES:
            return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        uploaded_file = request.FILES['file']
        
        # Validate file
        if not uploaded_file.name.lower().endswith('.pdf'):
            return Response({'error': 'Only PDF files are supported'}, status=status.HTTP_400_BAD_REQUEST)
        
        if uploaded_file.size > 1024 * 1024:  # 1MB limit
            return Response({'error': 'File size must be less than 1MB'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Create analysis session
        session_id = str(uuid.uuid4())
        session = AnalysisSession.objects.create(
            session_id=session_id,
            file_name=uploaded_file.name,
            file_size=uploaded_file.size
        )
        
        # Save file temporarily
        relative_path = default_storage.save(f'statements/{session_id}.pdf', ContentFile(uploaded_file.read()))
        absolute_path = os.path.join(settings.MEDIA_ROOT, relative_path)
        
        print(f"Saved file to: {absolute_path}")
        
        # Parse PDF
        parser = PDFParser()
        transactions = parser.parse_pdf(absolute_path)
        
        if not transactions:
            return Response({'error': 'Could not extract transactions from PDF'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Save transactions with error handling
        for trans_data in transactions:
            try:
                Transaction.objects.create(
                    session=session,
                    date=trans_data['date'],
                    description=trans_data['description'],
                    amount=trans_data['amount'],
                    transaction_type=trans_data['type']
                )
            except Exception as e:
                print(f"Error saving transaction {trans_data.get('description', 'Unknown')}: {e}")
                continue
        
        # Analyze with ML
        analyzer = MLAnalyzer()
        
        # Convert QuerySet to the format expected by ML analyzer
        transactions_for_analysis = []
        for trans in session.transactions.all():
            transactions_for_analysis.append({
                'date': trans.date,
                'description': trans.description,
                'amount': trans.amount,
                'type': trans.transaction_type
            })
        
        analysis_result = analyzer.analyze_transactions(transactions_for_analysis)
        
        # Save analysis result with error handling
        try:
            AnalysisResult.objects.create(
                session=session,
                total_income=analysis_result['total_income'],
                total_expenses=analysis_result['total_expenses'],
                net_amount=analysis_result['net_amount'],
                category_breakdown=analysis_result['category_breakdown'],
                anomaly_transactions=analysis_result['anomalies'],
                insights=analysis_result['insights']
            )
        except Exception as e:
            print(f"Error saving analysis result: {e}")
            # Continue without saving to database, but still return the result
        
        # Clean up temporary file
        default_storage.delete(relative_path)
        
        # Convert analysis result to JSON-serializable format
        def convert_decimals(obj):
            if isinstance(obj, dict):
                return {k: convert_decimals(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_decimals(item) for item in obj]
            elif hasattr(obj, '__float__') and not isinstance(obj, (str, bool)):  # Only convert numeric types
                try:
                    return float(obj) if obj is not None else 0.0
                except (ValueError, TypeError, decimal.InvalidOperation):
                    return 0.0
            else:
                return obj
        
        try:
            analysis_result_serializable = convert_decimals(analysis_result)
            
            return Response({
                'session_id': session_id,
                'analysis': analysis_result_serializable
            }, status=status.HTTP_200_OK)
        except Exception as e:
            print(f"Error serializing analysis result: {e}")
            # Return a simplified response if serialization fails
            return Response({
                'session_id': session_id,
                'analysis': {
                    'total_income': 0.0,
                    'total_expenses': 0.0,
                    'net_amount': 0.0,
                    'category_breakdown': {},
                    'anomalies': [],
                    'insights': {}
                }
            }, status=status.HTTP_200_OK)
        
    except Exception as e:
        print(f"Error in upload_statement: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def get_analysis(request, session_id):
    """Get analysis results for a session"""
    try:
        session = AnalysisSession.objects.get(session_id=session_id)
        analysis = session.analysis_result
        
        return Response({
            'session_id': session_id,
            'analysis': {
                'total_income': float(analysis.total_income),
                'total_expenses': float(analysis.total_expenses),
                'net_amount': float(analysis.net_amount),
                'category_breakdown': analysis.category_breakdown,
                'anomaly_transactions': analysis.anomaly_transactions,
                'insights': analysis.insights,
                'transactions': [
                    {
                        'date': trans.date.isoformat(),
                        'description': trans.description,
                        'amount': float(trans.amount),
                        'type': trans.transaction_type,
                        'category': trans.category
                    }
                    for trans in session.transactions.all()
                ]
            }
        }, status=status.HTTP_200_OK)
        
    except AnalysisSession.DoesNotExist:
        return Response({'error': 'Analysis session not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR) 