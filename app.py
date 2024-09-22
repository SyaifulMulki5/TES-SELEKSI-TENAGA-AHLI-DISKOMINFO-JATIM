from flask import Flask, jsonify, request
from flask_mysqldb import MySQL

app = Flask(__name__)
# mysql config
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'agent_penjualan'
mysql = MySQL(app)


@app.route('/')
def home():
    return "TES SELEKSI TENAGA AHLI DISKOMINFO JATIM"

@app.route('/api/products',methods=['GET'])
def list_products():
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM products")
    products = cursor.fetchall()
    print (products)
    cursor.close()

    results=[]
    for product in products:
      results.append({
      "id":product[0],
      "name":product[1],
      "price":product[2],
      "stock":product[3],
      "sold":product[4],
      "created_at":product[5].isoformat(),
      "updated_at":product[6].isoformat()
      })

    product = {
    "message": "Product List",
    "data": results
}
    return jsonify(product)


@app.route('/api/products' ,methods=['POST'])
def create_product():
  data = request.json
    # Validate required fields
  if not all(key in data for key in ['name', 'price', 'stock']):
        return jsonify({"error": "Missing required fields"}), 422

    # Validate data types and constraints
  if not isinstance(data['name'], str) or not data['name']:
        return jsonify({"error": "Name must be a non-empty string"}), 422
    
  if not isinstance(data['price'], int) or data['price'] < 1:
        return jsonify({"error": "Price must be an integer greater than or equal to 1"}), 422
    
  if not isinstance(data['stock'], int) or data['stock'] < 0:
        return jsonify({"error": "Stock must be an integer greater than or equal to 0"}), 422
  product_data = {
        'name': data['name'],
        'price': data['price'],
        'stock': data['stock']
    }
  cursor = mysql.connection.cursor()
  sql = "INSERT INTO PRODUCTS (name, price, stock) VALUES (%(name)s, %(price)s, %(stock)s)"
  cursor.execute(sql, product_data)
  mysql.connection.commit()
  product_id = cursor.lastrowid

  cursor.execute("SELECT id, name, price, stock, sold, created_at, updated_at FROM PRODUCTS WHERE id = %s", (product_id,))
  new_product = cursor.fetchone()
  cursor.close()

  product = {
        "message": "Product created successfully",
        "data": {
            "id": new_product[0],          # id
            "name": new_product[1],        # name
            "price": new_product[2],       # price
            "stock": new_product[3],       # stock
            "sold": new_product[4],        # sold
            "created_at": new_product[5],  # created_at
            "updated_at": new_product[6]   # updated_at
        }
    }

  return jsonify(product), 201

