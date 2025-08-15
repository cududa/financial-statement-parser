import csv
import pandas as pd
from pathlib import Path
from typing import List, Optional
from datetime import datetime
import logging

try:
    from .models import Transaction, StatementSummary
except ImportError:
    from models import Transaction, StatementSummary

logger = logging.getLogger(__name__)


class CSVExporter:
    """
    CSV export module optimized for Google Sheets compatibility.
    Handles various output formats and summary reporting.
    """
    
    def __init__(self):
        self.default_columns = [
            'Date', 'Amount', 'Type', 'Description', 'Merchant', 
            'Card', 'Category', 'Source_File', 'Month', 'Page'
        ]
    
    def format_data_for_export(self, transactions: List[Transaction], 
                             source_file: str = "unknown") -> List[dict]:
        """
        Format transaction data for CSV export.
        Returns list of dictionaries ready for CSV writing.
        """
        formatted_data = []
        
        for transaction in transactions:
            row = {
                'Date': transaction.full_date.strftime('%Y-%m-%d'),
                'Amount': float(transaction.signed_amount),  # Negative for debits
                'Type': transaction.transaction_type,
                'Description': transaction.description,
                'Merchant': transaction.merchant,
                'Card': transaction.card_last_four,
                'Category': transaction.category,
                'Source_File': source_file,
                'Month': f"{transaction.year}-{transaction.month:02d}",
                'Page': transaction.page_number
            }
            formatted_data.append(row)
        
        # Sort by date
        formatted_data.sort(key=lambda x: x['Date'])
        
        logger.info(f"Formatted {len(formatted_data)} transactions for export")
        return formatted_data
    
    def generate_csv_output(self, transactions: List[Transaction], 
                          output_path: Path, source_file: str = "unknown") -> bool:
        """
        Generate CSV file from transactions.
        Returns True if successful.
        """
        try:
            formatted_data = self.format_data_for_export(transactions, source_file)
            
            with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=self.default_columns)
                writer.writeheader()
                writer.writerows(formatted_data)
            
            logger.info(f"Successfully exported {len(transactions)} transactions to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export CSV to {output_path}: {e}")
            return False
    
    def create_google_sheets_compatible_format(self, transactions: List[Transaction],
                                             output_path: Path, source_file: str = "unknown") -> bool:
        """
        Create CSV optimized specifically for Google Sheets import.
        Includes proper date formatting and data types.
        """
        try:
            # Use pandas for better Google Sheets compatibility
            formatted_data = self.format_data_for_export(transactions, source_file)
            df = pd.DataFrame(formatted_data)
            
            # Ensure proper data types for Google Sheets
            df['Date'] = pd.to_datetime(df['Date']).dt.strftime('%Y-%m-%d')
            df['Amount'] = df['Amount'].astype(float)
            
            # Save with specific options for Google Sheets
            df.to_csv(
                output_path,
                index=False,
                encoding='utf-8',
                date_format='%Y-%m-%d',
                float_format='%.2f'
            )
            
            logger.info(f"Exported Google Sheets compatible CSV: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create Google Sheets format: {e}")
            return False
    
    def generate_summary_report(self, transactions: List[Transaction], 
                              summary: StatementSummary, output_path: Path) -> bool:
        """
        Generate summary report with totals and statistics.
        """
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write("PNC Statement Processing Summary\n")
                f.write("=" * 40 + "\n\n")
                
                # Statement info
                f.write(f"Account: {summary.account_number}\n")
                f.write(f"Period: {summary.statement_period_start.strftime('%m/%d/%Y')} to {summary.statement_period_end.strftime('%m/%d/%Y')}\n")
                f.write(f"Pages: {summary.total_pages}\n\n")
                
                # Transaction counts
                credit_count = len([t for t in transactions if t.transaction_type == 'CREDIT'])
                debit_count = len([t for t in transactions if t.transaction_type == 'DEBIT'])
                
                f.write(f"Transaction Counts:\n")
                f.write(f"  Credits: {credit_count}\n")
                f.write(f"  Debits: {debit_count}\n")
                f.write(f"  Total: {len(transactions)}\n\n")
                
                # Amount totals
                total_credits = sum(t.amount for t in transactions if t.transaction_type == 'CREDIT')
                total_debits = sum(t.amount for t in transactions if t.transaction_type == 'DEBIT')
                net_change = total_credits - total_debits
                
                f.write(f"Amount Totals:\n")
                f.write(f"  Total Credits: ${total_credits:,.2f}\n")
                f.write(f"  Total Debits: ${total_debits:,.2f}\n")
                f.write(f"  Net Change: ${net_change:,.2f}\n\n")
                
                # Category breakdown
                self._write_category_breakdown(f, transactions)
                
                # Merchant summary
                self._write_merchant_summary(f, transactions)
            
            logger.info(f"Generated summary report: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to generate summary report: {e}")
            return False
    
    def _write_category_breakdown(self, file, transactions: List[Transaction]):
        """Write category breakdown to summary file"""
        categories = {}
        
        for transaction in transactions:
            category = transaction.category
            if category not in categories:
                categories[category] = {'count': 0, 'total': 0}
            
            categories[category]['count'] += 1
            categories[category]['total'] += float(transaction.signed_amount)
        
        file.write("Category Breakdown:\n")
        for category, data in sorted(categories.items()):
            file.write(f"  {category}: {data['count']} transactions, ${data['total']:,.2f}\n")
        file.write("\n")
    
    def _write_merchant_summary(self, file, transactions: List[Transaction]):
        """Write top merchants to summary file"""
        merchants = {}
        
        for transaction in transactions:
            merchant = transaction.merchant
            if merchant and merchant != "Unknown":
                if merchant not in merchants:
                    merchants[merchant] = {'count': 0, 'total': 0}
                
                merchants[merchant]['count'] += 1
                merchants[merchant]['total'] += abs(float(transaction.signed_amount))
        
        # Sort by total amount
        sorted_merchants = sorted(merchants.items(), key=lambda x: x[1]['total'], reverse=True)
        
        file.write("Top Merchants by Amount:\n")
        for merchant, data in sorted_merchants[:10]:  # Top 10
            file.write(f"  {merchant}: {data['count']} transactions, ${data['total']:,.2f}\n")
        file.write("\n")
    
    def export_monthly_files(self, transactions: List[Transaction], 
                           output_dir: Path, source_file: str = "unknown") -> bool:
        """
        Export separate CSV files for each month.
        """
        try:
            # Group transactions by month
            monthly_groups = {}
            for transaction in transactions:
                month_key = f"{transaction.year}-{transaction.month:02d}"
                if month_key not in monthly_groups:
                    monthly_groups[month_key] = []
                monthly_groups[month_key].append(transaction)
            
            # Create output directory if it doesn't exist
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Export each month
            for month, month_transactions in monthly_groups.items():
                month_file = output_dir / f"transactions_{month}.csv"
                success = self.generate_csv_output(month_transactions, month_file, source_file)
                if not success:
                    return False
            
            logger.info(f"Exported {len(monthly_groups)} monthly files to {output_dir}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export monthly files: {e}")
            return False