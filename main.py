from fastapi import FastAPI, Request, Depends, Form, UploadFile, File
from fastapi.responses import RedirectResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from datetime import datetime
import os
import openpyxl

from database import Base, engine, get_db
from models import Cliente, Factura, Gasto, Proveedor
from config import EMISOR


# ======================= CONFIGURACIÓN INICIAL =======================

Base.metadata.create_all(bind=engine)

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

print(">>> STATIC ABSOLUTE PATH:", os.path.abspath("static"))
templates = Jinja2Templates(directory="templates")

@app.get("/")
def root():
    return RedirectResponse(url="/inicio")

@app.get("/inicio")
def inicio(request: Request, db: Session = Depends(get_db)):
    # Calcular totales de ingresos (facturas)
    facturas = db.query(Factura).all()
    total_ingresos = sum(f.total for f in facturas)

    # Calcular totales de gastos
    gastos = db.query(Gasto).all()
    total_gastos = sum(g.total for g in gastos)

    # Beneficio = ingresos - gastos
    beneficio = total_ingresos - total_gastos

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "total_ingresos": total_ingresos,
            "total_gastos": total_gastos,
            "beneficio": beneficio,
        }
    )



# ======================= CLIENTES =======================

@app.get("/clientes")
def listar_clientes(request: Request, db: Session = Depends(get_db)):
    clientes = db.query(Cliente).order_by(Cliente.id.desc()).all()
    return templates.TemplateResponse("clientes.html", {"request": request, "clientes": clientes})


@app.post("/clientes")
def crear_cliente(
    nombre: str = Form(...),
    nif: str = Form(""),
    direccion: str = Form(""),
    email: str = Form(""),
    telefono: str = Form(""),
    db: Session = Depends(get_db),
):
    nuevo = Cliente(nombre=nombre, nif=nif, direccion=direccion, email=email, telefono=telefono)
    db.add(nuevo)
    db.commit()
    return RedirectResponse(url="/clientes", status_code=303)


@app.get("/clientes/eliminar/{cliente_id}")
def eliminar_cliente(cliente_id: int, db: Session = Depends(get_db)):
    c = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    if c:
        db.delete(c)
        db.commit()
    return RedirectResponse(url="/clientes", status_code=303)


# ======================= PROVEEDORES =======================

@app.get("/proveedores")
def proveedores_list(request: Request, db: Session = Depends(get_db)):
    proveedores = db.query(Proveedor).order_by(Proveedor.id.desc()).all()
    return templates.TemplateResponse("proveedores.html", {"request": request, "proveedores": proveedores})


@app.post("/proveedores")
def proveedores_add(
    nombre: str = Form(...),
    nif: str = Form(""),
    direccion: str = Form(""),
    email: str = Form(""),
    telefono: str = Form(""),
    db: Session = Depends(get_db),
):
    nuevo = Proveedor(nombre=nombre, nif=nif, direccion=direccion, email=email, telefono=telefono)
    db.add(nuevo)
    db.commit()
    return RedirectResponse(url="/proveedores", status_code=303)


@app.get("/proveedores/eliminar/{proveedor_id}")
def proveedores_delete(proveedor_id: int, db: Session = Depends(get_db)):
    p = db.query(Proveedor).filter(Proveedor.id == proveedor_id).first()
    if p:
        db.delete(p)
        db.commit()
    return RedirectResponse(url="/proveedores", status_code=303)


# ======================= FACTURAS =======================

@app.get("/facturas")
def listar_facturas(request: Request, db: Session = Depends(get_db)):
    facturas = db.query(Factura).order_by(Factura.fecha.asc()).all()

    total_base = sum(f.base_imponible for f in facturas)
    total_iva = sum((f.base_imponible * f.iva / 100) for f in facturas)
    total_total = sum(f.total for f in facturas)

    clientes = db.query(Cliente).all()

    return templates.TemplateResponse(
        "facturas.html",
        {
            "request": request,
            "facturas": facturas,
            "clientes": clientes,
            "total_base": total_base,
            "total_iva": total_iva,
            "total_total": total_total,
        }
    )


