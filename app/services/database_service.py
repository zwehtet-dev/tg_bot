"""
Database service for managing transactions and balances
"""
import sqlite3
from datetime import datetime
from typing import List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class DatabaseService:
    """Manages SQLite database operations"""
    
    def __init__(self, db_path: str = "exchange_bot.db"):
        """
        Initialize database service
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.init_database()
        logger.info(f"Database service initialized: {db_path}")
    
    def get_connection(self) -> sqlite3.Connection:
        """Get database connection"""
        return sqlite3.connect(self.db_path)
    
    def init_database(self):
        """Initialize database tables"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Create transactions table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    username TEXT,
                    receipt_path TEXT,
                    admin_receipt_path TEXT,
                    from_bank TEXT,
                    to_bank TEXT,
                    thb_amount REAL,
                    mmk_amount REAL,
                    rate REAL,
                    user_bank_name TEXT,
                    user_account_number TEXT,
                    user_account_name TEXT,
                    admin_bank TEXT,
                    admin_thb_bank TEXT,
                    status TEXT DEFAULT 'pending',
                    transaction_ref TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    confirmed_at TIMESTAMP
                )
            """)
            
            # Create exchange_rate table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS exchange_rate (
                    id INTEGER PRIMARY KEY,
                    rate REAL NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create bot_settings table for dynamic configuration
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS bot_settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create admin_bank_accounts table with balance
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS admin_bank_accounts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    currency TEXT NOT NULL,
                    bank_name TEXT NOT NULL,
                    account_number TEXT NOT NULL,
                    account_name TEXT NOT NULL,
                    balance REAL DEFAULT 0.0,
                    is_active INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(currency, bank_name, account_number)
                )
            """)
            
            # Add balance column to existing admin_bank_accounts if it doesn't exist
            try:
                cursor.execute("ALTER TABLE admin_bank_accounts ADD COLUMN balance REAL DEFAULT 0.0")
                logger.info("Added balance column to admin_bank_accounts")
            except:
                pass  # Column already exists
            
            # Add display_name column to existing admin_bank_accounts if it doesn't exist
            try:
                cursor.execute("ALTER TABLE admin_bank_accounts ADD COLUMN display_name TEXT")
                logger.info("Added display_name column to admin_bank_accounts")
            except:
                pass  # Column already exists
            
            # Add updated_at column if it doesn't exist
            try:
                cursor.execute("ALTER TABLE admin_bank_accounts ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
                logger.info("Added updated_at column to admin_bank_accounts")
            except:
                pass  # Column already exists
            
            conn.commit()
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Error creating database tables: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def initialize_balances(self, initial_balances: List[Tuple[str, str, float]]):
        """Initialize balances in admin_bank_accounts if needed (only if balance is NULL or 0)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Only update balances for accounts that have NULL or 0 balance
            for currency, bank, balance in initial_balances:
                cursor.execute("""
                    UPDATE admin_bank_accounts 
                    SET balance = ?, updated_at = ?
                    WHERE currency = ? AND bank_name = ? 
                    AND (balance IS NULL OR balance = 0)
                """, (balance, datetime.now(), currency, bank))
            
            conn.commit()
            logger.info("Initial balances set successfully in admin_bank_accounts (only for NULL/0 balances)")
        except Exception as e:
            logger.error(f"Error initializing balances: {e}")
            conn.rollback()
        finally:
            conn.close()
    
    def initialize_exchange_rate(self, default_rate: float):
        """Initialize exchange rate if not set"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT COUNT(*) FROM exchange_rate")
            if cursor.fetchone()[0] == 0:
                cursor.execute("INSERT INTO exchange_rate (id, rate) VALUES (1, ?)", (default_rate,))
                conn.commit()
                logger.info(f"Exchange rate initialized to {default_rate}")
        except Exception as e:
            logger.error(f"Error initializing exchange rate: {e}")
            conn.rollback()
        finally:
            conn.close()
    
    def get_current_rate(self) -> float:
        """Get current exchange rate"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT rate FROM exchange_rate WHERE id = 1")
            result = cursor.fetchone()
            return result[0] if result else 121.5
        except Exception as e:
            logger.error(f"Error getting exchange rate: {e}")
            return 121.5
        finally:
            conn.close()
    
    def update_rate(self, new_rate: float):
        """Update exchange rate"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                "UPDATE exchange_rate SET rate = ?, updated_at = ? WHERE id = 1", 
                (new_rate, datetime.now())
            )
            conn.commit()
            logger.info(f"Exchange rate updated to {new_rate}")
        except Exception as e:
            logger.error(f"Error updating exchange rate: {e}")
            conn.rollback()
        finally:
            conn.close()
    
    def get_balances(self) -> List[Tuple[str, str, float, str]]:
        """Get all balances from admin_bank_accounts"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT currency, bank_name, balance, display_name
                FROM admin_bank_accounts 
                WHERE is_active = 1
                ORDER BY currency, bank_name
            """)
            return cursor.fetchall()
        except Exception as e:
            logger.error(f"Error getting balances: {e}")
            return []
        finally:
            conn.close()
    
    def update_balance(self, currency: str, bank: str, amount_change: float):
        """Update balance for a specific bank"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                "UPDATE admin_bank_accounts SET balance = balance + ?, updated_at = ? WHERE currency = ? AND bank_name = ?",
                (amount_change, datetime.now(), currency, bank)
            )
            conn.commit()
            logger.info(f"Balance updated: {currency} {bank} {amount_change:+.2f}")
        except Exception as e:
            logger.error(f"Error updating balance: {e}")
            conn.rollback()
        finally:
            conn.close()
    
    def create_transaction(
        self, 
        user_id: int, 
        username: Optional[str],
        thb_amount: float, 
        mmk_amount: float, 
        rate: float, 
        user_bank_name: str, 
        user_account_number: str, 
        user_account_name: str, 
        from_bank: str, 
        receipt_path: Optional[str] = None,
        admin_thb_bank: Optional[str] = None
    ) -> int:
        """Create a new transaction"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO transactions 
                (user_id, username, receipt_path, from_bank, thb_amount, mmk_amount, rate, 
                 user_bank_name, user_account_number, user_account_name, admin_thb_bank, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending')
            """, (user_id, username, receipt_path, from_bank, thb_amount, mmk_amount, rate,
                  user_bank_name, user_account_number, user_account_name, admin_thb_bank))
            
            transaction_id = cursor.lastrowid
            conn.commit()
            logger.info(f"Transaction created: #{transaction_id} with admin_thb_bank: {admin_thb_bank}")
            return transaction_id
        except Exception as e:
            logger.error(f"Error creating transaction: {e}")
            conn.rollback()
            return 0
        finally:
            conn.close()
    
    def get_transaction(self, transaction_id: int) -> Optional[Tuple]:
        """Get transaction by ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT * FROM transactions WHERE id = ?", (transaction_id,))
            return cursor.fetchone()
        except Exception as e:
            logger.error(f"Error getting transaction: {e}")
            return None
        finally:
            conn.close()
    
    def update_transaction_status(
        self, 
        transaction_id: int, 
        status: str, 
        admin_bank: Optional[str] = None
    ):
        """Update transaction status"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            if admin_bank:
                cursor.execute("""
                    UPDATE transactions 
                    SET status = ?, admin_bank = ?, confirmed_at = ? 
                    WHERE id = ?
                """, (status, admin_bank, datetime.now(), transaction_id))
            else:
                cursor.execute("""
                    UPDATE transactions 
                    SET status = ?, confirmed_at = ? 
                    WHERE id = ?
                """, (status, datetime.now(), transaction_id))
            
            conn.commit()
            logger.info(f"Transaction #{transaction_id} status updated to {status}")
        except Exception as e:
            logger.error(f"Error updating transaction status: {e}")
            conn.rollback()
        finally:
            conn.close()
    
    def get_today_transactions(self) -> List[Tuple]:
        """Get today's transactions"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            today = datetime.now().date()
            cursor.execute("""
                SELECT * FROM transactions 
                WHERE DATE(created_at) = ? 
                ORDER BY created_at DESC
            """, (today,))
            return cursor.fetchall()
        except Exception as e:
            logger.error(f"Error getting today's transactions: {e}")
            return []
        finally:
            conn.close()

    # Bot Settings Methods
    def get_setting(self, key: str) -> Optional[str]:
        """Get bot setting by key"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT value FROM bot_settings WHERE key = ?", (key,))
            result = cursor.fetchone()
            return result[0] if result else None
        except Exception as e:
            logger.error(f"Error getting setting {key}: {e}")
            return None
        finally:
            conn.close()
    
    def set_setting(self, key: str, value: str):
        """Set or update bot setting"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO bot_settings (key, value, updated_at) 
                VALUES (?, ?, ?)
                ON CONFLICT(key) DO UPDATE SET value = ?, updated_at = ?
            """, (key, value, datetime.now(), value, datetime.now()))
            conn.commit()
            logger.info(f"Setting updated: {key} = {value}")
        except Exception as e:
            logger.error(f"Error setting {key}: {e}")
            conn.rollback()
        finally:
            conn.close()
    
    # Admin Bank Account Methods
    def add_admin_bank_account(self, currency: str, bank_name: str, 
                               account_number: str, account_name: str,
                               display_name: Optional[str] = None):
        """Add admin bank account"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO admin_bank_accounts 
                (currency, bank_name, account_number, account_name, display_name)
                VALUES (?, ?, ?, ?, ?)
            """, (currency, bank_name, account_number, account_name, display_name))
            conn.commit()
            logger.info(f"Admin bank account added: {bank_name} - {account_number}")
        except sqlite3.IntegrityError:
            logger.warning(f"Admin bank account already exists: {bank_name} - {account_number}")
        except Exception as e:
            logger.error(f"Error adding admin bank account: {e}")
            conn.rollback()
        finally:
            conn.close()
    
    def get_admin_bank_accounts(self, currency: Optional[str] = None) -> List[Tuple]:
        """Get admin bank accounts"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            if currency:
                cursor.execute("""
                    SELECT id, currency, bank_name, account_number, account_name, is_active, display_name
                    FROM admin_bank_accounts 
                    WHERE currency = ? AND is_active = 1
                    ORDER BY bank_name
                """, (currency,))
            else:
                cursor.execute("""
                    SELECT id, currency, bank_name, account_number, account_name, is_active, display_name
                    FROM admin_bank_accounts 
                    WHERE is_active = 1
                    ORDER BY currency, bank_name
                """)
            return cursor.fetchall()
        except Exception as e:
            logger.error(f"Error getting admin bank accounts: {e}")
            return []
        finally:
            conn.close()
    
    def normalize_name(self, name: str) -> str:
        """Normalize name for comparison (remove spaces, lowercase, remove prefixes and special chars)"""
        if not name:
            return ""
        
        # Convert to lowercase and remove extra spaces
        normalized = name.lower().strip()
        
        # Remove common title prefixes
        prefixes = ['miss', 'mr', 'mrs', 'ms', 'dr', 'prof', 'sir', 'madam']
        for prefix in prefixes:
            # Check for prefix with space or dot
            if normalized.startswith(prefix + ' '):
                normalized = normalized[len(prefix) + 1:].strip()
                break
            elif normalized.startswith(prefix + '.'):
                normalized = normalized[len(prefix) + 1:].strip()
                break
        
        # Remove special characters and extra spaces
        # Keep only alphanumeric characters
        normalized = ''.join(c for c in normalized if c.isalnum() or c.isspace())
        
        # Remove all spaces and return
        return ''.join(normalized.split())
    
    def calculate_similarity(self, str1: str, str2: str) -> float:
        """
        Calculate similarity between two strings using Levenshtein distance
        Returns a value between 0 and 1, where 1 is identical
        """
        if not str1 or not str2:
            return 0.0
        
        # Normalize both strings
        s1 = self.normalize_name(str1)
        s2 = self.normalize_name(str2)
        
        if s1 == s2:
            return 1.0
        
        # Calculate Levenshtein distance
        len1, len2 = len(s1), len(s2)
        if len1 == 0 or len2 == 0:
            return 0.0
        
        # Create distance matrix
        matrix = [[0] * (len2 + 1) for _ in range(len1 + 1)]
        
        for i in range(len1 + 1):
            matrix[i][0] = i
        for j in range(len2 + 1):
            matrix[0][j] = j
        
        for i in range(1, len1 + 1):
            for j in range(1, len2 + 1):
                cost = 0 if s1[i-1] == s2[j-1] else 1
                matrix[i][j] = min(
                    matrix[i-1][j] + 1,      # deletion
                    matrix[i][j-1] + 1,      # insertion
                    matrix[i-1][j-1] + cost  # substitution
                )
        
        distance = matrix[len1][len2]
        max_len = max(len1, len2)
        similarity = 1 - (distance / max_len)
        
        return similarity
    
    def validate_receiver_account(self, account_name: str, bank_name: str = None, currency: str = 'THB') -> Optional[Tuple]:
        """Validate if receiver account name and bank matches admin accounts (case-insensitive)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Normalize input for comparison
            normalized_input_name = self.normalize_name(account_name)
            
            # Get all active admin accounts for the currency
            cursor.execute("""
                SELECT id, bank_name, account_number, account_name
                FROM admin_bank_accounts 
                WHERE currency = ? AND is_active = 1
            """, (currency,))
            
            accounts = cursor.fetchall()
            
            # First pass: exact match
            # Second pass: fuzzy match (for OCR errors)
            best_match = None
            best_similarity = 0.0
            similarity_threshold = 0.80  # 80% similarity required (more lenient for OCR errors)
            
            for account in accounts:
                acc_id, acc_bank, acc_number, acc_name = account
                normalized_acc_name = self.normalize_name(acc_name)
                
                # Calculate name similarity
                name_similarity = self.calculate_similarity(account_name, acc_name)
                
                # Log comparison for debugging
                logger.debug(f"Comparing names: '{account_name}' vs '{acc_name}' → similarity: {name_similarity:.2%}")
                
                # Check if names match exactly
                exact_name_match = normalized_input_name == normalized_acc_name
                # Or if similarity is high enough (handles OCR errors like MWE vs NWE)
                fuzzy_name_match = name_similarity >= similarity_threshold
                
                name_matches = exact_name_match or fuzzy_name_match
                
                if name_matches:
                    logger.debug(f"✓ Name matched: {account_name} → {acc_name} ({name_similarity:.2%})")
                
                # If bank name is provided, also check bank
                if bank_name:
                    normalized_input_bank = self.normalize_name(bank_name)
                    normalized_acc_bank = self.normalize_name(acc_bank)
                    
                    logger.debug(f"Comparing banks: '{bank_name}' (normalized: '{normalized_input_bank}') vs '{acc_bank}' (normalized: '{normalized_acc_bank}')")
                    
                    # Check for common bank abbreviations and variations
                    bank_aliases = {
                        # SCB / Siam Commercial Bank variations
                        'scb': 'siamcommercialbank',
                        'siamcommercial': 'siamcommercialbank',
                        'siamcommercialbank': 'siamcommercialbank',
                        'siam': 'siamcommercialbank',
                        # Krungthai variations
                        'ktb': 'krungthaibank',
                        'krungthai': 'krungthaibank',
                        'krungthaibank': 'krungthaibank',
                        # PromptPay
                        'promptpay': 'promptpay',
                        # Kasikorn variations
                        'kbank': 'kasikorn',
                        'kasikorn': 'kasikorn',
                        'kasikornbank': 'kasikorn',
                        # Bangkok Bank variations
                        'bbl': 'bangkokbank',
                        'bangkok': 'bangkokbank',
                        'bangkokbank': 'bangkokbank',
                    }
                    
                    # Apply aliases to both input and account bank
                    check_input_bank = bank_aliases.get(normalized_input_bank, normalized_input_bank)
                    check_acc_bank = bank_aliases.get(normalized_acc_bank, normalized_acc_bank)
                    
                    logger.debug(f"After alias: '{check_input_bank}' vs '{check_acc_bank}'")
                    
                    # Check if banks match using multiple strategies
                    bank_matches = (
                        # Direct match after alias resolution
                        check_input_bank == check_acc_bank or
                        # Substring match (e.g., "scb" in "siamcommercialbank")
                        check_input_bank in check_acc_bank or
                        check_acc_bank in check_input_bank or
                        # Original normalized names substring match
                        normalized_input_bank in normalized_acc_bank or
                        normalized_acc_bank in normalized_input_bank or
                        # Check if input bank alias matches account bank directly
                        check_input_bank == normalized_acc_bank or
                        # Check if account bank alias matches input bank directly
                        check_acc_bank == normalized_input_bank
                    )
                    
                    # Flexible matching: accept if name matches well, even if bank doesn't match perfectly
                    # This handles cases where OCR misreads the bank name
                    if name_matches:
                        # Calculate match score
                        match_score = name_similarity
                        if bank_matches:
                            match_score += 0.1  # Bonus for bank match
                        
                        # Track best match
                        if match_score > best_similarity:
                            best_similarity = match_score
                            best_match = account
                        
                        # If exact name match, return immediately (even if bank doesn't match)
                        if exact_name_match:
                            if bank_matches:
                                logger.info(f"Validated (exact): '{account_name}' at '{bank_name}' matches {acc_name} at {acc_bank}")
                            else:
                                logger.info(f"Validated (name only): '{account_name}' matches {acc_name} (bank mismatch: '{bank_name}' vs '{acc_bank}')")
                            return account
                else:
                    # No bank name provided - match on name only
                    if name_matches:
                        # Track best match for fuzzy matching
                        if name_similarity > best_similarity:
                            best_similarity = name_similarity
                            best_match = account
                        
                        # If exact match, return immediately
                        if exact_name_match:
                            logger.info(f"Validated (exact, no bank): '{account_name}' matches {acc_name}")
                            return account
            
            # Return best fuzzy match if found
            if best_match:
                acc_id, acc_bank, acc_number, acc_name = best_match
                logger.info(f"Validated (fuzzy {best_similarity:.2%}): '{account_name}' at '{bank_name}' matches {acc_name} at {acc_bank}")
                return best_match
            
            logger.warning(f"No match found for: '{account_name}' at '{bank_name}'")
            return None
            
        except Exception as e:
            logger.error(f"Error validating receiver account: {e}")
            return None
        finally:
            conn.close()
    
    def deactivate_admin_bank_account(self, account_id: int):
        """Deactivate admin bank account"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                UPDATE admin_bank_accounts 
                SET is_active = 0 
                WHERE id = ?
            """, (account_id,))
            conn.commit()
            logger.info(f"Admin bank account deactivated: ID {account_id}")
        except Exception as e:
            logger.error(f"Error deactivating admin bank account: {e}")
            conn.rollback()
        finally:
            conn.close()
    
    def update_transaction_with_admin_bank(
        self, 
        transaction_id: int, 
        status: str, 
        admin_mmk_bank: Optional[str] = None,
        admin_thb_bank: Optional[str] = None
    ):
        """Update transaction with admin bank information"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                UPDATE transactions 
                SET status = ?, admin_bank = ?, admin_thb_bank = ?, confirmed_at = ? 
                WHERE id = ?
            """, (status, admin_mmk_bank, admin_thb_bank, datetime.now(), transaction_id))
            
            conn.commit()
            logger.info(f"Transaction #{transaction_id} updated with banks: THB={admin_thb_bank}, MMK={admin_mmk_bank}")
        except Exception as e:
            logger.error(f"Error updating transaction: {e}")
            conn.rollback()
        finally:
            conn.close()
    
    def update_transaction_admin_receipt(self, transaction_id: int, admin_receipt_path: str):
        """Update transaction with admin receipt path"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                UPDATE transactions 
                SET admin_receipt_path = ? 
                WHERE id = ?
            """, (admin_receipt_path, transaction_id))
            
            conn.commit()
            logger.info(f"Transaction #{transaction_id} admin receipt saved: {admin_receipt_path}")
        except Exception as e:
            logger.error(f"Error updating admin receipt: {e}")
            conn.rollback()
        finally:
            conn.close()

    def set_balance(self, currency: str, bank: str, new_balance: float):
        """Set balance for a specific bank in admin_bank_accounts"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                UPDATE admin_bank_accounts 
                SET balance = ?, updated_at = ?
                WHERE currency = ? AND bank_name = ?
            """, (new_balance, datetime.now(), currency, bank))
            
            if cursor.rowcount == 0:
                logger.warning(f"No account found for {currency} {bank}")
            else:
                conn.commit()
                logger.info(f"Balance set: {currency} {bank} = {new_balance:.2f}")
        except Exception as e:
            logger.error(f"Error setting balance: {e}")
            conn.rollback()
        finally:
            conn.close()
    
    def get_balance(self, currency: str, bank: str) -> float:
        """Get balance for a specific bank from admin_bank_accounts"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                "SELECT balance FROM admin_bank_accounts WHERE currency = ? AND bank_name = ?",
                (currency, bank)
            )
            result = cursor.fetchone()
            return result[0] if result else 0.0
        except Exception as e:
            logger.error(f"Error getting balance: {e}")
            return 0.0
        finally:
            conn.close()

    def get_user_recent_pending_transaction(self, user_id: int) -> Optional[Tuple]:
        """Get the most recent pending transaction for a user"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT * FROM transactions 
                WHERE user_id = ? AND status = 'pending'
                ORDER BY created_at DESC
                LIMIT 1
            """, (user_id,))
            return cursor.fetchone()
        except Exception as e:
            logger.error(f"Error getting recent pending transaction for user {user_id}: {e}")
            return None
        finally:
            conn.close()

    def update_bank_display_name(self, account_id: int, display_name: str):
        """Update display name for a bank account"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                UPDATE admin_bank_accounts 
                SET display_name = ?, updated_at = ?
                WHERE id = ?
            """, (display_name, datetime.now(), account_id))
            
            if cursor.rowcount == 0:
                logger.warning(f"No account found with ID {account_id}")
                return False
            else:
                conn.commit()
                logger.info(f"Display name updated for account #{account_id}: {display_name}")
                return True
        except Exception as e:
            logger.error(f"Error updating display name: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
