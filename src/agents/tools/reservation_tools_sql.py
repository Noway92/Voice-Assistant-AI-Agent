from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Optional, Dict
from ..database.db_config import SessionLocal
from ..database.database import Reservation, Table

class ReservationTools:
    """Tools pour gérer les réservations."""
    
    @staticmethod
    def create_reservation(
        customer_name: str,
        customer_phone: str,
        date: str,
        time: str,
        number_of_people: int,
        customer_email: Optional[str] = None,
        special_requests: Optional[str] = None
    ) -> Dict:
        """Créer une nouvelle réservation."""
        db: Session = SessionLocal()
        try:
            # Convertir la date
            reservation_date = datetime.strptime(date, "%Y-%m-%d")
            
            # Vérifier la disponibilité
            available_table = ReservationTools.find_available_table(
                db, reservation_date, time, number_of_people
            )
            
            if not available_table:
                return {
                    "success": False,
                    "message": "Aucune table disponible pour cette date et heure."
                }
            
            # Créer la réservation
            reservation = Reservation(
                customer_name=customer_name,
                customer_phone=customer_phone,
                customer_email=customer_email,
                date=reservation_date,
                time=time,
                number_of_people=number_of_people,
                table_number=available_table.table_number,
                special_requests=special_requests,
                status="confirmed"
            )
            
            db.add(reservation)
            db.commit()
            db.refresh(reservation)
            
            return {
                "success": True,
                "message": f"Réservation confirmée pour {customer_name}",
                "reservation_id": reservation.id,
                "table_number": reservation.table_number,
                "date": date,
                "time": time
            }
            
        except Exception as e:
            db.rollback()
            return {"success": False, "message": f"Erreur: {str(e)}"}
        finally:
            db.close()
    
    @staticmethod
    def find_available_table(
        db: Session,
        date: datetime,
        time: str,
        number_of_people: int
    ) -> Optional[Table]:
        """Trouver une table disponible."""
        # Récupérer les tables avec capacité suffisante
        suitable_tables = db.query(Table).filter(
            Table.capacity >= number_of_people,
            Table.is_available == True
        ).all()
        
        # Vérifier les réservations existantes
        for table in suitable_tables:
            existing_reservation = db.query(Reservation).filter(
                Reservation.table_number == table.table_number,
                Reservation.date == date,
                Reservation.time == time,
                Reservation.status.in_(["pending", "confirmed"])
            ).first()
            
            if not existing_reservation:
                return table
        
        return None
    
    @staticmethod
    def get_reservation_by_phone(customer_phone: str) -> List[Dict]:
        """Récupérer les réservations par numéro de téléphone."""
        db: Session = SessionLocal()
        try:
            reservations = db.query(Reservation).filter(
                Reservation.customer_phone == customer_phone,
                Reservation.status != "cancelled"
            ).order_by(Reservation.date.desc()).all()
            
            return [
                {
                    "id": r.id,
                    "customer_name": r.customer_name,
                    "date": r.date.strftime("%Y-%m-%d"),
                    "time": r.time,
                    "number_of_people": r.number_of_people,
                    "table_number": r.table_number,
                    "status": r.status
                }
                for r in reservations
            ]
        finally:
            db.close()
    
    @staticmethod
    def cancel_reservation(reservation_id: int) -> Dict:
        """Annuler une réservation."""
        db: Session = SessionLocal()
        try:
            reservation = db.query(Reservation).filter(
                Reservation.id == reservation_id
            ).first()
            
            if not reservation:
                return {"success": False, "message": "Réservation non trouvée"}
            
            reservation.status = "cancelled"
            db.commit()
            
            return {
                "success": True,
                "message": f"Réservation #{reservation_id} annulée avec succès"
            }
        except Exception as e:
            db.rollback()
            return {"success": False, "message": f"Erreur: {str(e)}"}
        finally:
            db.close()
    
    @staticmethod
    def update_reservation(
        reservation_id: int,
        date: Optional[str] = None,
        time: Optional[str] = None,
        number_of_people: Optional[int] = None
    ) -> Dict:
        """Modifier une réservation."""
        db: Session = SessionLocal()
        try:
            reservation = db.query(Reservation).filter(
                Reservation.id == reservation_id
            ).first()
            
            if not reservation:
                return {"success": False, "message": "Réservation non trouvée"}
            
            if date:
                reservation.date = datetime.strptime(date, "%Y-%m-%d")
            if time:
                reservation.time = time
            if number_of_people:
                reservation.number_of_people = number_of_people
            
            db.commit()
            
            return {
                "success": True,
                "message": "Réservation modifiée avec succès",
                "reservation_id": reservation_id
            }
        except Exception as e:
            db.rollback()
            return {"success": False, "message": f"Erreur: {str(e)}"}
        finally:
            db.close()