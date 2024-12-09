from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

# Configuração do banco de dados SQLite
DATABASE_URL = "sqlite:///./users.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Modelo de tabela do SQLAlchemy
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    senha = Column(String, nullable=False)

# Criar tabelas no banco de dados
Base.metadata.create_all(bind=engine)

# Modelo de entrada/saída do Pydantic
class UserCreate(BaseModel):
    nome: str
    email: EmailStr
    senha: str

class UserResponse(BaseModel):
    id: int
    nome: str
    email: str

    class Config:
        from_attributes = True  # Corrige o aviso do Pydantic v2

# Inicializar a aplicação FastAPI
app = FastAPI()

# Dependência de sessão do banco de dados
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Rota para criar um novo usuário
@app.post("/users/", response_model=UserResponse)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    # Verificar se o e-mail já está cadastrado
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email já cadastrado.")
    
    new_user = User(nome=user.nome, email=user.email, senha=user.senha)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

# Rota para listar todos os usuários
@app.get("/users/", response_model=list[UserResponse])
def get_users(db: Session = Depends(get_db)):
    return db.query(User).all()

# Rota para buscar um usuário por ID
@app.get("/users/{user_id}", response_model=UserResponse)
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")
    return user

# Rota para deletar um usuário
@app.delete("/users/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")
    db.delete(user)
    db.commit()
    return {"detail": "Usuário deletado com sucesso."}