@app.post("/facturas")
def crear_factura(
    numero: str = Form(...),
    fecha: str = Form(...),
    concepto: str = Form(...),
    base_imponible: float = Form(...),
    iva: float = Form(...),
    cliente_id: int = Form(...),
    db: Session = Depends(get_db),
):
    total = base_imponible + (base_imponible * iva / 100)

    nueva = Factura(
        numero=numero,
        fecha=datetime.strptime(fecha, "%Y-%m-%d"),
        concepto=concepto,
        base_imponible=base_imponible,
        iva=iva,
        total=total,
        cliente_id=cliente_id
    )

    db.add(nueva)
    db.commit()
    return RedirectResponse(url="/facturas", status_code=303)


@app.get("/facturas/eliminar/{factura_id}")
def eliminar_factura(factura_id: int, db: Session = Depends(get_db)):
    f = db.query(Factura).filter(Factura.id == factura_id).first()
    if f:
        db.delete(f)
        db.commit()
    return RedirectResponse(url="/facturas", status_code=303)


# ======================= PDF FACTURA =======================

@app.get("/facturas/pdf/{factura_id}")
def pdf_factura(factura_id: int, db: Session = Depends(get_db)):
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.pagesizes import A4

    factura = db.query(Factura).filter(Factura.id == factura_id).first()
    if not factura:
        return RedirectResponse("/facturas", status_code=303)

    cliente = factura.cliente

    os.makedirs("static/pdf", exist_ok=True)
    nombre_pdf = f"factura_{factura.numero}.pdf"
    ruta_pdf = os.path.join("static/pdf", nombre_pdf)

    doc = SimpleDocTemplate(ruta_pdf, pagesize=A4, rightMargin=40, leftMargin=40, topMargin=60)
    elements = []

    styles = getSampleStyleSheet()
    color = colors.HexColor("#333333")

    Titulo = ParagraphStyle("Titulo", parent=styles["Heading1"], alignment=1, fontSize=22, textColor=color)
    Sub = ParagraphStyle("Sub", parent=styles["Normal"], fontSize=11, textColor=color)

    elements.append(Paragraph("FACTURA", Titulo))
    elements.append(Spacer(1, 10))

    emisor = [
        f"<b>{EMISOR['nombre']}</b>",
        f"NIF: {EMISOR['nif']}",
        EMISOR['direccion'],
        f"Tel: {EMISOR['telefono']} | {EMISOR['email']}",
    ]

    cliente_d = [
        "<b>Cliente:</b>",
        cliente.nombre,
        f"NIF: {cliente.nif}",
        cliente.direccion
    ]

    tabla = Table([[Paragraph("<br/>".join(emisor), styles["Normal"]),
                    Paragraph("<br/>".join(cliente_d), styles["Normal"])]],
                  colWidths=[260, 260])
    elements.append(tabla)
    elements.append(Spacer(1, 20))

    elements.append(Paragraph(f"Número: {factura.numero}", Sub))
    elements.append(Paragraph(f"Fecha: {factura.fecha.strftime('%d/%m/%Y')}", Sub))

    elements.append(Spacer(1, 15))

    data = [
        ["Concepto", "Base", "IVA %", "IVA (€)", "Total"],
        [
            factura.concepto,
            f"{factura.base_imponible:.2f}",
            f"{factura.iva:.0f}",
            f"{factura.base_imponible * factura.iva / 100:.2f}",
            f"{factura.total:.2f}"
        ]
    ]

    tabla2 = Table(data, colWidths=[200, 80, 60, 80, 80])
    tabla2.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), color),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.grey),
        ("ALIGN", (1, 1), (-1, -1), "RIGHT")
    ]))

    elements.append(tabla2)
    elements.append(Spacer(1, 20))

    elements.append(Paragraph(f"<b>Total:</b> {factura.total:.2f} €", Sub))

    pago = f"Banco: {EMISOR['banco']}<br/>IBAN: {EMISOR['iban']}"
    elements.append(Spacer(1, 20))
    elements.append(Paragraph(pago, styles["Normal"]))

    doc.build(elements)
    return FileResponse(ruta_pdf, filename=nombre_pdf)


