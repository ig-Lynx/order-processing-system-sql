from flask import Flask, render_template, request, redirect, url_for, jsonify
import mysql.connector

app = Flask(__name__)

# Database connection setup
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'dakshmysql',
    'database': 'ORDER_PROCESS_SYS'
}

def get_db_connection():
    return mysql.connector.connect(**db_config)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/customers')
def customers():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Customer")
    customers = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('customers.html', customers=customers)

@app.route('/products')
def products():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM Products")
    products = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('products.html', products=products)

@app.route('/place_order', methods=['GET', 'POST'])
def place_order():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    # Fetch customers and products for form dropdowns
    cursor.execute("SELECT CustomerID, Name FROM Customer")
    customers = cursor.fetchall()
    cursor.execute("SELECT ProductID, ProductName, Price , Stock FROM Products")
    products = cursor.fetchall()

    if request.method == 'POST':
        customer_id = request.form['customer']
        
        # Extract product IDs and quantities from the form data
        order_items = []
        for key, value in request.form.items():
            if key.startswith('quantity_') and int(value) > 0:
                product_id = key.replace('quantity_', '')
                quantity = int(value)
                order_items.append((product_id, quantity))

        if not order_items:
            cursor.close()
            conn.close()
            return "Please select at least one product with quantity greater than 0."

        # 1. Check stock availability
        for pid, qty in order_items:
            cursor.execute(
                "SELECT Stock FROM Products WHERE ProductID = %s",
                (pid,)
            )
            stock_result = cursor.fetchone()
            if not stock_result:
                cursor.close()
                conn.close()
                return f"Product {pid} not found."
            
            stock = stock_result['Stock']
            if stock < qty:
                cursor.close()
                conn.close()
                return f"Insufficient stock for product {pid}. Available: {stock}, Requested: {qty}"

        # 2. Insert order
        cursor.execute(
            "INSERT INTO `Order` (CustomerID, OrderDate, Status) VALUES (%s, CURDATE(), 'Placed')",
            (customer_id,)
        )
        order_id = cursor.lastrowid

        # 3. Insert items & decrease stock
        for pid, qty in order_items:
            cursor.execute(
                "INSERT INTO OrderItem (OrderID, ProductID, Quantity) VALUES (%s, %s, %s)",
                (order_id, pid, qty)
            )
            cursor.execute(
                "UPDATE Products SET Stock = Stock - %s WHERE ProductID = %s",
                (qty, pid)
            )

        conn.commit()
        cursor.close()
        conn.close()
        return redirect(url_for('list_orders', customer_id=customer_id))

    cursor.close()
    conn.close()
    return render_template('place_order.html', customers=customers, products=products)

