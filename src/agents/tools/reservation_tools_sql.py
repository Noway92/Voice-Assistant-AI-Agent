from sqlalchemy.orm import Session
from datetime import datetime, date
from typing import List, Optional, Dict
from ..database.db_config import SessionLocal
from ..database.database import Reservation, Table, Client


class ReservationToolsSQL:
    """Tools for managing restaurant reservations with PostgreSQL."""

    @staticmethod
    def check_availability(date_str: str, time: str, num_guests: int) -> str:
        """
        Check available tables for a specific date, time and number of guests.

        Args:
            date_str: Date in YYYY-MM-DD format
            time: Time in HH:MM format
            num_guests: Number of guests

        Returns:
            String describing availability
        """
        db: Session = SessionLocal()
        try:
            # Convert date string to date object
            reservation_date = datetime.strptime(date_str, "%Y-%m-%d").date()

            # Find available tables
            available_table = ReservationToolsSQL._find_available_table(
                db, reservation_date, time, num_guests
            )

            if available_table:
                # Get all tables that could fit this party
                suitable_tables = db.query(Table).filter(
                    Table.capacity >= num_guests,
                    Table.is_active == True
                ).all()

                available_tables = []
                for table in suitable_tables:
                    if not ReservationToolsSQL._is_table_reserved(db, table.id, reservation_date, time):
                        available_tables.append(table)

                tables_info = ", ".join([f"Table {t.table_number} (capacity: {t.capacity})"
                                        for t in available_tables])
                return f"Available tables for {num_guests} guests on {date_str} at {time}: {tables_info}"
            else:
                return f"No tables available for {num_guests} guests on {date_str} at {time}"

        except ValueError:
            return "Invalid date format. Please use YYYY-MM-DD"
        except Exception as e:
            return f"Error checking availability: {str(e)}"
        finally:
            db.close()

    @staticmethod
    def make_reservation(
        date_str: str,
        time: str,
        customer_name: str,
        phone: str,
        num_guests: int,
        special_requests: str = ""
    ) -> str:
        """
        Make a reservation.

        Args:
            date_str: Date in YYYY-MM-DD format
            time: Time in HH:MM format
            customer_name: Customer's name
            phone: Customer's phone number
            num_guests: Number of guests
            special_requests: Any special requests (optional)

        Returns:
            Confirmation message or error
        """
        db: Session = SessionLocal()
        try:
            # Convert date string to date object
            reservation_date = datetime.strptime(date_str, "%Y-%m-%d").date()

            # Find or create client
            client = db.query(Client).filter(Client.phone == phone).first()
            if not client:
                client = Client(name=customer_name, phone=phone)
                db.add(client)
                db.flush()  # Get the client ID

            # Find available table
            available_table = ReservationToolsSQL._find_available_table(
                db, reservation_date, time, num_guests
            )

            if not available_table:
                return f"Sorry, no tables available for {num_guests} guests on {date_str} at {time}"

            # Create reservation
            reservation = Reservation(
                client_id=client.id,
                table_id=available_table.id,
                date=reservation_date,
                time=time,
                num_guests=num_guests,
                status="booked",
                special_requests=special_requests if special_requests else None
            )

            db.add(reservation)
            db.commit()

            return (f"Reservation confirmed! Table {available_table.table_number} for {num_guests} guests "
                   f"on {date_str} at {time} under the name {customer_name}. "
                   f"Phone: {phone}. {f'Special requests: {special_requests}' if special_requests else ''}")

        except ValueError:
            db.rollback()
            return "Invalid date format. Please use YYYY-MM-DD"
        except Exception as e:
            db.rollback()
            return f"Error making reservation: {str(e)}"
        finally:
            db.close()

    @staticmethod
    def cancel_reservation(date_str: str, time: str, customer_name: str) -> str:
        """
        Cancel a reservation.

        Args:
            date_str: Date in YYYY-MM-DD format
            time: Time in HH:MM format
            customer_name: Customer's name

        Returns:
            Confirmation message or error
        """
        db: Session = SessionLocal()
        try:
            # Convert date string to date object
            reservation_date = datetime.strptime(date_str, "%Y-%m-%d").date()

            # Find the reservation
            reservation = (
                db.query(Reservation)
                .join(Client)
                .filter(
                    Reservation.date == reservation_date,
                    Reservation.time == time,
                    Client.name.ilike(f"%{customer_name}%"),
                    Reservation.status == "booked"
                )
                .first()
            )

            if not reservation:
                return f"No reservation found for {customer_name} on {date_str} at {time}"

            reservation.status = "cancelled"
            db.commit()

            return f"Reservation for {customer_name} on {date_str} at {time} has been cancelled"

        except ValueError:
            return "Invalid date format. Please use YYYY-MM-DD"
        except Exception as e:
            db.rollback()
            return f"Error cancelling reservation: {str(e)}"
        finally:
            db.close()

    @staticmethod
    def view_reservations(date_str: Optional[str] = None) -> str:
        """
        View all reservations, optionally filtered by date.

        Args:
            date_str: Optional date filter in YYYY-MM-DD format

        Returns:
            String with reservation details
        """
        db: Session = SessionLocal()
        try:
            query = (
                db.query(Reservation, Client, Table)
                .join(Client, Reservation.client_id == Client.id)
                .join(Table, Reservation.table_id == Table.id)
                .filter(Reservation.status == "booked")
            )

            if date_str:
                reservation_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                query = query.filter(Reservation.date == reservation_date)

            results = query.order_by(Reservation.date, Reservation.time).all()

            if not results:
                return f"No reservations found{f' for {date_str}' if date_str else ''}"

            reservations = []
            for reservation, client, table in results:
                date_formatted = reservation.date.strftime("%Y-%m-%d")
                reservations.append(
                    f"{date_formatted} at {reservation.time} - Table {table.table_number}: "
                    f"{client.name} ({reservation.num_guests} guests) - "
                    f"Phone: {client.phone}"
                    f"{f' - {reservation.special_requests}' if reservation.special_requests else ''}"
                )

            header = f"Reservations{f' for {date_str}' if date_str else ''}:\n"
            return header + "\n".join(reservations)

        except ValueError:
            return "Invalid date format. Please use YYYY-MM-DD"
        except Exception as e:
            return f"Error viewing reservations: {str(e)}"
        finally:
            db.close()

    @staticmethod
    def get_reservations_by_phone(phone: str) -> List[Dict]:
        """Get all reservations for a specific phone number."""
        db: Session = SessionLocal()
        try:
            client = db.query(Client).filter(Client.phone == phone).first()
            if not client:
                return []

            reservations = (
                db.query(Reservation, Table)
                .join(Table, Reservation.table_id == Table.id)
                .filter(
                    Reservation.client_id == client.id,
                    Reservation.status == "booked"
                )
                .order_by(Reservation.date.desc(), Reservation.time.desc())
                .all()
            )

            return [
                {
                    "id": r.id,
                    "date": r.date.strftime("%Y-%m-%d"),
                    "time": r.time,
                    "num_guests": r.num_guests,
                    "table_number": t.table_number,
                    "status": r.status,
                    "special_requests": r.special_requests
                }
                for r, t in reservations
            ]
        finally:
            db.close()

    @staticmethod
    def _find_available_table(
        db: Session,
        date: date,
        time: str,
        num_guests: int
    ) -> Optional[Table]:
        """Find an available table for the given criteria."""
        # Get all tables with sufficient capacity
        suitable_tables = db.query(Table).filter(
            Table.capacity >= num_guests,
            Table.is_active == True
        ).order_by(Table.capacity).all()  # Order by capacity to get smallest suitable table

        # Check each table for availability
        for table in suitable_tables:
            if not ReservationToolsSQL._is_table_reserved(db, table.id, date, time):
                return table

        return None

    @staticmethod
    def _is_table_reserved(db: Session, table_id: int, date: date, time: str) -> bool:
        """Check if a table is already reserved for a specific date and time."""
        existing_reservation = db.query(Reservation).filter(
            Reservation.table_id == table_id,
            Reservation.date == date,
            Reservation.time == time,
            Reservation.status == "booked"
        ).first()

        return existing_reservation is not None


# Tool functions for LangChain/agent integration
def check_availability_tool(date: str, time: str, num_guests: int) -> str:
    """Check table availability."""
    return ReservationToolsSQL.check_availability(date, time, num_guests)


def make_reservation_tool(
    date: str,
    time: str,
    customer_name: str,
    phone: str,
    num_guests: int,
    special_requests: str = ""
) -> str:
    """Make a table reservation."""
    return ReservationToolsSQL.make_reservation(
        date, time, customer_name, phone, num_guests, special_requests
    )


def cancel_reservation_tool(date: str, time: str, customer_name: str) -> str:
    """Cancel a table reservation."""
    return ReservationToolsSQL.cancel_reservation(date, time, customer_name)


def view_reservations_tool(date: str = None) -> str:
    """View all reservations."""
    return ReservationToolsSQL.view_reservations(date)