# ======================= GASTOS =======================

@app.get("/gastos")
def listar_gastos(request: Request, db: Session = Depends(get_db)):
    gastos = db.query(Gasto).order_by(Gasto.fecha.asc()).all()
    proveedores = db.query(Proveedor).all()

    total_base = sum(g.base_imponible for g in gastos)
    total_iva = sum((g.base_imponible * g.iva / 100) for g in gastos)
    total_total = sum(g.total for g in gastos)

    return templates.TemplateResponse(
        "gastos.html",
        {
            "request": request,
            "gastos": gastos,
            "proveedores": proveedores,
            "total_base": total_base,
            "total_iva": total_iva,
            "total_total": total_total
        }
    )


@app.post("/gastos")
def crear_gasto(
    numero_factura: str = Form(...),
    proveedor_id: int = Form(...),
    fecha: str = Form(...),
    base_imponible: float = Form(...),
    iva: float = Form(...),
    descripcion: str = Form(""),
    comprobante: UploadFile = File(None),
    db: Session = Depends(get_db),
):
    total = base_imponible + (base_imponible * iva / 100)

    archivo = None
    if comprobante:
        os.makedirs("static/comprobantes", exist_ok=True)
        archivo = f"{numero_factura}_{comprobante.filename}"
        ruta = os.path.join("static/comprobantes", archivo)
        with open(ruta, "wb") as f:
            f.write(comprobante.file.read())

    nuevo = Gasto(
        numero_factura=numero_factura,
        proveedor_id=proveedor_id,
        fecha=datetime.strptime(fecha, "%Y-%m-%d"),
        base_imponible=base_imponible,
        iva=iva,
        total=total,
        descripcion=descripcion,
        comprobante=archivo
    )

    db.add(nuevo)
    db.commit()
    return RedirectResponse(url="/gastos", status_code=303)


@app.get("/gastos/eliminar/{gasto_id}")
def eliminar_gasto(gasto_id: int, db: Session = Depends(get_db)):
    g = db.query(Gasto).filter(Gasto.id == gasto_id).first()
    if g:
        if g.comprobante:
            ruta = os.path.join("static/comprobantes", g.comprobante)
            if os.path.exists(ruta):
                os.remove(ruta)
        db.delete(g)
        db.commit()
    return RedirectResponse(url="/gastos", status_code=303)


# ======================= EXPORTACIÓN ANUAL (AT) =======================

@app.get("/exportar/AT")
def exportar_AT(db: Session = Depends(get_db)):
    facturas = db.query(Factura).order_by(Factura.fecha.asc()).all()
    gastos = db.query(Gasto).order_by(Gasto.fecha.asc()).all()

    wb = openpyxl.Workbook()

    ws1 = wb.active
    ws1.title = "EXPEDIDAS"
    ws1.append(["Fecha", "NIF", "Cliente", "Número", "Concepto", "Base", "IVA%", "IVA€", "Total"])

    for f in facturas:
        ws1.append([
            f.fecha.strftime("%d/%m/%Y"),
            f.cliente.nif if f.cliente else "",
            f.cliente.nombre if f.cliente else "",
            f.numero,
            f.concepto,
            f.base_imponible,
            f.iva,
            f.base_imponible * f.iva / 100,
            f.total
        ])

    ws2 = wb.create_sheet("RECIBIDAS")
    ws2.append(["Fecha", "NIF Proveedor", "Proveedor", "Número", "Descripción", "Base", "IVA%", "IVA€", "Total"])

    for g in gastos:
        ws2.append([
            g.fecha.strftime("%d/%m/%Y"),
            g.proveedor_rel.nif if g.proveedor_rel else "",
            g.proveedor_rel.nombre if g.proveedor_rel else "",
            g.numero_factura,
            g.descripcion,
            g.base_imponible,
            g.iva,
            g.base_imponible * g.iva / 100,
            g.total
        ])

    ruta_excel = "static/export_AT.xlsx"
    wb.save(ruta_excel)

    return FileResponse(ruta_excel, filename="export_AT.xlsx")