@app.route('/orders/<int:customer_id>')
def list_orders(customer_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    # Fetch orders for customer
    cursor.execute("""
        SELECT OrderID, OrderDate, Status FROM `Order`
        WHERE CustomerID = %s ORDER BY OrderDate DESC
    """, (customer_id,))
    orders = cursor.fetchall()

    # Fetch customer info
    cursor.execute("SELECT Name FROM Customer WHERE CustomerID = %s", (customer_id,))
    customer = cursor.fetchone()
    cursor.close()
    conn.close()
    return render_template('list_orders.html', orders=orders, customer=customer)

@app.route('/order/<int:order_id>')
def order_details(order_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Order info
    cursor.execute("""
        SELECT o.OrderID, o.OrderDate, o.Status, o.CustomerID, c.Name AS CustomerName
        FROM `Order` o JOIN Customer c ON o.CustomerID = c.CustomerID
        WHERE o.OrderID = %s
    """, (order_id,))
    order = cursor.fetchone()

    # Order items with price and quantity
    cursor.execute("""
        SELECT p.ProductName, p.Price, oi.Quantity
        FROM OrderItem oi
        JOIN Products p ON oi.ProductID = p.ProductID
        WHERE oi.OrderID = %s
    """, (order_id,))
    items = cursor.fetchall()

    # Calculate total
    total = sum(item['Price'] * item['Quantity'] for item in items)

    cursor.close()
    conn.close()
    return render_template('order_details.html', order=order, items=items, total=total)

@app.route('/cancel_order/<int:order_id>')
def cancel_order(order_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE `Order` SET Status = 'Cancelled' WHERE OrderID = %s", (order_id,))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(request.referrer or url_for('index'))

@app.route('/customer_summary')
def customer_summary():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Get customer summary data
    cursor.execute("""
        SELECT c.CustomerID, c.Name,
            COUNT(o.OrderID) AS TotalOrders,
            COALESCE(SUM(p.Price * oi.Quantity), 0) AS TotalSpent
        FROM Customer c
        LEFT JOIN `Order` o ON c.CustomerID = o.CustomerID
        LEFT JOIN OrderItem oi ON o.OrderID = oi.OrderID
        LEFT JOIN Products p ON oi.ProductID = p.ProductID
        GROUP BY c.CustomerID, c.Name
        ORDER BY c.Name
    """)
    summary = cursor.fetchall()
    
    # Calculate overall statistics
    cursor.execute("""
        SELECT 
            COUNT(DISTINCT c.CustomerID) AS total_customers,
            COUNT(DISTINCT o.OrderID) AS total_orders,
            COALESCE(SUM(p.Price * oi.Quantity), 0) AS total_revenue
        FROM Customer c
        LEFT JOIN `Order` o ON c.CustomerID = o.CustomerID
        LEFT JOIN OrderItem oi ON o.OrderID = oi.OrderID
        LEFT JOIN Products p ON oi.ProductID = p.ProductID
    """)
    stats = cursor.fetchone()
    
    cursor.close()
    conn.close()
    
    return render_template('customer_summary.html', 
                         summary=summary, 
                         total_customers=stats['total_customers'],
                         total_orders=stats['total_orders'],
                         total_revenue=stats['total_revenue'])

@app.route('/add_customer', methods=['POST'])
def add_customer():
    try:
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone', '')
        
        if not name or not email:
            return jsonify({'success': False, 'message': 'Name and email are required'})
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if email already exists
        cursor.execute("SELECT CustomerID FROM Customer WHERE Email = %s", (email,))
        if cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'message': 'Customer with this email already exists'})
        
        # Insert new customer
        cursor.execute(
            "INSERT INTO Customer (Name, Email, Phone) VALUES (%s, %s, %s)",
            (name, email, phone)
        )
        customer_id = cursor.lastrowid
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True, 
            'customer_id': customer_id, 
            'customer_name': name
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/add_product', methods=['POST'])
def add_product():
    try:
        name = request.form.get('name')
        price = request.form.get('price')
        stock = request.form.get('stock')
        
        if not name or not price or not stock:
            return jsonify({'success': False, 'message': 'All fields are required'})
        
        # Validate numeric values
        try:
            price = float(price)
            stock = int(stock)
        except ValueError:
            return jsonify({'success': False, 'message': 'Invalid price or stock value'})
        
        if price < 0 or stock < 0:
            return jsonify({'success': False, 'message': 'Price and stock must be non-negative'})
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if product name already exists
        cursor.execute("SELECT ProductID FROM Products WHERE ProductName = %s", (name,))
        if cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'message': 'Product with this name already exists'})
        
        # Insert new product
        cursor.execute(
            "INSERT INTO Products (ProductName, Price, Stock) VALUES (%s, %s, %s)",
            (name, price, stock)
        )
        product_id = cursor.lastrowid
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True, 
            'product_id': product_id, 
            'product_name': name
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/delete_product', methods=['POST'])
def delete_product():
    try:
        data = request.get_json()
        product_id = data.get('product_id')
        
        if not product_id:
            return jsonify({'success': False, 'message': 'Product ID is required'})
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if product exists
        cursor.execute("SELECT ProductName FROM Products WHERE ProductID = %s", (product_id,))
        product = cursor.fetchone()
        if not product:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'message': 'Product not found'})
        
        # Check if product is used in any orders
        cursor.execute("SELECT COUNT(*) as count FROM OrderItem WHERE ProductID = %s", (product_id,))
        order_count = cursor.fetchone()
        if order_count and order_count[0] > 0:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'message': 'Cannot delete product that has been ordered. Product is referenced in existing orders.'})
        
        # Delete the product
        cursor.execute("DELETE FROM Products WHERE ProductID = %s", (product_id,))
        
        if cursor.rowcount == 0:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'message': 'Product not found or already deleted'})
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Product deleted successfully'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/update_stock', methods=['POST'])
def update_stock():
    try:
        data = request.get_json()
        product_id = data.get('product_id')
        new_stock = data.get('new_stock')
        
        if not product_id or new_stock is None:
            return jsonify({'success': False, 'message': 'Product ID and new stock are required'})
        
        # Validate stock value
        try:
            new_stock = int(new_stock)
        except ValueError:
            return jsonify({'success': False, 'message': 'Invalid stock value'})
        
        if new_stock < 0:
            return jsonify({'success': False, 'message': 'Stock must be non-negative'})
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if product exists
        cursor.execute("SELECT ProductName FROM Products WHERE ProductID = %s", (product_id,))
        product = cursor.fetchone()
        if not product:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'message': 'Product not found'})
        
        # Update the stock
        cursor.execute("UPDATE Products SET Stock = %s WHERE ProductID = %s", (new_stock, product_id))
        
        if cursor.rowcount == 0:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'message': 'Failed to update stock'})
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Stock updated successfully', 'new_stock': new_stock})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

if __name__ == '__main__':
    app.run(debug=True)
