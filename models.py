from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey
from sqlalchemy.orm import relationship
from database import Base


class Cliente(Base):
    __tablename__ = "clientes"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    nif = Column(String, nullable=True)
    direccion = Column(String, nullable=True)
    email = Column(String, nullable=True)
    telefono = Column(String, nullable=True)

    facturas = relationship("Factura", back_populates="cliente")


class Proveedor(Base):
    __tablename__ = "proveedores"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, nullable=False)
    nif = Column(String, nullable=True)
    direccion = Column(String, nullable=True)
    email = Column(String, nullable=True)
    telefono = Column(String, nullable=True)

    gastos = relationship("Gasto", back_populates="proveedor_rel")


class Factura(Base):
    __tablename__ = "facturas"

    id = Column(Integer, primary_key=True, index=True)
    numero = Column(String, nullable=False)
    fecha = Column(Date, nullable=False)
    concepto = Column(String, nullable=False)
    base_imponible = Column(Float, nullable=False)
    iva = Column(Float, nullable=False)
    total = Column(Float, nullable=False)
    cliente_id = Column(Integer, ForeignKey("clientes.id"))

    cliente = relationship("Cliente", back_populates="facturas")


class Gasto(Base):
    __tablename__ = "gastos"

    id = Column(Integer, primary_key=True, index=True)
    numero_factura = Column(String, nullable=False)
    fecha = Column(Date, nullable=False)
    base_imponible = Column(Float, nullable=False)
    iva = Column(Float, nullable=False)
    total = Column(Float, nullable=False)
    descripcion = Column(String, nullable=True)
    comprobante = Column(String, nullable=True)
    proveedor_id = Column(Integer, ForeignKey("proveedores.id"))

    proveedor_rel = relationship("Proveedor", back_populates="gastos")






