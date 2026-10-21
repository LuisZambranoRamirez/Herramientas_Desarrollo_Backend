from typing import Optional
import datetime
import decimal
import enum
import uuid

from sqlalchemy import Boolean, CHAR, Date, DateTime, Enum, ForeignKeyConstraint, Numeric, PrimaryKeyConstraint, String, Text, Time, UniqueConstraint, Uuid
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    pass


class DiaSemanaEnum(str, enum.Enum):
    LUNES = 'LUNES'
    MARTES = 'MARTES'
    MIERCOLES = 'MIERCOLES'
    JUEVES = 'JUEVES'
    VIERNES = 'VIERNES'
    SABADO = 'SABADO'
    DOMINGO = 'DOMINGO'


class EspecialidadEnum(str, enum.Enum):
    ORTODONCIA = 'ORTODONCIA'
    ENDODONCIA = 'ENDODONCIA'
    PERIODONCIA = 'PERIODONCIA'
    ODONTOPEDIATRIA = 'ODONTOPEDIATRIA'
    CIRUGIA_MAXILOFACIAL = 'CIRUGIA_MAXILOFACIAL'
    IMPLANTOLOGIA = 'IMPLANTOLOGIA'
    REHABILITACION_ORAL = 'REHABILITACION_ORAL'
    ODONTOLOGIA_ESTETICA = 'ODONTOLOGIA_ESTETICA'


class EstadoCitaEnum(str, enum.Enum):
    PROGRAMADA = 'PROGRAMADA'
    CONFIRMADA = 'CONFIRMADA'
    ATENDIDA = 'ATENDIDA'
    CANCELADA = 'CANCELADA'
    NO_ASISTIO = 'NO_ASISTIO'
    REPROGRAMADA = 'REPROGRAMADA'
    EN_PROCESO = 'EN_PROCESO'


class EstadoTratamientoEnum(str, enum.Enum):
    INICIADO = 'INICIADO'
    EN_PROCESO = 'EN_PROCESO'
    FINALIZADO = 'FINALIZADO'
    PENDIENTE = 'PENDIENTE'


class MetodoPagoEnum(str, enum.Enum):
    EFECTIVO = 'efectivo'
    DIGITAL = 'digital'


class PermisosEnum(str, enum.Enum):
    LEER = 'LEER'
    ACTUALIZAR = 'ACTUALIZAR'
    ELIMINAR = 'ELIMINAR'
    CREAR = 'CREAR'


class TratamientoOdontologicoEnum(str, enum.Enum):
    LIMPIEZA_DENTAL_PROFUNDA = 'Limpieza_dental_profunda'
    APLICACION_DE_FLUOR = 'Aplicacion_de_fluor'
    SELLADORES_DE_FOSAS_Y_FISURAS = 'Selladores_de_fosas_y_fisuras'
    RESTAURACION_CON_RESINA = 'Restauracion_con_resina'
    ORTOPEDIA_MAXILAR = 'Ortopedia_maxilar'
    IMPLANTE_DENTAL = 'Implante_dental'


class UserRoleEnum(str, enum.Enum):
    SYSTEM_ADMIN = 'SYSTEM_ADMIN'
    ODONTOLOGO = 'ODONTOLOGO'
    PACIENTE = 'PACIENTE'


class Insumo(Base):
    __tablename__ = 'insumo'
    __table_args__ = (
        PrimaryKeyConstraint('insumo_id', name='insumo_pkey'),
        UniqueConstraint('nombre', name='insumo_nombre_key')
    )

    insumo_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    nombre: Mapped[str] = mapped_column(String(150), nullable=False)
    stock: Mapped[decimal.Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    stock_minimo: Mapped[decimal.Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    fecha_registro: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False)
    fecha_vencimiento: Mapped[Optional[datetime.date]] = mapped_column(Date)

    insumo_comprado: Mapped[list['InsumoComprado']] = relationship('InsumoComprado', back_populates='insumo')
    consumo_insumos: Mapped[list['ConsumoInsumos']] = relationship('ConsumoInsumos', back_populates='insumo')


class Personal(Base):
    __tablename__ = 'personal'
    __table_args__ = (
        PrimaryKeyConstraint('dni', name='personal_pkey'),
        UniqueConstraint('correo', name='personal_correo_key'),
        UniqueConstraint('telefono', name='personal_telefono_key')
    )

    dni: Mapped[str] = mapped_column(CHAR(8), primary_key=True)
    nombres: Mapped[str] = mapped_column(String(100), nullable=False)
    apellidos: Mapped[str] = mapped_column(String(100), nullable=False)
    telefono: Mapped[str] = mapped_column(CHAR(9), nullable=False)
    correo: Mapped[str] = mapped_column(String(150), nullable=False)
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False)
    fecha_registro: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False)

    horario_personal: Mapped[list['HorarioPersonal']] = relationship('HorarioPersonal', back_populates='personal')


