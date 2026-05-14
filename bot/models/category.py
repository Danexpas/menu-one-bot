from sqlalchemy import Integer, String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from bot.database.base import Base


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    emoji: Mapped[str] = mapped_column(String(10), nullable=False, default="📦")
    position: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())

    products: Mapped[list] = relationship("Product", back_populates="category", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Category id={self.id} name={self.name}>"
