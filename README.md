# Order Processing System (SQL)

A Flask-based web application for managing orders with MySQL database backend. This system provides a complete order management solution with customer management, product inventory, and order processing capabilities.

## Features

- **Customer Management**: View and manage customer information
- **Product Management**: Browse products with real-time stock information
- **Order Processing**: Place orders with automatic stock validation and updates
- **Order Tracking**: View order history and detailed order information
- **Stock Management**: Automatic stock decrement on order placement
- **Responsive Web Interface**: Clean, modern UI using HTML templates

## Technology Stack

- **Backend**: Flask (Python)
- **Database**: MySQL
- **Frontend**: HTML, CSS, JavaScript
- **Database Connector**: mysql-connector-python

## Database Schema

The system uses the following main tables:

- `Customer`: Stores customer information
- `Products`: Product catalog with pricing and stock
- `Order`: Order header information
- `OrderItem`: Line items for each order

## Installation

### Prerequisites

- Python 3.7+
- MySQL Server
- pip package manager

### Setup Instructions

1. **Clone the repository**
   ```bash
   git clone https://github.com/ig-Lynx/order-processing-system-sql.git
   cd order-processing-system-sql
   ```

2. **Create and activate virtual environment**
   ```bash
   python -m venv venv
   # On Windows
   venv\Scripts\activate
   # On Unix/MacOS
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install flask mysql-connector-python
   ```

4. **Database Setup**
   
   Create a MySQL database named `ORDER_PROCESS_SYS` and run the following SQL script to create the required tables:

   ```sql
   -- Customer Table
   CREATE TABLE Customer (
       CustomerID INT AUTO_INCREMENT PRIMARY KEY,
       Name VARCHAR(100) NOT NULL,
       Email VARCHAR(100) UNIQUE NOT NULL,
       Phone VARCHAR(20),
       Address TEXT
   );

   -- Products Table
   CREATE TABLE Products (
       ProductID INT AUTO_INCREMENT PRIMARY KEY,
       ProductName VARCHAR(100) NOT NULL,
       Description TEXT,
       Price DECIMAL(10,2) NOT NULL,
       Stock INT NOT NULL DEFAULT 0
   );

   -- Order Table
   CREATE TABLE `Order` (
       OrderID INT AUTO_INCREMENT PRIMARY KEY,
       CustomerID INT NOT NULL,
       OrderDate DATE NOT NULL,
       Status VARCHAR(20) DEFAULT 'Placed',
       FOREIGN KEY (CustomerID) REFERENCES Customer(CustomerID)
   );

   -- OrderItem Table
   CREATE TABLE OrderItem (
       OrderItemID INT AUTO_INCREMENT PRIMARY KEY,
       OrderID INT NOT NULL,
       ProductID INT NOT NULL,
       Quantity INT NOT NULL,
       FOREIGN KEY (OrderID) REFERENCES `Order`(OrderID),
       FOREIGN KEY (ProductID) REFERENCES Products(ProductID)
   );
   ```

5. **Configure Database Connection**
   
   Update the database configuration in `app.py`:
   ```python
   db_config = {
       'host': 'localhost',
       'user': 'your_mysql_username',
       'password': 'your_mysql_password',
       'database': 'ORDER_PROCESS_SYS'
   }
   ```

6. **Run the application**
   ```bash
   python app.py
   ```

   The application will be available at `http://localhost:5000`

## Usage

### Main Features

1. **Dashboard**: Home page with navigation to all main features
2. **Customers**: View all customers in the system
3. **Products**: Browse product catalog with current stock levels
4. **Place Order**: Create new orders with multiple products
   - Automatic stock validation
   - Real-time price calculation
   - Stock decrement on successful order placement
5. **Order History**: View orders by customer
6. **Order Details**: Detailed view of individual orders with line items

### Order Processing Flow

1. Select a customer from the dropdown
2. Choose products and specify quantities
3. System validates stock availability
4. Order is created and stock is automatically updated
5. Redirect to order confirmation page

## API Endpoints

- `GET /` - Home page
- `GET /customers` - List all customers
- `GET /products` - List all products
- `GET|POST /place_order` - Place new order
- `GET /orders/<customer_id>` - View customer's orders
- `GET /order/<order_id>` - View order details

## Security Considerations

- Database credentials should be moved to environment variables
- Input validation should be enhanced for production
- Consider implementing user authentication
- Add CSRF protection for forms

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is open source and available under the MIT License.

**Note**: This is the SQL-based version of the order processing system.
