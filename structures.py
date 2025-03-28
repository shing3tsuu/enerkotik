from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from typing import Optional, List
from datetime import date
from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint, Float, BigInteger, Date, func

# DB = Postgresql(14)

class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = 'users'
    __table_args__ = (
        UniqueConstraint('tg_id', 'shop_id', name='unique_user_shop'),
    )

    id: Mapped[int] = mapped_column(primary_key=True,)
    tg_id: Mapped[int] = mapped_column(BigInteger)
    name: Mapped[Optional[str]] = mapped_column(String(30))
    shop_id: Mapped[int] = mapped_column(ForeignKey('shops.id'))


class Shop(Base):
    __tablename__ = 'shops'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(unique=True)

    products: Mapped[List['Product']] = relationship(back_populates='shop', cascade='all, delete-orphan')


class Product(Base):
    __tablename__ = 'products'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    cost: Mapped[int]
    update_date: Mapped[date] = mapped_column(Date, server_default=func.now())
    shop_id: Mapped[int] = mapped_column(ForeignKey('shops.id', ondelete='CASCADE'), index=True)

    shop: Mapped['Shop'] = relationship(back_populates='products')
