"""
Formatting utilities
"""
from datetime import datetime


class Formatters:
    """Formatting helper functions"""
    
    @staticmethod
    def format_currency(amount: float, currency: str = "THB") -> str:
        """
        Format currency amount
        
        Args:
            amount: Amount to format
            currency: Currency code
            
        Returns:
            Formatted string
        """
        if currency == "MMK":
            return f"{amount:,.0f} {currency}"
        return f"{amount:,.2f} {currency}"
    
    @staticmethod
    def format_datetime(dt: datetime) -> str:
        """
        Format datetime for display
        
        Args:
            dt: Datetime object
            
        Returns:
            Formatted string
        """
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    
    @staticmethod
    def format_transaction_summary(transaction: tuple) -> str:
        """
        Format transaction for display
        
        Args:
            transaction: Transaction tuple from database
            
        Returns:
            Formatted string
        """
        txn_id = transaction[0]
        thb_amount = transaction[6]
        mmk_amount = transaction[7]
        status = transaction[13]
        
        status_emoji = {
            'confirmed': '✅',
            'pending': '⏳',
            'cancelled': '❌'
        }.get(status, '❓')
        
        return f"{status_emoji} #{txn_id} - {thb_amount} THB → {mmk_amount:,.0f} MMK - `{status}`"
