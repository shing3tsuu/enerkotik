from sqlalchemy import ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from typing import Optional
from datetime import date
from sqlalchemy import Date

class Base(DeclarativeBase): pass

class UserProduct(Base):
    __tablename__ = 'userproduct'
    product_name: Mapped[int] = mapped_column(ForeignKey('products.name'), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), primary_key=True)
    extra_data: Mapped[Optional[int]]
    products: Mapped['Products'] = relationship(back_populates="users")
    users: Mapped['Users'] = relationship(back_populates="products")


class Products(Base):
    __tablename__ = 'products'
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    cost: Mapped[int]
    shop: Mapped[str]
    update_date: Mapped[date] = mapped_column(Date)
    users: Mapped[list['UserProduct']] = relationship(back_populates="products")


class Users(Base):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(primary_key=True)
    tg_id: Mapped[int]
    name: Mapped[Optional[str]]
    products: Mapped[list['UserProduct']] = relationship( back_populates="users")