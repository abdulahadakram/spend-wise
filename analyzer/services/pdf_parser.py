import re
import pdfplumber
from datetime import datetime, date
from decimal import Decimal
from typing import List, Dict, Any, Optional


class PDFParser:
    """Parser for extracting transaction data from bank statement PDFs"""
    
    def __init__(self):
        # Updated patterns for Meezan Bank format
        self.date_patterns = [
            r'(Mon|Tue|Wed|Thu|Fri|Sat|Sun)\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2}',  # Wed Jun 26
            r'\d{2}/\d{2}/\d{4}',  # DD/MM/YYYY
            r'\d{2}-\d{2}-\d{4}',  # DD-MM-YYYY
            r'\d{4}-\d{2}-\d{2}',  # YYYY-MM-DD
        ]
        self.amount_patterns = [
            r'[\d,]+\.\d{2}',  # 1,234.56
            r'[\d,]+\.\d{2}',  # 1234.56
        ]
        
        # Month mapping for conversion
        self.month_map = {
            'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
            'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12
        }
    
    def parse_pdf(self, file_path: str) -> List[Dict[str, Any]]:
        """Extract transactions from PDF file"""
        transactions = []
        
        try:
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        page_transactions = self._extract_transactions_from_text(text)
                        transactions.extend(page_transactions)
            
            return transactions
        except Exception as e:
            print(f"Error parsing PDF: {e}")
            return []
    
    def _extract_transactions_from_text(self, text: str) -> List[Dict[str, Any]]:
        """Extract transaction data from text content"""
        transactions = []
        lines = text.split('\n')
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Look for transaction start (date pattern)
            date_match = self._find_date_in_line(line)
            if date_match:
                # Try to parse this as a transaction
                transaction = self._parse_meezan_transaction(lines, i)
                if transaction:
                    transactions.append(transaction)
                    # Skip lines we've already processed
                    i = transaction.get('next_line_index', i + 1)
                else:
                    i += 1
            else:
                i += 1
        return transactions
    
    def _find_date_in_line(self, line: str) -> Optional[re.Match]:
        """Find date pattern in a line"""
        for pattern in self.date_patterns:
            match = re.search(pattern, line)
            if match:
                return match
        return None
    
    def _parse_meezan_transaction(self, lines: List[str], start_index: int) -> Optional[Dict[str, Any]]:
        """Parse Meezan Bank transaction format with 5 columns"""
        if start_index >= len(lines):
            return None
        
        # Get the first line (should contain date)
        first_line = lines[start_index].strip()
        
        # Extract date
        date_match = self._find_date_in_line(first_line)
        if not date_match:
            return None
        
        date_str = date_match.group()
        transaction_date = self._parse_meezan_date(date_str)
        if not transaction_date:
            return None
        
        # Extract description and amount from the transaction block
        description_lines = []
        debit_amount = None
        credit_amount = None
        temp_amount = None
        transaction_type = 'DEBIT'  # Default
        
        # Look for amount in the first line
        amount_matches = re.findall(r'([\d,]+\.\d{2})', first_line)
        if amount_matches:
            # Take the last amount found (usually the transaction amount, not balance)
            amount_str = amount_matches[-1].replace(',', '')
            temp_amount = Decimal(amount_str)
            
            # Remove date and all amounts from first line for description
            desc_part = first_line
            for match in amount_matches:
                desc_part = desc_part.replace(match, '')
            desc_part = desc_part.replace(date_str, '').strip()
            if desc_part:
                description_lines.append(desc_part)
        
        # Look for description in subsequent lines
        i = start_index + 1
        while i < len(lines):
            line = lines[i].strip()
            
            # Stop if we hit another date (next transaction)
            if self._find_date_in_line(line):
                break
            
            # Look for amount in this line
            amount_matches = re.findall(r'([\d,]+\.\d{2})', line)
            if amount_matches and temp_amount is None:
                # Take the last amount found (usually the transaction amount, not balance)
                amount_str = amount_matches[-1].replace(',', '')
                temp_amount = Decimal(amount_str)
                
                # Remove all amounts from line for description
                desc_part = line
                for match in amount_matches:
                    desc_part = desc_part.replace(match, '')
                desc_part = desc_part.strip()
                if desc_part:
                    description_lines.append(desc_part)
            elif line and not amount_matches:
                # This line is part of description
                description_lines.append(line)
            
            i += 1
        
        # Combine description lines
        description = ' '.join(description_lines).strip()
        
        # Clean up description
        description = re.sub(r'\s+', ' ', description)
        description = re.sub(r'STAN\(\d+\)', '', description)  # Remove STAN numbers
        description = description.strip()
        
        if not description:
            description = "Unknown Transaction"
        
        # Determine transaction type based on description keywords and amounts
        description_lower = description.lower()
        
        # Keywords that indicate CREDIT (money coming in)
        credit_keywords = [
            'received', 'remittance', 'salary', 'batch transfer', 'inward rtgs',
            'home remittance', 'money received', 'credit', 'money received from',
            'remittance from', 'transfer from', 'raast p2p fund transfer from'
        ]
        
        # Keywords that indicate DEBIT (money going out)
        debit_keywords = [
            'transferred', 'charges', 'pos', 'purchase', 'atm cash', 'withdrawal',
            'money transferred', 'debit', 'taxes', 'fed', 'bank charges', 'bill paid',
            'raast p2p fund transfer to', 'chg:', 'visa card', 'replacement fee',
            'er ', 'payment gateway', 'payfast', 'gopb', 'telenor', 'zong', 'easy card',
            'monthly', 'prepaid', 'from ib', 'rev ', 'fbrtax:', 'stan (', 'transfer to'
        ]
        
        # Check for credit keywords first
        if any(keyword in description_lower for keyword in credit_keywords):
            transaction_type = 'CREDIT'
        # Then check for debit keywords
        elif any(keyword in description_lower for keyword in debit_keywords):
            transaction_type = 'DEBIT'
        # If no keywords match, default to DEBIT for safety
        else:
            transaction_type = 'DEBIT'
        
        # Use the temp_amount if available, otherwise 0
        amount = temp_amount if 'temp_amount' in locals() else 0
        
        return {
            'date': transaction_date,
            'description': description,
            'amount': abs(amount) if amount else 0,
            'type': transaction_type,
            'next_line_index': i
        }
    
    def _parse_meezan_date(self, date_str: str) -> Optional[date]:
        """Parse Meezan Bank date format (e.g., 'Wed Jun 26')"""
        try:
            # Handle "Wed Jun 26" format
            if re.match(r'(Mon|Tue|Wed|Thu|Fri|Sat|Sun)\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2}', date_str):
                parts = date_str.split()
                day = int(parts[2])
                month = self.month_map[parts[1]]
                year = 2024  # Assuming current year, you might want to extract this from the statement
                return date(year, month, day)
            
            # Handle other date formats
            for fmt in ['%d/%m/%Y', '%d-%m-%Y', '%Y-%m-%d']:
                try:
                    return datetime.strptime(date_str, fmt).date()
                except ValueError:
                    continue
        except:
            pass
        return None
    
    def _extract_date(self, line: str) -> Optional[date]:
        """Extract date from line"""
        for pattern in self.date_patterns:
            match = re.search(pattern, line)
            if match:
                date_str = match.group()
                return self._parse_meezan_date(date_str)
        return None
    
    def _extract_amount(self, line: str) -> Optional[Decimal]:
        """Extract amount from line"""
        for pattern in self.amount_patterns:
            matches = re.findall(pattern, line)
            if matches:
                # Take the last amount found (usually the transaction amount)
                amount_str = matches[-1].replace(',', '')
                try:
                    return Decimal(amount_str)
                except:
                    continue
        return None
    
    def _extract_description(self, line: str, date: date, amount: Decimal) -> str:
        """Extract description from line"""
        # Remove date and amount from line to get description
        line_clean = line
        
        # Remove date
        for pattern in self.date_patterns:
            line_clean = re.sub(pattern, '', line_clean)
        
        # Remove amount
        for pattern in self.amount_patterns:
            line_clean = re.sub(pattern, '', line_clean)
        
        # Clean up extra spaces and special characters
        description = re.sub(r'\s+', ' ', line_clean).strip()
        description = re.sub(r'[^\w\s\-\.]', '', description)
        
        return description if description else "Unknown Transaction" 