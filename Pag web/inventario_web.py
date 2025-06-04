from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, String, Integer, Float, Enum as SQLAlchemyEnum # Renombrado para evitar conflicto
import enum
import uuid
from datetime import datetime

app = Flask(__name__)
app.secret_key = "tu_clave_secreta"

Base = declarative_base()

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
    categoria = Column(SQLAlchemyEnum(CategoriaItem), nullable=False)
    ubicacion = Column(String)
    estado = Column(SQLAlchemyEnum(EstadoItem), default=EstadoItem.DISPONIBLE)
    responsable = Column(String)
    tipo_compra = Column(SQLAlchemyEnum(TipoCompra), nullable=False, default=TipoCompra.COMPRADO)

engine = create_engine('sqlite:///inventario_web.db')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

@app.route('/', methods=['GET', 'POST'])
def index():
    session = Session()
    if request.method == 'POST':
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

    items = session.query(Item).order_by(Item.nombre).all()
    session.close()
    return render_template('index.html', items=items,
                           categorias=CategoriaItem,
                           estados=EstadoItem,
                           tipos_compra=TipoCompra)

@app.route('/estadisticas')
def estadisticas():
    # Esta ruta ahora simplemente renderiza el HTML.
    # Los datos se cargarán vía JavaScript desde /api/estadisticas
    return render_template('estadisticas.html')


