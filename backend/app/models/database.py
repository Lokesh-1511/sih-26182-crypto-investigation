# backend/app/models/database.py
import os
import json
from datetime import datetime
from typing import Any, Dict, List, Optional

try:
    from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey
    from sqlalchemy.orm import declarative_base, sessionmaker, relationship, Session
    HAS_SQLALCHEMY = True
except ImportError:
    HAS_SQLALCHEMY = False

if HAS_SQLALCHEMY:
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./crypto_investigation.db")
    connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
    engine = create_engine(DATABASE_URL, connect_args=connect_args)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base = declarative_base()

    def get_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()
else:
    Session = Any

    # Zero-dependency in-memory/standard-library fallback
    class MockColumn:
        def __init__(self, *args, **kwargs):
            self.args = args
            self.kwargs = kwargs
            self.primary_key = kwargs.get("primary_key", False)
            self.name = kwargs.get("name", None)

        def desc(self):
            return self

        def asc(self):
            return self

        def like(self, *args, **kwargs):
            return self

        def in_(self, *args, **kwargs):
            return self

        def is_(self, *args, **kwargs):
            return self

        def isnot(self, *args, **kwargs):
            return self

        def __repr__(self):
            return "<MockColumn>"

    Column = MockColumn
    Integer = String = Float = DateTime = Boolean = Text = ForeignKey = MockColumn

    def relationship(*args, **kwargs):
        return None

    class MockMetadata:
        def create_all(self, bind=None):
            pass
        def drop_all(self, bind=None):
            pass

    class MockBase:
        metadata = MockMetadata()
        def __init__(self, **kwargs):
            # Assign defaults defined on the model class columns
            for attr_name, attr_val in type(self).__dict__.items():
                if isinstance(attr_val, MockColumn):
                    d = attr_val.kwargs.get("default")
                    if d is not None:
                        val = d() if callable(d) else d
                        setattr(self, attr_name, val)
                    else:
                        setattr(self, attr_name, None)
            for k, v in kwargs.items():
                setattr(self, k, v)

    Base = MockBase
    engine = None

    class MockQuery:
        def __init__(self, model_class, storage):
            self.model_class = model_class
            self.storage = storage
            self.items = storage.get(model_class, [])

        def filter_by(self, **kwargs):
            res = []
            for item in self.items:
                match = True
                for k, v in kwargs.items():
                    if getattr(item, k, None) != v:
                        match = False
                        break
                if match:
                    res.append(item)
            q = MockQuery(self.model_class, self.storage)
            q.items = res
            return q

        def order_by(self, *args):
            # Sort items by created_at or id in reverse if possible
            try:
                self.items.sort(
                    key=lambda x: str(getattr(x, "created_at", None) or getattr(x, "id", "")),
                    reverse=True
                )
            except Exception:
                pass
            return self

        def all(self):
            return list(self.items)

        def first(self):
            return self.items[0] if self.items else None

    class MockSession:
        _global_storage: Dict[Any, List[Any]] = {}
        _initialized: bool = False

        def __init__(self):
            self.storage = MockSession._global_storage
            self._ensure_seed_data()

        def _ensure_seed_data(self):
            if MockSession._initialized:
                return
            MockSession._initialized = True
            
            # Auto-seed demo cases if available
            base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
            cases_dir = os.path.join(base_dir, "data", "demo", "cases")
            if os.path.exists(cases_dir):
                from .entities import CaseModel
                for fname in os.listdir(cases_dir):
                    if fname.endswith(".json"):
                        fpath = os.path.join(cases_dir, fname)
                        try:
                            with open(fpath, "r", encoding="utf-8") as f:
                                cdata = json.load(f)
                                cid = cdata.get("case_id")
                                if cid:
                                    cm = CaseModel(
                                        id=cid,
                                        title=cdata.get("title", "Demo Case"),
                                        investigator=cdata.get("investigator", "Investigator"),
                                        description=cdata.get("description"),
                                        status="OPEN",
                                        priority=cdata.get("priority", "MEDIUM"),
                                        suspect_wallet=cdata.get("suspect_wallet"),
                                        chain=cdata.get("chain", "ETH"),
                                        created_at=datetime.utcnow()
                                    )
                                    self.add(cm)
                        except Exception as e:
                            print(f"Error auto-seeding demo case {fname}: {e}")

        def query(self, model_class):
            return MockQuery(model_class, self.storage)

        def add(self, obj):
            cls = type(obj)
            if cls not in self.storage:
                self.storage[cls] = []
            if obj not in self.storage[cls]:
                self.storage[cls].append(obj)

        def commit(self):
            pass

        def refresh(self, obj):
            pass

        def close(self):
            pass

    SessionLocal = MockSession

    def get_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()