class Proveedor(Base):
    __tablename__ = 'proveedor'
    __table_args__ = (
        PrimaryKeyConstraint('ruc', name='proveedor_pkey'),
        UniqueConstraint('nombre', name='proveedor_nombre_key'),
        UniqueConstraint('telefono', name='proveedor_telefono_key')
    )

    ruc: Mapped[str] = mapped_column(CHAR(11), primary_key=True)
    nombre: Mapped[str] = mapped_column(String(255), nullable=False)
    telefono: Mapped[str] = mapped_column(CHAR(9), nullable=False)
    fecha_registro: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False)

    insumo_comprado: Mapped[list['InsumoComprado']] = relationship('InsumoComprado', back_populates='proveedor')


class RolePermisos(Base):
    __tablename__ = 'role_permisos'
    __table_args__ = (
        PrimaryKeyConstraint('role', name='role_permisos_pkey'),
    )

    role: Mapped[UserRoleEnum] = mapped_column(Enum(UserRoleEnum, values_callable=lambda cls: [member.value for member in cls], name='user_role_enum'), primary_key=True)
    permisos: Mapped[PermisosEnum] = mapped_column(Enum(PermisosEnum, values_callable=lambda cls: [member.value for member in cls], name='permisos_enum'), nullable=False)


class Usuario(Base):
    __tablename__ = 'usuario'
    __table_args__ = (
        PrimaryKeyConstraint('username', name='usuario_pkey'),
    )

    username: Mapped[str] = mapped_column(String(50), primary_key=True)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False)
    user_role: Mapped[UserRoleEnum] = mapped_column(Enum(UserRoleEnum, values_callable=lambda cls: [member.value for member in cls], name='user_role_enum'), nullable=False)
    fecha_registro: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False)

    odontologo: Mapped['Odontologo'] = relationship('Odontologo', uselist=False, back_populates='usuario')
    paciente: Mapped['Paciente'] = relationship('Paciente', uselist=False, back_populates='usuario')


class HorarioPersonal(Base):
    __tablename__ = 'horario_personal'
    __table_args__ = (
        ForeignKeyConstraint(['dni'], ['personal.dni'], ondelete='CASCADE', onupdate='CASCADE', name='fk_horario_personal_personal'),
        PrimaryKeyConstraint('horario_odontologo_id', name='horario_personal_pkey')
    )

    horario_odontologo_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    dni: Mapped[str] = mapped_column(CHAR(8), nullable=False)
    dia_semana: Mapped[DiaSemanaEnum] = mapped_column(Enum(DiaSemanaEnum, values_callable=lambda cls: [member.value for member in cls], name='dia_semana_enum'), nullable=False)
    hora_inicio: Mapped[datetime.time] = mapped_column(Time, nullable=False)
    hora_fin: Mapped[datetime.time] = mapped_column(Time, nullable=False)

    personal: Mapped['Personal'] = relationship('Personal', back_populates='horario_personal')


