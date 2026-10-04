from collections import defaultdict
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Response, status
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select
from sqlalchemy.orm import Session

from . import schemas
from .auth import create_token, current_user, hash_password, verify_password
from .database import Base, engine, get_db
from .models import Transaction, User

Base.metadata.create_all(engine)

app = FastAPI(title="Finance Tracker")
STATIC = Path(__file__).resolve().parent.parent / "static"


@app.post("/api/register", response_model=schemas.Token, status_code=201)
def register(body: schemas.Credentials, db: Session = Depends(get_db)):
    if db.scalar(select(User).where(User.username == body.username)):
        raise HTTPException(status.HTTP_409_CONFLICT, "Username already taken")
    user = User(username=body.username, password_hash=hash_password(body.password))
    db.add(user)
    db.commit()
    return schemas.Token(access_token=create_token(user.id))


@app.post("/api/login", response_model=schemas.Token)
def login(body: schemas.Credentials, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.username == body.username))
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Wrong username or password")
    return schemas.Token(access_token=create_token(user.id))


@app.get("/api/transactions", response_model=list[schemas.TransactionOut])
def list_transactions(user: User = Depends(current_user), db: Session = Depends(get_db)):
    q = (
        select(Transaction)
        .where(Transaction.user_id == user.id)
        .order_by(Transaction.date.desc(), Transaction.id.desc())
    )
    return db.scalars(q).all()


@app.post("/api/transactions", response_model=schemas.TransactionOut, status_code=201)
def add_transaction(
    body: schemas.TransactionIn,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    tx = Transaction(user_id=user.id, **body.model_dump())
    db.add(tx)
    db.commit()
    db.refresh(tx)
    return tx


def _own(db: Session, user: User, tx_id: int) -> Transaction:
    tx = db.get(Transaction, tx_id)
    if not tx or tx.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Transaction not found")
    return tx


@app.put("/api/transactions/{tx_id}", response_model=schemas.TransactionOut)
def update_transaction(
    tx_id: int,
    body: schemas.TransactionIn,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    tx = _own(db, user, tx_id)
    for key, value in body.model_dump().items():
        setattr(tx, key, value)
    db.commit()
    db.refresh(tx)
    return tx


@app.delete("/api/transactions/{tx_id}", status_code=204)
def delete_transaction(
    tx_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)
):
    db.delete(_own(db, user, tx_id))
    db.commit()
    return Response(status_code=204)


@app.get("/api/summary", response_model=schemas.Summary)
def summary(user: User = Depends(current_user), db: Session = Depends(get_db)):
    income = expense = 0.0
    by_category: dict[str, float] = defaultdict(float)
    by_month: dict[str, dict[str, float]] = defaultdict(lambda: {"income": 0.0, "expense": 0.0})
    for tx in db.scalars(select(Transaction).where(Transaction.user_id == user.id)):
        by_month[tx.date.strftime("%Y-%m")][tx.kind] += tx.amount
        if tx.kind == "income":
            income += tx.amount
        else:
            expense += tx.amount
            by_category[tx.category] += tx.amount
    return schemas.Summary(
        income=income,
        expense=expense,
        balance=income - expense,
        by_category=dict(by_category),
        by_month=dict(sorted(by_month.items())),
    )


@app.get("/")
def index():
    return FileResponse(STATIC / "index.html")


app.mount("/static", StaticFiles(directory=STATIC), name="static")
