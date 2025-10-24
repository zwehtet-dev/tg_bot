"""
Validation utilities
"""
from typing import Optional


class Validators:
    """Validation helper functions"""
    
    @staticmethod
    def validate_amount(amount_str: str) -> Optional[float]:
        """
        Validate and parse amount string
        
        Args:
            amount_str: Amount as string
            
        Returns:
            Float amount or None if invalid
        """
        try:
            amount = float(amount_str.replace(',', ''))
            if amount <= 0:
                return None
            return amount
        except (ValueError, AttributeError):
            return None
    
    @staticmethod
    def validate_bank_info(bank_info_str: str) -> Optional[tuple]:
        """
        Validate and parse bank information
        
        Args:
            bank_info_str: Bank info string in format "Bank | Account | Name"
            
        Returns:
            Tuple of (bank_name, account_number, account_name) or None if invalid
        """
        parts = bank_info_str.split('|')
        
        if len(parts) != 3:
            return None
        
        bank_name = parts[0].strip()
        account_number = parts[1].strip()
        account_name = parts[2].strip()
        
        if not all([bank_name, account_number, account_name]):
            return None
        
        return (bank_name, account_number, account_name)
    
    @staticmethod
    def is_supported_bank(bank_name: str, supported_banks: list) -> bool:
        """
        Check if bank is in supported list
        
        Args:
            bank_name: Bank name to check
            supported_banks: List of supported bank names
            
        Returns:
            True if supported, False otherwise
        """
        return any(bank.lower() in bank_name.lower() for bank in supported_banks)
