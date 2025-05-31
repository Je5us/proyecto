import sqlalchemy

from tkinter import *
from tkinter import ttk, messagebox
from sqlalchemy import create_engine, Column, String, Integer, Float, Enum
from sqlalchemy.orm import declarative_base, sessionmaker
import enum
from datetime import datetime
import uuid

# Configuración de la Base de Datos
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
    categoria = Column(Enum(CategoriaItem), nullable=False)
    ubicacion = Column(String)
    estado = Column(Enum(EstadoItem), default=EstadoItem.DISPONIBLE)
    responsable = Column(String)
    tipo_compra = Column(Enum(TipoCompra), nullable=False, default=TipoCompra.COMPRADO)

engine = create_engine('sqlite:///inventario_gui.db')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()

class InventarioApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Sistema de Inventario")
        self.root.geometry("1000x600")
        self.root.resizable(True, True)
        self.root.configure(bg="#add8e6")  # Fondo celeste para ventana principal
        
        self.style = ttk.Style()
        self.style.configure('TFrame', background='#add8e6')
        self.style.configure('TLabel', background='#add8e6', font=('Arial', 10))
        self.style.configure('Header.TLabel', font=('Arial', 12, 'bold'), background='#add8e6')
        self.style.configure('TButton', font=('Arial', 10), padding=5)
        
        self.create_widgets()
        self.load_items()
    
    def create_widgets(self):
        # Definir nuevo estilo para etiquetas del formulario
        self.style.configure('FormLabel.TLabel', font=('Verdana', 16), background='#add8e6')
    
        # Frame Principal con fondo celeste
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=BOTH, expand=True, padx=10, pady=10)
        main_frame.configure(style='TFrame')  # asegura que use el estilo
    
        # Frame de Formulario
        form_frame = ttk.LabelFrame(main_frame, text="Agregar/Editar Ítem", padding=10)
        form_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        form_frame.configure(style='TFrame')
    
        # Campos del Formulario usando el nuevo estilo 'FormLabel.TLabel'
        ttk.Label(form_frame, text="Nombre:", style='FormLabel.TLabel').grid(row=0, column=0, sticky=W, pady=2)
        self.nombre_entry = ttk.Entry(form_frame, width=30)
        self.nombre_entry.grid(row=0, column=1, pady=2, padx=5)
    
        ttk.Label(form_frame, text="Descripción:", style='FormLabel.TLabel').grid(row=1, column=0, sticky=W, pady=2)
        self.desc_entry = ttk.Entry(form_frame, width=30)
        self.desc_entry.grid(row=1, column=1, pady=2, padx=5)
    
        ttk.Label(form_frame, text="Cantidad:", style='FormLabel.TLabel').grid(row=2, column=0, sticky=W, pady=2)
        self.cantidad_entry = ttk.Spinbox(form_frame, from_=1, to=1000, width=10)
        self.cantidad_entry.grid(row=2, column=1, sticky=W, pady=2, padx=5)
    
        ttk.Label(form_frame, text="Valor Unitario:", style='FormLabel.TLabel').grid(row=3, column=0, sticky=W, pady=2)
        self.valor_entry = ttk.Entry(form_frame, width=15)
        self.valor_entry.grid(row=3, column=1, sticky=W, pady=2, padx=5)
    
        ttk.Label(form_frame, text="Categoría:", style='FormLabel.TLabel').grid(row=4, column=0, sticky=W, pady=2)
        self.categoria_combo = ttk.Combobox(form_frame, values=[cat.value for cat in CategoriaItem], state="readonly")
        self.categoria_combo.grid(row=4, column=1, sticky=W, pady=2, padx=5)
    
        ttk.Label(form_frame, text="Ubicación:", style='FormLabel.TLabel').grid(row=5, column=0, sticky=W, pady=2)
        self.ubicacion_entry = ttk.Entry(form_frame, width=30)
        self.ubicacion_entry.grid(row=5, column=1, pady=2, padx=5)
    
        ttk.Label(form_frame, text="Estado:", style='FormLabel.TLabel').grid(row=6, column=0, sticky=W, pady=2)
        self.estado_combo = ttk.Combobox(form_frame, values=[estado.value for estado in EstadoItem], state="readonly")
        self.estado_combo.grid(row=6, column=1, sticky=W, pady=2, padx=5)
    
        ttk.Label(form_frame, text="Responsable:", style='FormLabel.TLabel').grid(row=7, column=0, sticky=W, pady=2)
        self.responsable_entry = ttk.Entry(form_frame, width=30)
        self.responsable_entry.grid(row=7, column=1, pady=2, padx=5)
    
        ttk.Label(form_frame, text="Tipo de Compra:", style='FormLabel.TLabel').grid(row=8, column=0, sticky=W, pady=2)
        self.tipo_compra_combo = ttk.Combobox(form_frame, values=[t.value for t in TipoCompra], state="readonly")
        self.tipo_compra_combo.grid(row=8, column=1, sticky=W, pady=2, padx=5)
        self.tipo_compra_combo.set(TipoCompra.COMPRADO.value)
        
        button_frame = ttk.Frame(form_frame)
        button_frame.grid(row=9, column=0, columnspan=2, pady=10)
        button_frame.configure(style='TFrame')
        
        self.guardar_btn = ttk.Button(button_frame, text="Guardar", command=self.save_item)
        self.guardar_btn.pack(side=LEFT, padx=5)
        
        self.limpiar_btn = ttk.Button(button_frame, text="Limpiar", command=self.clear_form)
        self.limpiar_btn.pack(side=LEFT, padx=5)
        
        list_frame = ttk.LabelFrame(main_frame, text="Lista de Ítems", padding=10)
        list_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        list_frame.configure(style='TFrame')
        
        columns = ("id", "nombre", "cantidad", "valor", "categoria", "estado", "tipo_compra")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings", selectmode="browse")
        
        self.tree.heading("id", text="ID")
        self.tree.heading("nombre", text="Nombre")
        self.tree.heading("cantidad", text="Cantidad")
        self.tree.heading("valor", text="Valor")
        self.tree.heading("categoria", text="Categoría")
        self.tree.heading("estado", text="Estado")
        self.tree.heading("tipo_compra", text="Tipo de Compra")
        
        self.tree.column("id", width=100, anchor=W)
        self.tree.column("nombre", width=150, anchor=W)
        self.tree.column("cantidad", width=60, anchor=CENTER)
        self.tree.column("valor", width=80, anchor=E)
        self.tree.column("categoria", width=120, anchor=W)
        self.tree.column("estado", width=100, anchor=W)
        self.tree.column("tipo_compra", width=100, anchor=W)
        
        scrollbar = ttk.Scrollbar(list_frame, orient=VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=RIGHT, fill=Y)
        self.tree.pack(fill=BOTH, expand=True)
        
        action_frame = ttk.Frame(list_frame)
        action_frame.pack(fill=X, pady=5)
        action_frame.configure(style='TFrame')
        
        self.editar_btn = ttk.Button(action_frame, text="Editar", command=self.edit_item, state=DISABLED)
        self.editar_btn.pack(side=LEFT, padx=5)
        
        self.eliminar_btn = ttk.Button(action_frame, text="Eliminar", command=self.delete_item, state=DISABLED)
        self.eliminar_btn.pack(side=LEFT, padx=5)
        
        self.buscar_entry = ttk.Entry(action_frame, width=30)
        self.buscar_entry.pack(side=LEFT, padx=5, fill=X, expand=True)
        self.buscar_entry.bind("<KeyRelease>", self.search_items)
        
        self.buscar_btn = ttk.Button(action_frame, text="Buscar", command=self.search_items)
        self.buscar_btn.pack(side=LEFT, padx=5)
        
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=3)
        main_frame.rowconfigure(0, weight=1)
        
        self.tree.bind("<<TreeviewSelect>>", self.on_item_select)
    
    def load_items(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        items = session.query(Item).order_by(Item.nombre).all()
        for item in items:
            self.tree.insert("", END, values=(
                item.id,
                item.nombre,
                item.cantidad,
                f"${item.valor_unitario:,.2f}",
                item.categoria.value,
                item.estado.value,
                item.tipo_compra.value
            ))
    
    def clear_form(self):
        self.nombre_entry.delete(0, END)
        self.desc_entry.delete(0, END)
        self.cantidad_entry.delete(0, END)
        self.cantidad_entry.insert(0, "1")
        self.valor_entry.delete(0, END)
        self.categoria_combo.set("")
        self.ubicacion_entry.delete(0, END)
        self.estado_combo.set(EstadoItem.DISPONIBLE.value)
        self.responsable_entry.delete(0, END)
        self.tipo_compra_combo.set(TipoCompra.COMPRADO.value)
        self.current_item = None
    
    def save_item(self):
        nombre = self.nombre_entry.get().strip()
        descripcion = self.desc_entry.get().strip()
        cantidad = self.cantidad_entry.get().strip()
        valor = self.valor_entry.get().strip()
        categoria = self.categoria_combo.get()
        ubicacion = self.ubicacion_entry.get().strip()
        estado = self.estado_combo.get()
        responsable = self.responsable_entry.get().strip()
        tipo_compra = self.tipo_compra_combo.get()
        
        if not nombre:
            messagebox.showerror("Error", "El nombre es obligatorio")
            return
        
        try:
            cantidad = int(cantidad)
            if cantidad <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Error", "Cantidad debe ser un número entero positivo")
            return
        
        try:
            valor = float(valor) if valor else 0.0
            if valor < 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Error", "Valor debe ser un número positivo")
            return
        
        if not categoria:
            messagebox.showerror("Error", "Seleccione una categoría")
            return
        
        if not estado:
            estado = EstadoItem.DISPONIBLE.value
        
        if not tipo_compra:
            tipo_compra = TipoCompra.COMPRADO.value
        
        try:
            if hasattr(self, 'current_item') and self.current_item:
                item = session.query(Item).get(self.current_item)
                item.nombre = nombre
                item.descripcion = descripcion
                item.cantidad = cantidad
                item.valor_unitario = valor
                item.categoria = CategoriaItem(categoria)
                item.ubicacion = ubicacion
                item.estado = EstadoItem(estado)
                item.responsable = responsable
                item.tipo_compra = TipoCompra(tipo_compra)
                messagebox.showinfo("Éxito", "Ítem actualizado correctamente")
            else:
                new_item = Item(
                    nombre=nombre,
                    descripcion=descripcion,
                    cantidad=cantidad,
                    valor_unitario=valor,
                    categoria=CategoriaItem(categoria),
                    ubicacion=ubicacion,
                    estado=EstadoItem(estado),
                    responsable=responsable,
                    tipo_compra=TipoCompra(tipo_compra)
                )
                session.add(new_item)
                messagebox.showinfo("Éxito", "Ítem agregado correctamente")
            
            session.commit()
            self.load_items()
            self.clear_form()
        except Exception as e:
            session.rollback()
            messagebox.showerror("Error", f"No se pudo guardar: {str(e)}")
    
    def on_item_select(self, event):
        selected = self.tree.focus()
        if selected:
            self.editar_btn.config(state=NORMAL)
            self.eliminar_btn.config(state=NORMAL)
            self.current_item = self.tree.item(selected)['values'][0]
        else:
            self.editar_btn.config(state=DISABLED)
            self.eliminar_btn.config(state=DISABLED)
            self.current_item = None
    
    def edit_item(self):
        if not self.current_item:
            return
        
        item = session.query(Item).get(self.current_item)
        if item:
            self.clear_form()
            self.nombre_entry.insert(0, item.nombre)
            self.desc_entry.insert(0, item.descripcion)
            self.cantidad_entry.delete(0, END)
            self.cantidad_entry.insert(0, str(item.cantidad))
            self.valor_entry.insert(0, str(item.valor_unitario))
            self.categoria_combo.set(item.categoria.value)
            self.ubicacion_entry.insert(0, item.ubicacion)
            self.estado_combo.set(item.estado.value)
            self.responsable_entry.insert(0, item.responsable)
            self.tipo_compra_combo.set(item.tipo_compra.value)
    
    def delete_item(self):
        if not self.current_item:
            return
        
        if messagebox.askyesno("Confirmar", "¿Está seguro de eliminar este ítem?"):
            try:
                item = session.query(Item).get(self.current_item)
                session.delete(item)
                session.commit()
                self.load_items()
                self.clear_form()
                messagebox.showinfo("Éxito", "Ítem eliminado correctamente")
            except Exception as e:
                session.rollback()
                messagebox.showerror("Error", f"No se pudo eliminar: {str(e)}")
    
    def search_items(self, event=None):
        query = self.buscar_entry.get().strip().lower()
        
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        items = session.query(Item).filter(Item.nombre.ilike(f"%{query}%")).order_by(Item.nombre).all()
        
        for item in items:
            self.tree.insert("", END, values=(
                item.id,
                item.nombre,
                item.cantidad,
                f"${item.valor_unitario:,.2f}",
                item.categoria.value,
                item.estado.value,
                item.tipo_compra.value
            ))

if __name__ == "__main__":
    root = Tk()
    app = InventarioApp(root)
    root.mainloop()