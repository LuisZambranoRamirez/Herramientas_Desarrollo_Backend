from datetime import datetime, date, time
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload

from app.database.connection import get_db
from app.models.usuario import Usuario
from app.models.cita import Cita, EstadoCita
from app.models.paciente import Paciente
from app.models.odontologo import Odontologo
from app.models.personal import Personal
from app.routers.auth import get_current_user
from app.schemas.cita import (
    CitaCreate, 
    CitaUpdate, 
    CitaEstadoUpdate, 
    CitaResponse, 
    OdontologoSimpleResponse
)

router = APIRouter(prefix="/citas", tags=["Citas Odontológicas"])

def format_cita_response(cita: Cita) -> dict:
    """Transforma un modelo Cita a diccionario con datos de relaciones."""
    paciente_data = None
    if cita.paciente:
        paciente_data = {
            "dni": cita.paciente.dni,
            "nombres": cita.paciente.nombres,
            "apellidos": cita.paciente.apellidos,
            "telefono": cita.paciente.telefono,
            "correo": cita.paciente.correo
        }
        
    odontologo_data = None
    if cita.odontologo:
        esp = (
            cita.odontologo.especialidad.value 
            if hasattr(cita.odontologo.especialidad, "value") 
            else str(cita.odontologo.especialidad)
        )
        nombres = cita.odontologo.personal.nombres if cita.odontologo.personal else ""
        apellidos = cita.odontologo.personal.apellidos if cita.odontologo.personal else ""
        odontologo_data = {
            "dni": cita.odontologo.dni,
            "nombres": nombres,
            "apellidos": apellidos,
            "especialidad": esp,
            "colegiatura": cita.odontologo.colegiatura
        }
        
    return {
        "cita_id": str(cita.cita_id),
        "dni_paciente": cita.dni_paciente,
        "dni_odontologo": cita.dni_odontologo,
        "fecha": cita.fecha,
        "hora": cita.hora,
        "motivo_consulta": cita.motivo_consulta,
        "diagnostico": cita.diagnostico,
        "estado": (
            cita.estado.value 
            if hasattr(cita.estado, "value") 
            else str(cita.estado)
        ),
        "fecha_registro": cita.fecha_registro,
        "paciente": paciente_data,
        "odontologo": odontologo_data
    }

@router.get("/odontologos", response_model=List[OdontologoSimpleResponse])
def listar_odontologos_disponibles(db: Session = Depends(get_db)):
    """
    Lista todos los odontólogos registrados y activos para seleccionar al agendar citas.
    """
    odontologos = (
        db.query(Odontologo)
        .join(Personal, Odontologo.dni == Personal.dni)
        .filter(Personal.activo == True)
        .all()
    )
    
    resultado = []
    for o in odontologos:
        esp = o.especialidad.value if hasattr(o.especialidad, "value") else str(o.especialidad)
        resultado.append({
            "dni": o.dni,
            "nombres": o.personal.nombres if o.personal else "",
            "apellidos": o.personal.apellidos if o.personal else "",
            "especialidad": esp,
            "colegiatura": o.colegiatura
        })
    return resultado

@router.post("", response_model=CitaResponse, status_code=status.HTTP_201_CREATED)
def agendar_cita(
    data: CitaCreate, 
    current_user: Usuario = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    """
    Agenda una nueva cita odontológica.
    - Si el usuario es rol PACIENTE, se enlaza automáticamente a su DNI.
    - Si es ADMIN u ODONTOLOGO, requiere el campo 'dni_paciente'.
    """
    # 1. Determinar DNI del paciente
    if current_user.user_role == "PACIENTE":
        paciente = db.query(Paciente).filter(Paciente.username == current_user.username).first()
        if not paciente:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No se encontró el registro de paciente asociado a este usuario"
            )
        dni_paciente = paciente.dni
    else:
        if not data.dni_paciente:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Se debe proporcionar el DNI del paciente"
            )
        paciente = db.query(Paciente).filter(Paciente.dni == data.dni_paciente).first()
        if not paciente:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No existe ningún paciente con DNI {data.dni_paciente}"
            )
        dni_paciente = data.dni_paciente

    # 2. Validar que el odontólogo exista
    odontologo = db.query(Odontologo).filter(Odontologo.dni == data.dni_odontologo).first()
    if not odontologo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El odontólogo seleccionado no existe"
        )

    # 3. Validar disponibilidad de horario (evitar doble cita al mismo odontólogo)
    conflicto = db.query(Cita).filter(
        Cita.dni_odontologo == data.dni_odontologo,
        Cita.fecha == data.fecha,
        Cita.hora == data.hora,
        Cita.estado.notin_(["CANCELADA", "NO_ASISTIO"])
    ).first()
    
    if conflicto:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El odontólogo ya tiene una cita programada para esa fecha y hora"
        )

    # 4. Crear la cita
    nueva_cita = Cita(
        dni_paciente=dni_paciente,
        dni_odontologo=data.dni_odontologo,
        fecha=data.fecha,
        hora=data.hora,
        motivo_consulta=data.motivo_consulta,
        estado=EstadoCita.PROGRAMADA.value,
        fecha_registro=datetime.utcnow()
    )

    db.add(nueva_cita)
    db.commit()
    db.refresh(nueva_cita)

    return format_cita_response(nueva_cita)

