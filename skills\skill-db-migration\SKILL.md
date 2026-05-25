---
name: skill-db-migration
description: "Database migration and ORM patterns distilled from sqlalchemy/sqlalchemy + alembic — schema changes, seeding, rollback."
---

# Database Migration & ORM

Distilled from [sqlalchemy/sqlalchemy](https://github.com/sqlalchemy/sqlalchemy) + Alembic. Manage schema evolution with version-controlled migrations.

## Migration Workflow

```
1. Define/update ORM model  →  models.py
2. Auto-generate migration  →  alembic revision --autogenerate -m "add user.avatar"
3. Review generated SQL     →  check upgrade()/downgrade()
4. Apply                    →  alembic upgrade head
5. Verify                   →  SELECT on new columns
6. Rollback if needed       →  alembic downgrade -1
```

## ORM Model Template

```python
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Index, create_engine
from sqlalchemy.orm import DeclarativeBase, relationship, Session
from datetime import datetime

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        Index("idx_users_email", "email", unique=True),
        Index("idx_users_created", "created_at"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), nullable=False, unique=True)
    name = Column(String(100), nullable=False)
    avatar_url = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    posts = relationship("Post", back_populates="author", cascade="all, delete-orphan")

class Post(Base):
    __tablename__ = "posts"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(200), nullable=False)
    body = Column(Text, nullable=False)
    author = relationship("User", back_populates="posts")
```

## Migration Example (Alembic)

```python
# alembic/versions/xxxx_add_avatar.py
def upgrade():
    op.add_column("users", sa.Column("avatar_url", sa.Text(), nullable=True))
    op.create_index("idx_users_avatar", "users", ["avatar_url"])

def downgrade():
    op.drop_index("idx_users_avatar")
    op.drop_column("users", "avatar_url")
```

## Seed / Reset

```python
def seed(session: Session):
    if session.query(User).count() > 0:
        return  # already seeded
    users = [User(email=f"user{i}@test.com", name=f"User {i}") for i in range(1, 11)]
    session.add_all(users)
    session.commit()

def reset():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    seed(Session(engine))
```

## Query Patterns

```python
# Filter + order
User.query.filter(User.email.like("%@test.com")).order_by(User.created_at.desc()).limit(10).all()

# Join
query = session.query(User, Post).join(Post, User.id == Post.user_id).filter(Post.title.contains("hello"))

# Bulk insert
session.bulk_insert_mappings(User, [{"email": "...", "name": "..."} for _ in range(1000)])

# Atomic update
session.query(User).filter(User.id == uid).update({"name": "new"}, synchronize_session="fetch")
session.commit()
```

## Anti-patterns
- Don't use auto-migration in production — always review generated SQL
- Don't skip downgrade() — needed for rollback
- Don't use `autoincrement` with UUID primary keys