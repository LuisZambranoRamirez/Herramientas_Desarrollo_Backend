import uuid
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.models import Insumo, InsumoComprado, ConsumoInsumos, Proveedor, AgendaTratamientos, Usuario
from app.schemas.insumo import InsumoCreate, InsumoUpdate, InsumoCompradoCreate, ConsumoInsumosCreate

def listar_insumos(db: Session, current_user: Usuario, stock_bajo: bool = False) -> List[Insumo]:
    query = db.query(Insumo)
    if stock_bajo:
        query = query.filter(Insumo.stock <= Insumo.stock_minimo)
    return query.order_by(Insumo.nombre.asc()).all()

def obtener_insumo_por_id(db: Session, insumo_id: uuid.UUID, current_user: Usuario) -> Insumo:
    insumo = db.query(Insumo).filter(Insumo.insumo_id == insumo_id).first()
    if not insumo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Insumo no encontrado."
        )
    return insumo

def crear_insumo(db: Session, data: InsumoCreate, current_user: Usuario) -> Insumo:
    role_val = current_user.user_role.value if hasattr(current_user.user_role, "value") else str(current_user.user_role)
    if role_val != "SYSTEM_ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo administradores pueden crear insumos."
        )

    existente = db.query(Insumo).filter(Insumo.nombre == data.nombre).first()
    if existente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ya existe un insumo con el nombre '{data.nombre}'."
        )

    nuevo_insumo = Insumo(
        nombre=data.nombre,
        stock=data.stock,
        stock_minimo=data.stock_minimo,
        fecha_vencimiento=data.fecha_vencimiento,
        fecha_registro=datetime.now(timezone.utc)
    )

    try:
        db.add(nuevo_insumo)
        db.commit()
        db.refresh(nuevo_insumo)
        return nuevo_insumo
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ocurrió un error interno al registrar el insumo."
        )

def actualizar_insumo(db: Session, insumo_id: uuid.UUID, data: InsumoUpdate, current_user: Usuario) -> Insumo:
    role_val = current_user.user_role.value if hasattr(current_user.user_role, "value") else str(current_user.user_role)
    if role_val != "SYSTEM_ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo administradores pueden modificar insumos."
        )

    insumo = obtener_insumo_por_id(db, insumo_id, current_user)

    if data.nombre is not None:
        insumo.nombre = data.nombre
    if data.stock is not None:
        insumo.stock = data.stock
    if data.stock_minimo is not None:
        insumo.stock_minimo = data.stock_minimo
    if data.fecha_vencimiento is not None:
        insumo.fecha_vencimiento = data.fecha_vencimiento

    try:
        db.commit()
        db.refresh(insumo)
        return insumo
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ocurrió un error interno al actualizar el insumo."
        )

def eliminar_insumo(db: Session, insumo_id: uuid.UUID, current_user: Usuario) -> None:
    role_val = current_user.user_role.value if hasattr(current_user.user_role, "value") else str(current_user.user_role)
    if role_val != "SYSTEM_ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo administradores pueden eliminar insumos."
        )

    insumo = obtener_insumo_por_id(db, insumo_id, current_user)

    try:
        db.delete(insumo)
        db.commit()
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ocurrió un error interno al eliminar el insumo."
        )

def listar_compras(db: Session, insumo_id: Optional[uuid.UUID], current_user: Usuario) -> List[InsumoComprado]:
    query = db.query(InsumoComprado)
    if insumo_id:
        query = query.filter(InsumoComprado.id_insumo == insumo_id)
    return query.order_by(InsumoComprado.fecha_registro.desc()).all()

def registrar_compra(db: Session, data: InsumoCompradoCreate, current_user: Usuario) -> InsumoComprado:
    role_val = current_user.user_role.value if hasattr(current_user.user_role, "value") else str(current_user.user_role)
    if role_val != "SYSTEM_ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo administradores pueden registrar compras de insumos."
        )

    insumo = db.query(Insumo).filter(Insumo.insumo_id == data.id_insumo).first()
    if not insumo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Insumo no encontrado."
        )

    prov = db.query(Proveedor).filter(Proveedor.ruc == data.id_proveedor).first()
    if not prov:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Proveedor no encontrado."
        )

    # Aumentar stock del insumo
    insumo.stock += data.cantidad

    compra = InsumoComprado(
        id_insumo=data.id_insumo,
        id_proveedor=data.id_proveedor,
        cantidad=data.cantidad,
        precio_unitario=data.precio_unitario,
        fecha_registro=datetime.now(timezone.utc)
    )

    try:
        db.add(compra)
        db.commit()
        db.refresh(compra)
        return compra
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ocurrió un error interno al registrar la compra de insumos."
        )

def listar_consumos(db: Session, current_user: Usuario) -> List[ConsumoInsumos]:
    return db.query(ConsumoInsumos).all()

def registrar_consumo(db: Session, data: ConsumoInsumosCreate, current_user: Usuario) -> ConsumoInsumos:
    role_val = current_user.user_role.value if hasattr(current_user.user_role, "value") else str(current_user.user_role)
    if role_val not in ("SYSTEM_ADMIN", "ODONTOLOGO"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo administradores u odontólogos pueden registrar consumo de insumos."
        )

    insumo = db.query(Insumo).filter(Insumo.insumo_id == data.id_insumo).first()
    if not insumo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Insumo no encontrado."
        )

    if insumo.stock < data.cantidad:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Stock insuficiente. Stock actual: {insumo.stock}"
        )

    agenda = db.query(AgendaTratamientos).filter(AgendaTratamientos.agenda_tratamientos_id == data.id_agenda_tratamiento).first()
    if not agenda:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agenda de tratamiento no encontrada."
        )

    insumo.stock -= data.cantidad

    consumo = ConsumoInsumos(
        id_agenda_tratamiento=data.id_agenda_tratamiento,
        id_insumo=data.id_insumo,
        cantidad=data.cantidad
    )

    try:
        db.add(consumo)
        db.commit()
        db.refresh(consumo)
        return consumo
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ocurrió un error interno al registrar el consumo de insumo."
        )
