import os
import logging
from dotenv import load_dotenv

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, Integer, String, Date, Boolean, ForeignKey, Text, select, update, insert, JSON
from sqlalchemy.exc import SQLAlchemyError
from typing import List, Tuple
from sqlalchemy.ext.mutable import MutableList

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./akvamatica.db")

engine = create_async_engine(DATABASE_URL, echo=False, future=True)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, nullable=True)
    first_name = Column(String, nullable=True)
    phone = Column(String, nullable=True)



class Filter(Base):
    __tablename__ = "filters"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    type = Column(String, nullable=False)
    install_date = Column(Date, nullable=False)
    interval = Column(Integer, nullable=False)
    next_reminder_date = Column(Date, nullable=False)
    replace_count = Column(Integer, default=0, nullable=False)
    name = Column(String, default="")  
    history = Column(MutableList.as_mutable(JSON), default=list)
    photos = Column(MutableList.as_mutable(JSON), default=list)

# --- CRM-модели ---
class Client(Base):
    __tablename__ = "clients"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    phone = Column(String, nullable=True)
    comment = Column(Text, nullable=True)

class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    description = Column(Text, nullable=False)
    due_date = Column(Date, nullable=False)
    done = Column(Boolean, default=False)

# --- Инициализация БД ---
async def init_db(app):
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    except Exception as e:
        logging.error(f"Ошибка инициализации БД: {e}")
        raise

# --- CRM-функции ---
async def add_client(name: str, phone: str, comment: str = None):
    try:
        async with async_session() as session:
            async with session.begin():
                client = Client(name=name, phone=phone, comment=comment)
                session.add(client)
            await session.commit()
    except SQLAlchemyError as e:
        logging.error(f"Ошибка добавления клиента: {e}")
        raise

async def get_clients() -> List[Tuple[int, str, str, str]]:
    async with async_session() as session:
        result = await session.execute(select(Client))
        clients = result.scalars().all()
        return [(c.id, c.name, c.phone, c.comment) for c in clients]

async def add_task(client_id, description, due_date):
    async with async_session() as session:
        async with session.begin():
            task = Task(client_id=client_id, description=description, due_date=due_date)
            session.add(task)
        await session.commit()

async def get_tasks():
    async with async_session() as session:
        query = (
            select(Task.id, Client.name, Task.description, Task.due_date, Task.done)
            .join(Client, Client.id == Task.client_id)
        )
        result = await session.execute(query)
        return result.all()

async def mark_task_done(task_id):
    async with async_session() as session:
        await session.execute(update(Task).where(Task.id == task_id).values(done=True))
        await session.commit()

# --- Базовые функции для фильтров ---
async def add_filter(user_id: int, type: str, install_date, interval: int, name: str = ""):
    async with async_session() as session:
        async with session.begin():
            filter_obj = Filter(
                user_id=user_id,
                type=type,
                install_date=install_date,
                interval=interval,
                next_reminder_date=install_date,
                name=name
            )
            session.add(filter_obj)
        await session.commit()

async def get_filters(user_id: int):
    async with async_session() as session:
        result = await session.execute(select(Filter).where(Filter.user_id == user_id))
        filters = result.scalars().all()
        return [f"{f.name or f.type}: установлен {f.install_date}, замена через {f.interval} дней" for f in filters]

async def save_photo(user_id: int, file_path: str):
    async with async_session() as session:
        result = await session.execute(
            select(Filter).where(Filter.user_id == user_id).order_by(Filter.id.desc())
        )
        filter_obj = result.scalars().first()
        if filter_obj:
            filter_obj.photos.append(file_path)
            await session.commit()

