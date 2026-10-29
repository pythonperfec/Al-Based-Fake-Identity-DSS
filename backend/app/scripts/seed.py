import sys
import os
import asyncio
import logging

# Ensure backend directory is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from sqlalchemy import select
from app.core.config import settings
from app.core.database import AsyncSessionLocal, engine, Base
from app.core.security import get_password_hash
from app.models.user import User

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("seed")


async def seed_users():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        users_to_seed = [
            {
                "username": "officer",
                "email": "officer@demo.com",
                "password": settings.DEMO_OFFICER_PASSWORD,
                "role": "officer"
            },
            {
                "username": "admin",
                "email": "admin@demo.com",
                "password": settings.DEMO_ADMIN_PASSWORD,
                "role": "admin"
            }
        ]

        for user_data in users_to_seed:
            stmt = select(User).where(User.username == user_data["username"])
            result = await session.execute(stmt)
            existing_user = result.scalar_one_or_none()

            if not existing_user:
                new_user = User(
                    username=user_data["username"],
                    email=user_data["email"],
                    hashed_password=get_password_hash(user_data["password"]),
                    role=user_data["role"],
                    is_active=True
                )
                session.add(new_user)
                logger.info(f"Seeded user: {user_data['username']} ({user_data['email']}) with role '{user_data['role']}'")
            else:
                logger.info(f"User already exists: {user_data['username']} ({user_data['email']})")

        await session.commit()
    logger.info("Database seeding completed.")


if __name__ == "__main__":
    asyncio.run(seed_users())
