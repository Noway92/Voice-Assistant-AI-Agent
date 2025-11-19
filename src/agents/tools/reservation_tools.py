import csv
import os
from datetime import datetime
from typing import List, Dict, Optional

class ReservationTools:
    """Tools for managing table reservations."""
    
    def __init__(self, csv_file: str = None):
        # Si aucun chemin n'est fourni, utiliser le répertoire du script
        if csv_file is None:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            self.csv_file = os.path.join(script_dir, "../database/reservation.csv")
        else:
            self.csv_file = csv_file
        self._ensure_file_exists()
    
    def _ensure_file_exists(self):
        """Create CSV file if it doesn't exist."""
        if not os.path.exists(self.csv_file):
            with open(self.csv_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['date', 'time', 'table_number', 'capacity', 
                               'customer_name', 'phone', 'num_guests', 'status', 
                               'special_requests'])
    
    def check_availability(self, date: str, time: str, num_guests: int) -> str:
        """
        Check available tables for a specific date, time and number of guests.
        
        Args:
            date: Date in YYYY-MM-DD format
            time: Time in HH:MM format
            num_guests: Number of guests
            
        Returns:
            String describing availability
        """
        try:
            available_tables = []
            
            with open(self.csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if (row['date'] == date and 
                        row['time'] == time and 
                        row['status'] == 'available' and 
                        int(row['capacity']) >= num_guests):
                        available_tables.append({
                            'table_number': row['table_number'],
                            'capacity': row['capacity']
                        })
            
            if available_tables:
                tables_info = ", ".join([f"Table {t['table_number']} (capacity: {t['capacity']})" 
                                        for t in available_tables])
                return f"Available tables for {num_guests} guests on {date} at {time}: {tables_info}"
            else:
                return f"No tables available for {num_guests} guests on {date} at {time}"
                
        except Exception as e:
            return f"Error checking availability: {str(e)}"
    
    def make_reservation(self, date: str, time: str, customer_name: str, 
                        phone: str, num_guests: int, special_requests: str = "") -> str:
        """
        Make a reservation.
        
        Args:
            date: Date in YYYY-MM-DD format
            time: Time in HH:MM format
            customer_name: Customer's name
            phone: Customer's phone number
            num_guests: Number of guests
            special_requests: Any special requests (optional)
            
        Returns:
            Confirmation message or error
        """
        try:
            # Read all rows
            rows = []
            reserved_table = None
            
            with open(self.csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            
            # Find first available table
            for row in rows:
                if (row['date'] == date and 
                    row['time'] == time and 
                    row['status'] == 'available' and 
                    int(row['capacity']) >= num_guests):
                    
                    row['customer_name'] = customer_name
                    row['phone'] = phone
                    row['num_guests'] = str(num_guests)
                    row['status'] = 'booked'
                    row['special_requests'] = special_requests
                    reserved_table = row['table_number']
                    break
            
            if reserved_table:
                # Write back to CSV
                with open(self.csv_file, 'w', newline='', encoding='utf-8') as f:
                    fieldnames = ['date', 'time', 'table_number', 'capacity', 
                                'customer_name', 'phone', 'num_guests', 'status', 
                                'special_requests']
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(rows)
                
                return (f"Reservation confirmed! Table {reserved_table} for {num_guests} guests "
                       f"on {date} at {time} under the name {customer_name}. "
                       f"Phone: {phone}. {f'Special requests: {special_requests}' if special_requests else ''}")
            else:
                return f"Sorry, no tables available for {num_guests} guests on {date} at {time}"
                
        except Exception as e:
            return f"Error making reservation: {str(e)}"
    
    def cancel_reservation(self, date: str, time: str, customer_name: str) -> str:
        """
        Cancel a reservation.
        
        Args:
            date: Date in YYYY-MM-DD format
            time: Time in HH:MM format
            customer_name: Customer's name
            
        Returns:
            Confirmation message or error
        """
        try:
            rows = []
            cancelled = False
            
            with open(self.csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            
            for row in rows:
                if (row['date'] == date and 
                    row['time'] == time and 
                    row['customer_name'].lower() == customer_name.lower() and
                    row['status'] == 'booked'):
                    
                    row['customer_name'] = ''
                    row['phone'] = ''
                    row['num_guests'] = '0'
                    row['status'] = 'available'
                    row['special_requests'] = ''
                    cancelled = True
                    break
            
            if cancelled:
                with open(self.csv_file, 'w', newline='', encoding='utf-8') as f:
                    fieldnames = ['date', 'time', 'table_number', 'capacity', 
                                'customer_name', 'phone', 'num_guests', 'status', 
                                'special_requests']
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(rows)
                
                return f"Reservation for {customer_name} on {date} at {time} has been cancelled"
            else:
                return f"No reservation found for {customer_name} on {date} at {time}"
                
        except Exception as e:
            return f"Error cancelling reservation: {str(e)}"
    
    def view_reservations(self, date: Optional[str] = None) -> str:
        """
        View all reservations, optionally filtered by date.
        
        Args:
            date: Optional date filter in YYYY-MM-DD format
            
        Returns:
            String with reservation details
        """
        try:
            reservations = []
            
            with open(self.csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row['status'] == 'booked':
                        if date is None or row['date'] == date:
                            reservations.append(
                                f"{row['date']} at {row['time']} - Table {row['table_number']}: "
                                f"{row['customer_name']} ({row['num_guests']} guests) - "
                                f"Phone: {row['phone']}"
                                f"{f' - {row["special_requests"]}' if row['special_requests'] else ''}"
                            )
            
            if reservations:
                header = f"Reservations{f' for {date}' if date else ''}:\n"
                return header + "\n".join(reservations)
            else:
                return f"No reservations found{f' for {date}' if date else ''}"
                
        except Exception as e:
            return f"Error viewing reservations: {str(e)}"


# Tool functions for LangChain integration
def check_availability_tool(date: str, time: str, num_guests: int) -> str:
    """Check table availability."""
    tools = ReservationTools()
    return tools.check_availability(date, time, num_guests)

def make_reservation_tool(date: str, time: str, customer_name: str, 
                         phone: str, num_guests: int, special_requests: str = "") -> str:
    """Make a table reservation."""
    tools = ReservationTools()
    return tools.make_reservation(date, time, customer_name, phone, num_guests, special_requests)

def cancel_reservation_tool(date: str, time: str, customer_name: str) -> str:
    """Cancel a table reservation."""
    tools = ReservationTools()
    return tools.cancel_reservation(date, time, customer_name)

def view_reservations_tool(date: str = None) -> str:
    """View all reservations."""
    tools = ReservationTools()
    return tools.view_reservations(date)