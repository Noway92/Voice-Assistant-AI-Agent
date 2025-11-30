"""
Test script for PostgreSQL reservation tools.
This script demonstrates all the functionality of the reservation system.
"""

import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from agents.tools.reservation_tools_sql import ReservationToolsSQL


def test_reservation_system():
    """Test all reservation system functionality."""
    print("=" * 60)
    print("Testing PostgreSQL Reservation System")
    print("=" * 60)

    # Test 1: Check availability
    print("\n[TEST 1] Checking availability for 2025-12-01 at 19:00 for 4 guests")
    result = ReservationToolsSQL.check_availability("2025-12-01", "19:00", 4)
    print(result)

    # Test 2: Make a reservation
    print("\n[TEST 2] Making a reservation")
    result = ReservationToolsSQL.make_reservation(
        date_str="2025-12-01",
        time="19:00",
        customer_name="Test Customer",
        phone="0700000000",
        num_guests=4,
        special_requests="Test reservation - can be deleted"
    )
    print(result)

    # Test 3: View all reservations
    print("\n[TEST 3] Viewing all reservations")
    result = ReservationToolsSQL.view_reservations()
    print(result)

    # Test 4: View reservations for specific date
    print("\n[TEST 4] Viewing reservations for 2025-12-01")
    result = ReservationToolsSQL.view_reservations("2025-12-01")
    print(result)

    # Test 5: Get reservations by phone
    print("\n[TEST 5] Getting reservations for phone 0700000000")
    reservations = ReservationToolsSQL.get_reservations_by_phone("0700000000")
    print(f"Found {len(reservations)} reservations")
    for res in reservations:
        print(f"  - {res['date']} at {res['time']}: Table {res['table_number']}, {res['num_guests']} guests")

    # Test 6: Cancel a reservation
    print("\n[TEST 6] Cancelling the test reservation")
    result = ReservationToolsSQL.cancel_reservation("2025-12-01", "19:00", "Test Customer")
    print(result)

    # Test 7: Verify cancellation
    print("\n[TEST 7] Verifying cancellation")
    result = ReservationToolsSQL.view_reservations("2025-12-01")
    print(result)

    print("\n" + "=" * 60)
    print("[SUCCESS] All tests completed!")
    print("=" * 60)


if __name__ == "__main__":
    try:
        test_reservation_system()
    except Exception as e:
        print(f"\n[ERROR] Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
