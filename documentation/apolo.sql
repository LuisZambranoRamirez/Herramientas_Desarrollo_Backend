CREATE TYPE "user_role_enum" AS ENUM (
	'SYSTEM_ADMIN',
	'ODONTOLOGO',
	'PACIENTE'
);

CREATE TYPE "dia_semana_enum" AS ENUM (
	'LUNES',
	'MARTES',
	'MIERCOLES',
	'JUEVES',
	'VIERNES',
	'SABADO',
	'DOMINGO'
);

CREATE TYPE "especialidad_enum" AS ENUM (
	'ORTODONCIA',
	'ENDODONCIA',
	'PERIODONCIA',
	'ODONTOPEDIATRIA',
	'CIRUGIA_MAXILOFACIAL',
	'IMPLANTOLOGIA',
	'REHABILITACION_ORAL',
	'ODONTOLOGIA_ESTETICA'
);

CREATE TYPE "estado_cita_enum" AS ENUM (
	'PROGRAMADA',
	'CONFIRMADA',
	'ATENDIDA',
	'CANCELADA',
	'NO_ASISTIO',
	'REPROGRAMADA',
	'EN_PROCESO'
);

CREATE TYPE "estado_tratamiento_enum" AS ENUM (
	'INICIADO',
	'EN_PROCESO',
	'FINALIZADO',
	'PENDIENTE'
);

CREATE TYPE "permisos_enum" AS ENUM (
	'LEER',
	'ACTULIZAR',
	'ELIMINAR',
	'CREAR'
);

CREATE TYPE "metodo_pago_enum" AS ENUM (
	'efectivo',
	'digital'
);

CREATE TYPE "tratamiento_odontologico_enum" AS ENUM (
	'Limpieza_dental_profunda',
	'Aplicacion_de_fluor',
	'Selladores_de_fosas_y_fisuras',
	'Restauracion_con_resina',
	'Ortopedia_maxilar',
	'Implante_dental'
);

-- ---------------------FIN ENUMS ---------------------------

CREATE TABLE "usuario" (
    "username" VARCHAR(50) PRIMARY KEY,
    "password" VARCHAR(255) NOT NULL,
    "activo" BOOLEAN NOT NULL,
    "user_role" user_role_enum NOT NULL,
    "fecha_registro" TIMESTAMP NOT NULL
);

CREATE TABLE "personal" (
    "dni" CHAR(8) PRIMARY KEY,
    "nombres" VARCHAR(100) NOT NULL,
    "apellidos" VARCHAR(100) NOT NULL,
    "telefono" CHAR(9) NOT NULL UNIQUE,
    "correo" VARCHAR(150) NOT NULL UNIQUE,
    "activo" BOOLEAN NOT NULL,
    "fecha_registro" TIMESTAMP NOT NULL
);