@router.get("/mis-citas", response_model=List[CitaResponse])
def mis_citas(
    current_user: Usuario = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    """
    Retorna el listado de citas del usuario conectado:
    - Pacientes ven sus citas médicas agendadas.
    - Odontólogos ven las citas asignadas a ellos.
    - Administradores ven todas las citas.
    """
    query = (
        db.query(Cita)
        .options(
            joinedload(Cita.paciente),
            joinedload(Cita.odontologo).joinedload(Odontologo.personal)
        )
    )

    if current_user.user_role == "PACIENTE":
        paciente = db.query(Paciente).filter(Paciente.username == current_user.username).first()
        if not paciente:
            return []
        citas = query.filter(Cita.dni_paciente == paciente.dni).order_by(Cita.fecha.desc(), Cita.hora.desc()).all()
    elif current_user.user_role == "ODONTOLOGO":
        odontologo = db.query(Odontologo).filter(Odontologo.username == current_user.username).first()
        if not odontologo:
            return []
        citas = query.filter(Cita.dni_odontologo == odontologo.dni).order_by(Cita.fecha.desc(), Cita.hora.desc()).all()
    else:
        # Administrador
        citas = query.order_by(Cita.fecha.desc(), Cita.hora.desc()).all()

    return [format_cita_response(c) for c in citas]

@router.get("", response_model=List[CitaResponse])
def listar_todas_las_citas(
    fecha: Optional[date] = Query(None, description="Filtrar por fecha"),
    estado: Optional[str] = Query(None, description="Filtrar por estado"),
    dni_paciente: Optional[str] = Query(None, description="Filtrar por DNI paciente"),
    dni_odontologo: Optional[str] = Query(None, description="Filtrar por DNI odontólogo"),
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Listado general de citas con filtros para administración y personal clínico.
    """
    query = (
        db.query(Cita)
        .options(
            joinedload(Cita.paciente),
            joinedload(Cita.odontologo).joinedload(Odontologo.personal)
        )
    )

    # Si es paciente, solo puede ver las suyas
    if current_user.user_role == "PACIENTE":
        paciente = db.query(Paciente).filter(Paciente.username == current_user.username).first()
        if not paciente:
            return []
        query = query.filter(Cita.dni_paciente == paciente.dni)
    else:
        if dni_paciente:
            query = query.filter(Cita.dni_paciente == dni_paciente)
        if dni_odontologo:
            query = query.filter(Cita.dni_odontologo == dni_odontologo)

    if fecha:
        query = query.filter(Cita.fecha == fecha)
    if estado:
        query = query.filter(Cita.estado == estado.upper())

    citas = query.order_by(Cita.fecha.desc(), Cita.hora.desc()).all()
    return [format_cita_response(c) for c in citas]

@router.get("/{cita_id}", response_model=CitaResponse)
def obtener_detalle_cita(
    cita_id: str,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtiene los datos detallados de una cita."""
    cita = (
        db.query(Cita)
        .options(
            joinedload(Cita.paciente),
            joinedload(Cita.odontologo).joinedload(Odontologo.personal)
        )
        .filter(Cita.cita_id == cita_id)
        .first()
    )
    if not cita:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cita no encontrada"
        )

    # Validación de permisos: un paciente solo puede ver su propia cita
    if current_user.user_role == "PACIENTE":
        paciente = db.query(Paciente).filter(Paciente.username == current_user.username).first()
        if not paciente or cita.dni_paciente != paciente.dni:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para ver esta cita"
            )

    return format_cita_response(cita)

@router.patch("/{cita_id}/estado", response_model=CitaResponse)
def actualizar_estado_cita(
    cita_id: str,
    data: CitaEstadoUpdate,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Actualiza el estado de una cita (CONFIRMADA, ATENDIDA, CANCELADA, etc.).
    """
    cita = db.query(Cita).filter(Cita.cita_id == cita_id).first()
    if not cita:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cita no encontrada"
        )

    # Validar permisos
    if current_user.user_role == "PACIENTE":
        paciente = db.query(Paciente).filter(Paciente.username == current_user.username).first()
        if not paciente or cita.dni_paciente != paciente.dni:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para modificar esta cita"
            )
        # Los pacientes solo pueden cancelar su cita
        if data.estado.upper() != "CANCELADA":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Los pacientes solo pueden cancelar sus citas"
            )

    estado_upper = data.estado.upper()
    if estado_upper not in EstadoCita.__members__:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Estado inválido. Opciones permitidas: {list(EstadoCita.__members__.keys())}"
        )

    cita.estado = estado_upper
    if data.diagnostico:
        cita.diagnostico = data.diagnostico

    db.commit()
    db.refresh(cita)
    return format_cita_response(cita)

@router.patch("/{cita_id}/cancelar", response_model=CitaResponse)
def cancelar_cita(
    cita_id: str,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Cancela una cita de forma directa.
    """
    cita = db.query(Cita).filter(Cita.cita_id == cita_id).first()
    if not cita:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cita no encontrada"
        )

    if current_user.user_role == "PACIENTE":
        paciente = db.query(Paciente).filter(Paciente.username == current_user.username).first()
        if not paciente or cita.dni_paciente != paciente.dni:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para cancelar esta cita"
            )

    cita.estado = EstadoCita.CANCELADA.value
    db.commit()
    db.refresh(cita)
    return format_cita_response(cita)