# API endpoint para datos de gráficos (MEJORADO)
@app.route('/api/estadisticas')
def api_estadisticas():
    session = Session()
    try:
        # Datos para gráficos de categorías
        categorias_nombres = []
        categorias_valores = []
        categorias_cantidades_items = []
        
        for categoria_enum in CategoriaItem:
            items = session.query(Item).filter_by(categoria=categoria_enum).all()
            valor_total_categoria = sum(item.valor_unitario * item.cantidad for item in items if item.valor_unitario is not None)
            cantidad_total_items_categoria = sum(item.cantidad for item in items)
            
            categorias_nombres.append(categoria_enum.value)
            categorias_valores.append(valor_total_categoria)
            categorias_cantidades_items.append(cantidad_total_items_categoria)

        # Datos para gráficos de estados
        estados_nombres = []
        estados_valores = []
        estados_cantidades_items = []

        for estado_enum in EstadoItem:
            items = session.query(Item).filter_by(estado=estado_enum).all()
            valor_total_estado = sum(item.valor_unitario * item.cantidad for item in items if item.valor_unitario is not None)
            cantidad_total_items_estado = sum(item.cantidad for item in items)

            estados_nombres.append(estado_enum.value)
            estados_valores.append(valor_total_estado)
            estados_cantidades_items.append(cantidad_total_items_estado)

        # Datos para gráficos de tipos de compra
        tipos_compra_nombres = []
        tipos_compra_valores = []
        tipos_compra_cantidades_items = []

        for tipo_enum in TipoCompra:
            items = session.query(Item).filter_by(tipo_compra=tipo_enum).all()
            valor_total_tipo = sum(item.valor_unitario * item.cantidad for item in items if item.valor_unitario is not None)
            cantidad_total_items_tipo = sum(item.cantidad for item in items)

            tipos_compra_nombres.append(tipo_enum.value)
            tipos_compra_valores.append(valor_total_tipo)
            tipos_compra_cantidades_items.append(cantidad_total_items_tipo)
        
        # Totales generales para las tarjetas de resumen
        todos_los_items = session.query(Item).all()
        gran_total_valor = sum(item.valor_unitario * item.cantidad for item in todos_los_items if item.valor_unitario is not None)
        gran_total_cantidad_items = sum(item.cantidad for item in todos_los_items)
        
        # Contar categorías únicas que realmente tienen items
        categorias_con_items = session.query(Item.categoria).distinct().count()
        
        return jsonify({
            'categorias_nombres': categorias_nombres,
            'categorias_valores': categorias_valores,
            'categorias_cantidades_items': categorias_cantidades_items,
            
            'estados_nombres': estados_nombres,
            'estados_valores': estados_valores,
            'estados_cantidades_items': estados_cantidades_items,
            
            'tipos_compra_nombres': tipos_compra_nombres,
            'tipos_compra_valores': tipos_compra_valores,
            'tipos_compra_cantidades_items': tipos_compra_cantidades_items,

            'gran_total_valor': gran_total_valor,
            'gran_total_cantidad_items': gran_total_cantidad_items,
            # Usar len(CategoriaItem) si se quieren todas las definidas,
            # o categorias_con_items si solo las que tienen items.
            'total_categorias_activas': len(CategoriaItem) 
        })
    except Exception as e:
        # Log el error en el servidor
        print(f"Error en /api/estadisticas: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()

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
            session.close() # Asegurar que la sesión se cierre también en caso de éxito
        return redirect(url_for('index'))

    # GET request
    # session.close() # No cerrar aquí, se necesita para render_template si la sesión se usara en el template
    # Sin embargo, para este caso, item ya está cargado. Es buena práctica cerrar después de usar.
    # Pero si el POST falla y se re-renderiza, la sesión debe estar abierta.
    # La estructura actual con finally en POST es mejor. Para GET, cerrar después de render_template o al final.
    # En este caso, el item ya está cargado, así que podemos cerrar la sesión.
    # Pero si la plantilla necesitara lazy loading, esto fallaría.
    # Por seguridad y consistencia, mantenemos el cierre después de la operación principal.
    # Para GET, es después de cargar el item.
    # Para POST, es dentro del finally.
    
    # Considerando que no hay más operaciones de sesión después de cargar el item para GET:
    # Se podría cerrar la sesión aquí para el GET.
    # session.close() # Pero si se hace así, el finally del POST no la tendrá si el POST no se ejecuta
    # Lo mejor es que cada ruta maneje su sesión completamente.
    # En este caso, la sesión ya está cerrada si viene de un POST fallido (por el finally).
    # Si es un GET puro, se cerrará al final del try/except/finally de este request.
    # La sesión se pasará al template renderizado, pero no se harán más queries allí.

    # Re-evaluando: el session.close() debe estar en un finally para la lógica del GET.
    # El código original tenía session.close() antes de render_template para el GET,
    # lo cual está bien si item ya tiene todos los datos cargados (no lazy-loading).
    # Y un finally en el POST.
    # Para mayor claridad, cada bloque (GET, POST) debe gestionar su sesión.

    # La estructura original del GET era:
    # session = Session()
    # try: item = ...
    # except NoResultFound: session.close(); ...
    # if POST: ... finally: session.close()
    # session.close() ANTES de render_template para el GET. Esto es correcto.
    # Aquí la sesión ya estaría cerrada por el try/except de la carga del ítem o por el POST.
    # Sin embargo, para ser explícito, el GET también debería tener su propio try/finally para session.
    # El session.close() que está fuera del if POST en el original, aplica al final del GET.

    # El código original era:
    # session = Session()
    # try: item = ...
    # except: flash(); session.close(); return redirect()
    # if POST:
    #    try: ... session.commit()
    #    except: session.rollback(); flash()
    #    finally: session.close() # CIERRA SESIÓN DEL POST
    #    return redirect()
    # session.close() # CIERRA SESIÓN DEL GET
    # return render_template(...)
    # Esto es redundante si el POST siempre redirige. Si el POST no redirige (ej. error y re-renderiza), entonces el session.close() del GET se ejecutaría.
    # Es más limpio que cada ruta cierre su propia sesión.
    # Aquí, si es GET, la sesión sigue abierta hasta `session.close()` más abajo.
    # Si es POST, el `finally` del POST la cierra.
    _item_data = {
        'id': item.id,
        'nombre': item.nombre,
        'descripcion': item.descripcion,
        'cantidad': item.cantidad,
        'valor_unitario': item.valor_unitario,
        'fecha_registro': item.fecha_registro,
        'categoria': item.categoria,
        'ubicacion': item.ubicacion,
        'estado': item.estado,
        'responsable': item.responsable,
        'tipo_compra': item.tipo_compra
    }
    session.close() # Cerrar sesión después de haber accedido a todos los atributos de item.
    return render_template('editar.html', item=_item_data, # Pasar un dict es más seguro si el objeto item pudiera expirar
                           categorias=CategoriaItem,
                           estados=EstadoItem,
                           tipos_compra=TipoCompra)


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