CREATE TABLE "paciente" (
	"dni" CHAR(8) PRIMARY KEY,
	"username" VARCHAR(50) NOT NULL UNIQUE,
	"nombres" VARCHAR(100) NOT NULL,
	"apellidos" VARCHAR(100) NOT NULL,
	"direccion" VARCHAR(200) UNIQUE,
	"telefono" CHAR(9) UNIQUE,
	"correo" VARCHAR(150) UNIQUE,
	"observaciones" TEXT NOT NULL,
	"fecha_nacimiento" DATE NOT NULL,
	"fecha_registro" TIMESTAMP NOT NULL,

    CONSTRAINT "fk_paciente_usuario" 
        FOREIGN KEY ("username") REFERENCES "usuario"("username")
        ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE "odontologo" (
    "dni" CHAR(8) PRIMARY KEY,
    "colegiatura" VARCHAR(50) NOT NULL UNIQUE,
    "especialidad" especialidad_enum NOT NULL,
    "username" VARCHAR(50) NOT NULL UNIQUE,

    CONSTRAINT "fk_odontologo_personal" 
        FOREIGN KEY ("dni") REFERENCES "personal"("dni")
        ON DELETE CASCADE ON UPDATE CASCADE,

    CONSTRAINT "fk_odontologo_usuario" 
        FOREIGN KEY ("username") REFERENCES "usuario"("username")
        ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE "horario_personal" (
    "horario_odontologo_id" UUID PRIMARY KEY,
    "dni" CHAR(8) NOT NULL,
    "dia_semana" dia_semana_enum NOT NULL,
    "hora_inicio" TIME NOT NULL,
    "hora_fin" TIME NOT NULL,

    CONSTRAINT "fk_horario_personal_personal" 
        FOREIGN KEY ("dni") REFERENCES "personal"("dni")
        ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE "cita" (
    "cita_id" UUID PRIMARY KEY,
    "dni_paciente" CHAR(8) NOT NULL,
    "dni_odontologo" CHAR(8) NOT NULL,
    "fecha" DATE NOT NULL,
    "hora" TIME NOT NULL,
    "motivo_consulta" VARCHAR(255) NOT NULL,
    "diagnostico" VARCHAR(255),
    "estado" estado_cita_enum NOT NULL,
    "fecha_registro" TIMESTAMP NOT NULL,

    CONSTRAINT "fk_cita_paciente" 
        FOREIGN KEY ("dni_paciente") REFERENCES "paciente"("dni")
        ON DELETE CASCADE ON UPDATE CASCADE,

    CONSTRAINT "fk_cita_odontologo" 
        FOREIGN KEY ("dni_odontologo") REFERENCES "odontologo"("dni")
        ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE "tratamiento_paciente" (
    "tratamiento_paciente_id" UUID PRIMARY KEY,
    "dni_paciente" CHAR(8) NOT NULL,
    "dni_odontologo" CHAR(8) NOT NULL,
    "observaciones" TEXT NOT NULL,
    "precio" NUMERIC(10,2) NOT NULL,
    "tratamiento" tratamiento_odontologico_enum NOT NULL,
    "estado" estado_tratamiento_enum NOT NULL,
    "fecha_registro" TIMESTAMP NOT NULL,

    CONSTRAINT "fk_tratamiento_paciente_odontologo" 
        FOREIGN KEY ("dni_odontologo") REFERENCES "odontologo"("dni")
        ON DELETE CASCADE ON UPDATE CASCADE,
    
    CONSTRAINT "fk_tratamiento_paciente_paciente" 
        FOREIGN KEY ("dni_paciente") REFERENCES "paciente"("dni")
        ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE "agenda_tratamientos" (
    "agenda_tratamientos_id" UUID PRIMARY KEY,
    "id_tratamiento_paciente" UUID NOT NULL,
    "dia_semana" dia_semana_enum NOT NULL,
    "hora_inicio" TIME NOT NULL,
    "hora_fin" TIME NOT NULL,
    "fecha_registro" TIMESTAMP NOT NULL,

    CONSTRAINT "fk_agenda_tratamientos_tratamiento_paciente" 
        FOREIGN KEY ("id_tratamiento_paciente") REFERENCES "tratamiento_paciente"("tratamiento_paciente_id")
        ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE "insumo" (
    "insumo_id" UUID PRIMARY KEY,
    "nombre" VARCHAR(150) NOT NULL UNIQUE,
    "stock" NUMERIC(10,2) NOT NULL,
    "stock_minimo" NUMERIC(10,2) NOT NULL,
    "fecha_vencimiento" DATE,
    "fecha_registro" TIMESTAMP NOT NULL
);

CREATE TABLE "proveedor" (
    "ruc" CHAR(11) PRIMARY KEY,
    "nombre" VARCHAR(255) NOT NULL UNIQUE,
    "telefono" CHAR(9) NOT NULL UNIQUE,
    "fecha_registro" TIMESTAMP NOT NULL
);

CREATE TABLE "insumo_comprado" (
    "insumo_comprado_id" UUID PRIMARY KEY,
    "id_insumo" UUID NOT NULL,
    "id_proveedor" CHAR(11) NOT NULL,
    "cantidad" NUMERIC(10,2) NOT NULL,
    "precio_unitario" NUMERIC(10,2) NOT NULL,
    "fecha_registro" TIMESTAMP NOT NULL,

    CONSTRAINT "fk_insumo_comprado_insumo" 
        FOREIGN KEY ("id_insumo") REFERENCES "insumo"("insumo_id")
        ON DELETE CASCADE ON UPDATE CASCADE,
        
    CONSTRAINT "fk_insumo_comprado_proveedor" 
        FOREIGN KEY ("id_proveedor") REFERENCES "proveedor"("ruc")
        ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE "consumo_insumos" (
    "consumo_insumos_id" UUID PRIMARY KEY,
    "id_agenda_tratamiento" UUID NOT NULL,
    "id_insumo" UUID NOT NULL,
    "cantidad" NUMERIC(10,2) NOT NULL,

    CONSTRAINT "fk_consumo_insumos_agenda_tratamientos" 
        FOREIGN KEY ("id_agenda_tratamiento") REFERENCES "agenda_tratamientos"("agenda_tratamientos_id")
        ON DELETE CASCADE ON UPDATE CASCADE,
    
    CONSTRAINT "fk_consumo_insumos_insumo" 
        FOREIGN KEY ("id_insumo") REFERENCES "insumo"("insumo_id")
        ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE "role_permisos" (
    "role" user_role_enum PRIMARY KEY,
    "permisos" permisos_enum NOT NULL
);

CREATE TABLE "pago" (
    "pago_id" UUID PRIMARY KEY,
    "id_tratamiento_paciente" UUID NOT NULL,
    "monto" NUMERIC(10,2) NOT NULL,
    "metodo_pago" metodo_pago_enum NOT NULL,
    "fecha_registro" TIMESTAMP NOT NULL,

    CONSTRAINT "fk_pago_tratamiento_paciente" 
        FOREIGN KEY ("id_tratamiento_paciente") REFERENCES "tratamiento_paciente"("tratamiento_paciente_id")
        ON DELETE CASCADE ON UPDATE CASCADE
);