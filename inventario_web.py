from flask import Flask, render_template, request, redirect, url_for, flash
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, String, Integer, Float, Enum
import enum
import uuid
from datetime import datetime

app = Flask(__name__)
app.secret_key = "tu_clave_secreta"  # Cambia por algo seguro

Base = declarative_base()

# Enum como antes
class CategoriaItem(enum.Enum):
    MUEBLE = "Mueble"
    ELECTRONICO = "Electrónico"
    MATERIAL = "Material de oficina"
    HERRAMIENTA = "Herramienta"
    OTROS = "Otros"

class EstadoItem(enum.Enum):
    DISPONIBLE = "Disponible"
    EN_USO = "En uso"
    REPARACION = "En reparación"
    DESCARTADO = "Descartado"

class TipoCompra(enum.Enum):
    DONADO = "Donado"
    COMPRADO = "Comprado"

class Item(Base):
    __tablename__ = 'items'
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    nombre = Column(String, nullable=False)
    descripcion = Column(String)
    cantidad = Column(Integer, nullable=False, default=1)
    valor_unitario = Column(Float)
    fecha_registro = Column(String, default=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    categoria = Column(Enum(CategoriaItem), nullable=False)
    ubicacion = Column(String)
    estado = Column(Enum(EstadoItem), default=EstadoItem.DISPONIBLE)
    responsable = Column(String)
    tipo_compra = Column(Enum(TipoCompra), nullable=False, default=TipoCompra.COMPRADO)

# Config DB
engine = create_engine('sqlite:///inventario_web.db')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

# Ruta principal: mostrar lista y formulario para agregar
@app.route('/', methods=['GET', 'POST'])
def index():
    session = Session()
    if request.method == 'POST':
        # Agregar nuevo ítem
        try:
            nombre = request.form['nombre'].strip()
            if not nombre:
                flash("El nombre es obligatorio", "error")
                return redirect(url_for('index'))

            cantidad = int(request.form.get('cantidad', 1))
            valor = float(request.form.get('valor_unitario', 0) or 0)
            categoria = CategoriaItem(request.form['categoria'])
            estado = EstadoItem(request.form.get('estado', EstadoItem.DISPONIBLE.value))
            tipo_compra = TipoCompra(request.form.get('tipo_compra', TipoCompra.COMPRADO.value))
            descripcion = request.form.get('descripcion', '')
            ubicacion = request.form.get('ubicacion', '')
            responsable = request.form.get('responsable', '')

            nuevo_item = Item(
                nombre=nombre,
                cantidad=cantidad,
                valor_unitario=valor,
                categoria=categoria,
                estado=estado,
                tipo_compra=tipo_compra,
                descripcion=descripcion,
                ubicacion=ubicacion,
                responsable=responsable
            )
            session.add(nuevo_item)
            session.commit()
            flash("Ítem agregado correctamente", "success")
        except Exception as e:
            session.rollback()
            flash(f"Error al agregar ítem: {e}", "error")
        finally:
            session.close()
        return redirect(url_for('index'))

    # GET: mostrar lista
    items = session.query(Item).order_by(Item.nombre).all()
    session.close()
    return render_template('index.html', items=items,
                           categorias=CategoriaItem,
                           estados=EstadoItem,
                           tipos_compra=TipoCompra)

# Ruta para editar ítem
@app.route('/editar/<item_id>', methods=['GET', 'POST'])
def editar(item_id):
    session = Session()
    try:
        item = session.query(Item).filter_by(id=item_id).one()
    except NoResultFound:
        session.close()
        flash("Ítem no encontrado", "error")
        return redirect(url_for('index'))

    if request.method == 'POST':
        try:
            item.nombre = request.form['nombre'].strip()
            item.cantidad = int(request.form.get('cantidad', 1))
            item.valor_unitario = float(request.form.get('valor_unitario', 0) or 0)
            item.categoria = CategoriaItem(request.form['categoria'])
            item.estado = EstadoItem(request.form.get('estado', EstadoItem.DISPONIBLE.value))
            item.tipo_compra = TipoCompra(request.form.get('tipo_compra', TipoCompra.COMPRADO.value))
            item.descripcion = request.form.get('descripcion', '')
            item.ubicacion = request.form.get('ubicacion', '')
            item.responsable = request.form.get('responsable', '')
            session.commit()
            flash("Ítem actualizado correctamente", "success")
        except Exception as e:
            session.rollback()
            flash(f"Error al actualizar ítem: {e}", "error")
        finally:
            session.close()
        return redirect(url_for('index'))

    session.close()
    return render_template('editar.html', item=item,
                           categorias=CategoriaItem,
                           estados=EstadoItem,
                           tipos_compra=TipoCompra)

# Ruta para eliminar
@app.route('/eliminar/<item_id>', methods=['POST'])
def eliminar(item_id):
    session = Session()
    try:
        item = session.query(Item).filter_by(id=item_id).one()
        session.delete(item)
        session.commit()
        flash("Ítem eliminado correctamente", "success")
    except NoResultFound:
        flash("Ítem no encontrado", "error")
    except Exception as e:
        session.rollback()
        flash(f"Error al eliminar ítem: {e}", "error")
    finally:
        session.close()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
