"""Seed demo data for the Personal Financial Agent.

Creates a demo user and 3 sample financial goals with contributions
to demonstrate the app's functionality.

Usage:
    docker compose exec backend python seed_demo_data.py
"""

import asyncio
import uuid
from datetime import datetime, timezone, timedelta

from app.database import create_tables, async_session
from app.models.user import User
from app.models.goal import Goal


DEMO_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


async def seed():
    """Create demo user and sample goals."""
    await create_tables()

    async with async_session() as db:
        # Check if demo user already exists
        from sqlalchemy import select

        result = await db.execute(select(User).where(User.id == DEMO_USER_ID))
        if result.scalar_one_or_none():
            print("Demo data already exists. Skipping.")
            return

        # Create demo user
        user = User(id=DEMO_USER_ID, name="Demo User", preferred_language="ro")
        db.add(user)
        await db.flush()  # Ensure user exists before creating goals with FK

        # Goal 1: Car — 40% progress
        goal1 = Goal(
            user_id=DEMO_USER_ID,
            name="Mașină nouă",
            icon="🚗",
            target_amount=50000,
            saved_amount=20000,
            monthly_contribution=2000,
            deadline=datetime(2026, 12, 31, tzinfo=timezone.utc),
            priority="high",
            status="active",
            notes="Dacia Duster sau Skoda Octavia",
        )

        # Goal 2: Vacation — 75% progress
        goal2 = Goal(
            user_id=DEMO_USER_ID,
            name="Vacanță Grecia",
            icon="🏖️",
            target_amount=8000,
            saved_amount=6000,
            monthly_contribution=1000,
            deadline=datetime(2026, 7, 1, tzinfo=timezone.utc),
            priority="medium",
            status="active",
        )

        # Goal 3: Emergency fund — 20% progress
        goal3 = Goal(
            user_id=DEMO_USER_ID,
            name="Fond de urgență",
            icon="🛡️",
            target_amount=30000,
            saved_amount=6000,
            monthly_contribution=500,
            priority="high",
            status="active",
            notes="6 luni de cheltuieli",
        )

        db.add_all([goal1, goal2, goal3])
        await db.commit()

        print(f"✅ Demo user created: {user.name} (ID: {DEMO_USER_ID})")
        print(f"✅ 3 goals created:")
        print(f"   🚗 Mașină nouă: 20,000 / 50,000 RON (40%)")
        print(f"   🏖️  Vacanță Grecia: 6,000 / 8,000 RON (75%)")
        print(f"   🛡️  Fond de urgență: 6,000 / 30,000 RON (20%)")


if __name__ == "__main__":
    asyncio.run(seed())