class InsumoComprado(Base):
    __tablename__ = 'insumo_comprado'
    __table_args__ = (
        ForeignKeyConstraint(['id_insumo'], ['insumo.insumo_id'], ondelete='CASCADE', onupdate='CASCADE', name='fk_insumo_comprado_insumo'),
        ForeignKeyConstraint(['id_proveedor'], ['proveedor.ruc'], ondelete='CASCADE', onupdate='CASCADE', name='fk_insumo_comprado_proveedor'),
        PrimaryKeyConstraint('insumo_comprado_id', name='insumo_comprado_pkey')
    )

    insumo_comprado_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    id_insumo: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    id_proveedor: Mapped[str] = mapped_column(CHAR(11), nullable=False)
    cantidad: Mapped[decimal.Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    precio_unitario: Mapped[decimal.Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    fecha_registro: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False)

    insumo: Mapped['Insumo'] = relationship('Insumo', back_populates='insumo_comprado')
    proveedor: Mapped['Proveedor'] = relationship('Proveedor', back_populates='insumo_comprado')


class Odontologo(Personal):
    __tablename__ = 'odontologo'
    __table_args__ = (
        ForeignKeyConstraint(['dni'], ['personal.dni'], ondelete='CASCADE', onupdate='CASCADE', name='fk_odontologo_personal'),
        ForeignKeyConstraint(['username'], ['usuario.username'], ondelete='CASCADE', onupdate='CASCADE', name='fk_odontologo_usuario'),
        PrimaryKeyConstraint('dni', name='odontologo_pkey'),
        UniqueConstraint('colegiatura', name='odontologo_colegiatura_key'),
        UniqueConstraint('username', name='odontologo_username_key')
    )

    dni: Mapped[str] = mapped_column(CHAR(8), primary_key=True)
    colegiatura: Mapped[str] = mapped_column(String(50), nullable=False)
    especialidad: Mapped[EspecialidadEnum] = mapped_column(Enum(EspecialidadEnum, values_callable=lambda cls: [member.value for member in cls], name='especialidad_enum'), nullable=False)
    username: Mapped[str] = mapped_column(String(50), nullable=False)

    usuario: Mapped['Usuario'] = relationship('Usuario', back_populates='odontologo')
    cita: Mapped[list['Cita']] = relationship('Cita', back_populates='odontologo')
    tratamiento_paciente: Mapped[list['TratamientoPaciente']] = relationship('TratamientoPaciente', back_populates='odontologo')


class Paciente(Base):
    __tablename__ = 'paciente'
    __table_args__ = (
        ForeignKeyConstraint(['username'], ['usuario.username'], ondelete='CASCADE', onupdate='CASCADE', name='fk_paciente_usuario'),
        PrimaryKeyConstraint('dni', name='paciente_pkey'),
        UniqueConstraint('correo', name='paciente_correo_key'),
        UniqueConstraint('direccion', name='paciente_direccion_key'),
        UniqueConstraint('telefono', name='paciente_telefono_key'),
        UniqueConstraint('username', name='paciente_username_key')
    )

    dni: Mapped[str] = mapped_column(CHAR(8), primary_key=True)
    username: Mapped[str] = mapped_column(String(50), nullable=False)
    nombres: Mapped[str] = mapped_column(String(100), nullable=False)
    apellidos: Mapped[str] = mapped_column(String(100), nullable=False)
    observaciones: Mapped[str] = mapped_column(Text, nullable=False)
    fecha_nacimiento: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    fecha_registro: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False)
    direccion: Mapped[Optional[str]] = mapped_column(String(200))
    telefono: Mapped[Optional[str]] = mapped_column(CHAR(9))
    correo: Mapped[Optional[str]] = mapped_column(String(150))

    usuario: Mapped['Usuario'] = relationship('Usuario', back_populates='paciente')
    cita: Mapped[list['Cita']] = relationship('Cita', back_populates='paciente')
    tratamiento_paciente: Mapped[list['TratamientoPaciente']] = relationship('TratamientoPaciente', back_populates='paciente')


class Cita(Base):
    __tablename__ = 'cita'
    __table_args__ = (
        ForeignKeyConstraint(['dni_odontologo'], ['odontologo.dni'], ondelete='CASCADE', onupdate='CASCADE', name='fk_cita_odontologo'),
        ForeignKeyConstraint(['dni_paciente'], ['paciente.dni'], ondelete='CASCADE', onupdate='CASCADE', name='fk_cita_paciente'),
        PrimaryKeyConstraint('cita_id', name='cita_pkey')
    )

    cita_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    dni_paciente: Mapped[str] = mapped_column(CHAR(8), nullable=False)
    dni_odontologo: Mapped[str] = mapped_column(CHAR(8), nullable=False)
    fecha: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    hora: Mapped[datetime.time] = mapped_column(Time, nullable=False)
    motivo_consulta: Mapped[str] = mapped_column(String(255), nullable=False)
    estado: Mapped[EstadoCitaEnum] = mapped_column(Enum(EstadoCitaEnum, values_callable=lambda cls: [member.value for member in cls], name='estado_cita_enum'), nullable=False)
    fecha_registro: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False)
    diagnostico: Mapped[Optional[str]] = mapped_column(String(255))

    odontologo: Mapped['Odontologo'] = relationship('Odontologo', back_populates='cita')
    paciente: Mapped['Paciente'] = relationship('Paciente', back_populates='cita')


