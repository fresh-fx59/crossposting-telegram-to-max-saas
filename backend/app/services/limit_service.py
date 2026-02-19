"""User limit enforcement service."""

import logging
from datetime import datetime, date, timedelta, timezone

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import and_

from ..config import settings
from ..database.models import Connection, DailyPostCount, Post, User

logger = logging.getLogger(__name__)


async def check_connection_limit(
    session: AsyncSession,
    user_id: int,
) -> bool:
    """Check if user can create more connections.

    Args:
        session: Database session
        user_id: User ID

    Returns:
        True if user can create more connections, False otherwise
    """
    # Get user's configured limit
    result = await session.execute(
        select(User.connections_limit).where(User.id == user_id)
    )
    limit = result.scalar_one_or_none()

    if limit is None:
        limit = settings.MAX_CONNECTIONS_PER_USER

    # Count active connections
    result = await session.execute(
        select(func.count(Connection.id)).where(
            Connection.user_id == user_id,
            Connection.is_active.is_(True),
        )
    )
    active_count = result.scalar_one()

    return active_count < limit


async def get_connection_count(
    session: AsyncSession,
    user_id: int,
) -> int:
    """Get the number of active connections for a user.

    Args:
        session: Database session
        user_id: User ID

    Returns:
        Number of active connections
    """
    result = await session.execute(
        select(func.count(Connection.id)).where(
            Connection.user_id == user_id,
            Connection.is_active.is_(True),
        )
    )
    return result.scalar_one()


async def get_remaining_connections(
    session: AsyncSession,
    user_id: int,
) -> int:
    """Get the number of remaining connections a user can create.

    Args:
        session: Database session
        user_id: User ID

    Returns:
        Number of remaining connections (may be 0 or negative)
    """
    result = await session.execute(
        select(User.connections_limit).where(User.id == user_id)
    )
    limit = result.scalar_one_or_none()

    if limit is None:
        limit = settings.MAX_CONNECTIONS_PER_USER

    active_count = await get_connection_count(session, user_id)

    return limit - active_count


async def can_post_to_connection(
    session: AsyncSession,
    connection_id: int,
) -> tuple[bool, int]:
    """Check if a connection can post to Max today (daily limit not exceeded).

    Args:
        session: Database session
        connection_id: Connection ID

    Returns:
        Tuple of (can_post, remaining_count)
    """
    # Get user's configured limit for this connection
    from ..database.models import Connection as Conn

    conn_result = await session.execute(
        select(Conn.user_id).where(Conn.id == connection_id)
    )
    user_id = conn_result.scalar_one_or_none()

    if user_id is None:
        return False, 0

    user_result = await session.execute(
        select(User.daily_posts_limit).where(User.id == user_id)
    )
    limit = user_result.scalar_one_or_none()

    if limit is None:
        limit = settings.MAX_POSTS_PER_DAY_PER_CONNECTION

    # Get today's post count
    today = date.today()

    result = await session.execute(
        select(DailyPostCount.count).where(
            DailyPostCount.connection_id == connection_id,
            DailyPostCount.date == today,
        )
    )
    today_count = result.scalar_one_or_none()

    if today_count is None:
        today_count = 0

    remaining = limit - today_count

    return remaining > 0, remaining


async def increment_post_count(
    session: AsyncSession,
    connection_id: int,
) -> int:
    """Increment the daily post counter for a connection.

    Args:
        session: Database session
        connection_id: Connection ID

    Returns:
        New count for today
    """
    today = date.today()

    # Try to get existing daily count
    result = await session.execute(
        select(DailyPostCount).where(
            DailyPostCount.connection_id == connection_id,
            DailyPostCount.date == today,
        )
    )
    daily_count = result.scalar_one_or_none()

    if daily_count is None:
        # Create new daily counter
        daily_count = DailyPostCount(
            connection_id=connection_id,
            date=today,
            count=1,
        )
        session.add(daily_count)
        await session.flush()
        return 1
    else:
        # Increment existing counter
        daily_count.count += 1
        await session.flush()
        return daily_count.count


async def cleanup_old_post_counts(
    session: AsyncSession,
) -> int:
    """Clean up old daily post counters (older than retention period).

    Args:
        session: Database session

    Returns:
        Number of records deleted
    """
    # We only need to keep counts for the last 2 days
    # (yesterday and today)
    cutoff_date = date.today() - timedelta(days=2)

    result = await session.execute(
        delete(DailyPostCount).where(DailyPostCount.date < cutoff_date)
    )

    deleted_count = result.rowcount
    if deleted_count > 0:
        logger.info("Cleaned up %d old daily post counters", deleted_count)

    return deleted_count


async def cleanup_old_posts(
    session: AsyncSession,
) -> int:
    """Clean up old post history based on success status.

    Args:
        session: Database session

    Returns:
        Number of records deleted
    """
    # Calculate cutoff dates
    success_cutoff = datetime.now(timezone.utc) - timedelta(
        days=settings.POST_HISTORY_RETENTION_DAYS_SUCCESS
    )
    failed_cutoff = datetime.now(timezone.utc) - timedelta(
        days=settings.POST_HISTORY_RETENTION_DAYS_FAILED
    )

    # Delete old success posts
    success_result = await session.execute(
        delete(Post).where(
            and_(
                Post.status == "success",
                Post.created_at < success_cutoff,
            )
        )
    )
    success_deleted = success_result.rowcount

    # Delete old failed posts
    failed_result = await session.execute(
        delete(Post).where(
            and_(
                Post.status == "failed",
                Post.created_at < failed_cutoff,
            )
        )
    )
    failed_deleted = failed_result.rowcount

    total_deleted = success_deleted + failed_deleted

    if total_deleted > 0:
        logger.info(
            "Cleaned up %d old posts (success: %d, failed: %d)",
            total_deleted,
            success_deleted,
            failed_deleted,
        )

    return total_deleted


async def get_post_history(
    session: AsyncSession,
    connection_id: int,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[Post], int]:
    """Get post history for a connection with pagination.

    Args:
        session: Database session
        connection_id: Connection ID
        limit: Maximum number of posts to return
        offset: Offset for pagination

    Returns:
        Tuple of (posts list, total count)
    """
    # Get total count
    count_result = await session.execute(
        select(func.count(Post.id)).where(Post.connection_id == connection_id)
    )
    total = count_result.scalar_one()

    # Get posts
    result = await session.execute(
        select(Post)
        .where(Post.connection_id == connection_id)
        .order_by(Post.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    posts = result.scalars().all()

    return list(posts), total