@app.route('/api/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    cursor = None
    try:
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT id, name, price, stock, sold, created_at, updated_at FROM PRODUCTS WHERE id = %s", (product_id,))
        product = cursor.fetchone()

        if product is None:
            return jsonify({"error": "Product not found"}), 404

        # Mengembalikan data dengan format yang diinginkan
        return jsonify({
            "message": "Product Detail",
            "data": {
                "id": product[0],
                "name": product[1],
                "price": product[2],
                "stock": product[3],
                "sold": product[4],
                "created_at": product[5].isoformat() + 'Z',
                "updated_at": product[6].isoformat() + 'Z'
            }
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if cursor:
            cursor.close()

@app.route('/api/products/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    data = request.json

    # Validasi field yang wajib diisi
    if not any(key in data for key in ['name', 'price', 'stock']):
        return jsonify({"error": "At least one field (name, price, stock) must be provided"}), 422

    # Validasi tipe data
    if 'name' in data and (not isinstance(data['name'], str) or not data['name']):
        return jsonify({"error": "Name must be a non-empty string"}), 422
    
    if 'price' in data and (not isinstance(data['price'], (int, float)) or data['price'] < 1):
        return jsonify({"error": "Price must be a number greater than or equal to 1"}), 422
    
    if 'stock' in data and (not isinstance(data['stock'], int) or data['stock'] < 0):
        return jsonify({"error": "Stock must be an integer greater than or equal to 0"}), 422

    cursor = None
    try:
        cursor = mysql.connection.cursor()

        # Update data produk berdasarkan ID
        updates = []
        values = []
        
        if 'name' in data:
            updates.append("name = %s")
            values.append(data['name'])
        
        if 'price' in data:
            updates.append("price = %s")
            values.append(data['price'])
        
        if 'stock' in data:
            updates.append("stock = %s")
            values.append(data['stock'])

        # Menyusun query
        sql = f"UPDATE PRODUCTS SET {', '.join(updates)} WHERE id = %s"
        values.append(product_id)
        cursor.execute(sql, tuple(values))
        mysql.connection.commit()

        # Mengecek apakah ada yang diperbarui
        if cursor.rowcount == 0:
            return jsonify({"error": "Product not found"}), 404

        # Mengambil data produk yang diperbarui
        cursor.execute("SELECT id, name, price, stock, sold, created_at, updated_at FROM PRODUCTS WHERE id = %s", (product_id,))
        product = cursor.fetchone()

        return jsonify({
            "message": "Product updated successfully",
            "data": {
                "id": product[0],
                "name": product[1],
                "price": product[2],
                "stock": product[3],
                "sold": product[4],
                "created_at": product[5].isoformat() + 'Z',
                "updated_at": product[6].isoformat() + 'Z'
            }
        })
    except Exception as e:
        mysql.connection.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        if cursor:
            cursor.close()

@app.route('/api/products/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    cursor = None
    try:
        cursor = mysql.connection.cursor()

        # Mengambil data produk sebelum dihapus
        cursor.execute("SELECT id, name, price, stock, sold, created_at, updated_at FROM PRODUCTS WHERE id = %s", (product_id,))
        product = cursor.fetchone()

        # Jika produk tidak ditemukan, kembalikan pesan error
        if product is None:
            return jsonify({"error": "Product not found"}), 404

        # Menghapus produk dari database
        cursor.execute("DELETE FROM PRODUCTS WHERE id = %s", (product_id,))
        mysql.connection.commit()

        # Mengembalikan data produk yang dihapus
        return jsonify({
            "message": "Product deleted successfully",
            "data": {
                "id": product[0],
                "name": product[1],
                "price": product[2],
                "stock": product[3],
                "sold": product[4],
                "created_at": product[5].isoformat() + 'Z',
                "updated_at": product[6].isoformat() + 'Z'
            }
        })
    except Exception as e:
        mysql.connection.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        if cursor:
            cursor.close()

@app.route('/api/orders', methods=['GET'])
def get_orders():
    cursor = None
    try:
        cursor = mysql.connection.cursor()
        
        # Mengambil daftar pesanan
        cursor.execute("SELECT id, created_at, updated_at FROM ORDERS")
        orders = cursor.fetchall()
        
        order_list = []
        
        for order in orders:
            order_id = order[0]
            created_at = order[1]
            updated_at = order[2]
            
            # Mengambil produk terkait untuk setiap pesanan
            cursor.execute("""
                SELECT p.id, p.name, p.price, op.quantity, 
                       p.stock, p.sold, p.created_at, p.updated_at 
                FROM ORDER_PRODUCTS op
                JOIN PRODUCTS p ON op.product_id = p.id
                WHERE op.order_id = %s
            """, (order_id,))
            
            products = cursor.fetchall()
            product_list = []
            
            for product in products:
                product_list.append({
                    "id": product[0],
                    "name": product[1],
                    "price": product[2],
                    "quantity": product[3],
                    "stock": product[4],
                    "sold": product[5],
                    "created_at": product[6].isoformat() + 'Z',
                    "updated_at": product[7].isoformat() + 'Z'
                })

            order_list.append({
                "id": order_id,
                "products": product_list,
                "created_at": created_at.isoformat() + 'Z',
                "updated_at": updated_at.isoformat() + 'Z'
            })

        return jsonify({
            "message": "Order List",
            "data": order_list
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if cursor:
            cursor.close()





@app.route('/api/orders', methods=['GET'])
def fetch_orders():  # Ganti nama fungsi dari get_orders ke fetch_orders
    cursor = mysql.connection.cursor()
    cursor.execute("""
        SELECT 
            o.id AS order_id,
            o.created_at AS order_created_at,
            o.updated_at AS order_updated_at,
            o.product_id,
            p.name,
            p.price,
            o.quantity,
            p.stock,
            p.sold,
            p.created_at AS product_created_at,
            p.updated_at AS product_updated_at
        FROM 
            ORDERS o
        JOIN 
            PRODUCTS p ON o.product_id = p.id;
    """)

    orders = {}
    for row in cursor.fetchall():
        order_id = row[0]
        
        if order_id not in orders:
            orders[order_id] = {
                "id": order_id,
                "products": [],
                "created_at": row[1],
                "updated_at": row[2]
            }
        
        orders[order_id]["products"].append({
            "id": row[3],
            "name": row[4],
            "price": row[5],
            "quantity": row[6],
            "stock": row[7],
            "sold": row[8],
            "created_at": row[9],
            "updated_at": row[10],
        })

    cursor.close()

    return jsonify({
        "message": "Order List",
        "data": list(orders.values())
    })


app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'username'
app.config['MYSQL_PASSWORD'] = 'password'
app.config['MYSQL_DB'] = 'agent_penjualan'

mysql = MySQL(app)
@app.route('/orders', methods=['GET'])
def get_orders_list():
    cur = mysql.connection.cursor()

    # Ambil semua order
    cur.execute("SELECT * FROM orders")
    orders = cur.fetchall()
    
    order_list = []

    for order in orders:
        order_id = order[0]  # id
        created_at = order[2]
        updated_at = order[3]

        # Ambil produk terkait dengan order
        cur.execute("""
            SELECT p.id, p.name, p.price, op.quantity, p.stock, p.sold, p.created_at, p.updated_at
            FROM order_products op
            JOIN products p ON op.product_id = p.id
            WHERE op.order_id = %s
        """, (order_id,))
        
        products = cur.fetchall()
        product_list = []

        for product in products:
            product_list.append({
                'id': product[0],
                'name': product[1],
                'price': product[2],
                'quantity': product[3],
                'stock': product[4],
                'sold': product[5],
                'created_at': product[6].isoformat() + "Z",
                'updated_at': product[7].isoformat() + "Z"
            })

        order_list.append({
            'id': order_id,
            'products': product_list,
            'created_at': created_at.isoformat() + "Z",
            'updated_at': updated_at.isoformat() + "Z"
        })

    cur.close()
    
    return jsonify({
        "message": "Order List",
        "data": order_list
    })

   
if __name__ == '__main__':
    app.run(debug=True)