class TratamientoPaciente(Base):
    __tablename__ = 'tratamiento_paciente'
    __table_args__ = (
        ForeignKeyConstraint(['dni_odontologo'], ['odontologo.dni'], ondelete='CASCADE', onupdate='CASCADE', name='fk_tratamiento_paciente_odontologo'),
        ForeignKeyConstraint(['dni_paciente'], ['paciente.dni'], ondelete='CASCADE', onupdate='CASCADE', name='fk_tratamiento_paciente_paciente'),
        PrimaryKeyConstraint('tratamiento_paciente_id', name='tratamiento_paciente_pkey')
    )

    tratamiento_paciente_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    dni_paciente: Mapped[str] = mapped_column(CHAR(8), nullable=False)
    dni_odontologo: Mapped[str] = mapped_column(CHAR(8), nullable=False)
    observaciones: Mapped[str] = mapped_column(Text, nullable=False)
    precio: Mapped[decimal.Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    tratamiento: Mapped[TratamientoOdontologicoEnum] = mapped_column(Enum(TratamientoOdontologicoEnum, values_callable=lambda cls: [member.value for member in cls], name='tratamiento_odontologico_enum'), nullable=False)
    estado: Mapped[EstadoTratamientoEnum] = mapped_column(Enum(EstadoTratamientoEnum, values_callable=lambda cls: [member.value for member in cls], name='estado_tratamiento_enum'), nullable=False)
    fecha_registro: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False)

    odontologo: Mapped['Odontologo'] = relationship('Odontologo', back_populates='tratamiento_paciente')
    paciente: Mapped['Paciente'] = relationship('Paciente', back_populates='tratamiento_paciente')
    agenda_tratamientos: Mapped[list['AgendaTratamientos']] = relationship('AgendaTratamientos', back_populates='tratamiento_paciente')
    pago: Mapped[list['Pago']] = relationship('Pago', back_populates='tratamiento_paciente')


class AgendaTratamientos(Base):
    __tablename__ = 'agenda_tratamientos'
    __table_args__ = (
        ForeignKeyConstraint(['id_tratamiento_paciente'], ['tratamiento_paciente.tratamiento_paciente_id'], ondelete='CASCADE', onupdate='CASCADE', name='fk_agenda_tratamientos_tratamiento_paciente'),
        PrimaryKeyConstraint('agenda_tratamientos_id', name='agenda_tratamientos_pkey')
    )

    agenda_tratamientos_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    id_tratamiento_paciente: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    dia_semana: Mapped[DiaSemanaEnum] = mapped_column(Enum(DiaSemanaEnum, values_callable=lambda cls: [member.value for member in cls], name='dia_semana_enum'), nullable=False)
    hora_inicio: Mapped[datetime.time] = mapped_column(Time, nullable=False)
    hora_fin: Mapped[datetime.time] = mapped_column(Time, nullable=False)
    fecha_registro: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False)

    tratamiento_paciente: Mapped['TratamientoPaciente'] = relationship('TratamientoPaciente', back_populates='agenda_tratamientos')
    consumo_insumos: Mapped[list['ConsumoInsumos']] = relationship('ConsumoInsumos', back_populates='agenda_tratamientos')


class Pago(Base):
    __tablename__ = 'pago'
    __table_args__ = (
        ForeignKeyConstraint(['id_tratamiento_paciente'], ['tratamiento_paciente.tratamiento_paciente_id'], ondelete='CASCADE', onupdate='CASCADE', name='fk_pago_tratamiento_paciente'),
        PrimaryKeyConstraint('pago_id', name='pago_pkey')
    )

    pago_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    id_tratamiento_paciente: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    monto: Mapped[decimal.Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    metodo_pago: Mapped[MetodoPagoEnum] = mapped_column(Enum(MetodoPagoEnum, values_callable=lambda cls: [member.value for member in cls], name='metodo_pago_enum'), nullable=False)
    fecha_registro: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False)

    tratamiento_paciente: Mapped['TratamientoPaciente'] = relationship('TratamientoPaciente', back_populates='pago')


class ConsumoInsumos(Base):
    __tablename__ = 'consumo_insumos'
    __table_args__ = (
        ForeignKeyConstraint(['id_agenda_tratamiento'], ['agenda_tratamientos.agenda_tratamientos_id'], ondelete='CASCADE', onupdate='CASCADE', name='fk_consumo_insumos_agenda_tratamientos'),
        ForeignKeyConstraint(['id_insumo'], ['insumo.insumo_id'], ondelete='CASCADE', onupdate='CASCADE', name='fk_consumo_insumos_insumo'),
        PrimaryKeyConstraint('consumo_insumos_id', name='consumo_insumos_pkey')
    )

    consumo_insumos_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    id_agenda_tratamiento: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    id_insumo: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    cantidad: Mapped[decimal.Decimal] = mapped_column(Numeric(10, 2), nullable=False)

    agenda_tratamientos: Mapped['AgendaTratamientos'] = relationship('AgendaTratamientos', back_populates='consumo_insumos')
    insumo: Mapped['Insumo'] = relationship('Insumo', back_populates='consumo_insumos')
