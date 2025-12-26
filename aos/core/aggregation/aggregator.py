"""
Regional Aggregation
Cross-village data aggregation for regional analytics.
"""
from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta
from typing import Any


class RegionalAggregator:
    """
    Aggregates data across multiple village nodes.
    Provides regional analytics without centralized cloud.
    """

    def __init__(self, db_conn: sqlite3.Connection):
        self.db = db_conn

    def aggregate_harvests(self, days: int = 30) -> list[dict[str, Any]]:
        """
        Aggregate harvest data across all villages for the last N days.
        Returns totals by crop type.
        """
        since = int((datetime.now() - timedelta(days=days)).timestamp())

        cursor = self.db.execute("""
            SELECT 
                crop_type,
                SUM(quantity) as total_quantity,
                COUNT(DISTINCT farmer_id) as farmer_count,
                COUNT(*) as harvest_count
            FROM harvests
            WHERE created_at >= ?
            GROUP BY crop_type
            ORDER BY total_quantity DESC
        """, (since,))

        results = []
        for row in cursor.fetchall():
            results.append({
                "crop_type": row[0],
                "total_quantity": row[1],
                "farmer_count": row[2],
                "harvest_count": row[3]
            })

        return results

    def aggregate_transport(self, days: int = 7) -> list[dict[str, Any]]:
        """
        Aggregate transport bookings for the last N days.
        Returns utilization by route.
        """
        since = int((datetime.now() - timedelta(days=days)).timestamp())

        cursor = self.db.execute("""
            SELECT 
                r.id as route_id,
                r.name as route_name,
                COUNT(b.id) as booking_count,
                SUM(b.passengers) as total_passengers
            FROM routes r
            LEFT JOIN bookings b ON r.id = b.route_id AND b.created_at >= ?
            GROUP BY r.id, r.name
            ORDER BY booking_count DESC
        """, (since,))

        results = []
        for row in cursor.fetchall():
            results.append({
                "route_id": row[0],
                "route_name": row[1],
                "booking_count": row[2] or 0,
                "total_passengers": row[3] or 0
            })

        return results

    def get_village_summary(self) -> dict[str, Any]:
        """
        Get summary statistics for the regional dashboard.
        """
        # Total farmers
        cursor = self.db.execute("SELECT COUNT(*) FROM farmers")
        total_farmers = cursor.fetchone()[0]

        # Total harvests (last 30 days)
        since_30d = int((datetime.now() - timedelta(days=30)).timestamp())
        cursor = self.db.execute(
            "SELECT COUNT(*), SUM(quantity) FROM harvests WHERE created_at >= ?",
            (since_30d,)
        )
        row = cursor.fetchone()
        total_harvests = row[0]
        total_quantity = row[1] or 0

        # Total routes
        cursor = self.db.execute("SELECT COUNT(*) FROM routes")
        total_routes = cursor.fetchone()[0]

        # Total vehicles
        cursor = self.db.execute("SELECT COUNT(*) FROM vehicles")
        total_vehicles = cursor.fetchone()[0]

        return {
            "total_farmers": total_farmers,
            "total_harvests_30d": total_harvests,
            "total_quantity_30d": total_quantity,
            "total_routes": total_routes,
            "total_vehicles": total_vehicles
        }
