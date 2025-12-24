from flask import Flask, request, jsonify
from flask_cors import CORS
import psycopg2
import redis
import os
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

# Database connection
def get_db_connection():
    return psycopg2.connect(
        host=os.getenv('DB_HOST'),
        database=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASS'),
        port=5432
    )

# Redis connection
redis_client = redis.Redis(
    host=os.getenv('REDIS_HOST'),
    port=6379,
    decode_responses=True
)

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'healthy',
        'service': 'order-service',
        'timestamp': datetime.now().isoformat()
    }), 200

@app.route('/api/orders', methods=['GET'])
def get_orders():
    """Get all orders"""
    try:
        # Check cache first
        cache_key = 'orders:all'
        cached = redis_client.get(cache_key)
        
        if cached:
            return jsonify({
                'source': 'cache',
                'data': json.loads(cached)
            }), 200

        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute('''
            SELECT o.id, o.user_id, o.total_amount, o.status, 
                   o.shipping_address, o.created_at, u.username
            FROM orders o
            JOIN users u ON o.user_id = u.id
            ORDER BY o.created_at DESC
        ''')
        
        orders = []
        for row in cur.fetchall():
            orders.append({
                'id': row[0],
                'user_id': row[1],
                'total_amount': float(row[2]),
                'status': row[3],
                'shipping_address': row[4],
                'created_at': row[5].isoformat(),
                'username': row[6]
            })
        
        cur.close()
        conn.close()
        
        # Cache for 2 minutes
        redis_client.setex(cache_key, 120, json.dumps(orders))
        
        return jsonify({
            'source': 'database',
            'data': orders
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/orders/<int:order_id>', methods=['GET'])
def get_order(order_id):
    """Get order by ID with items"""
    try:
        cache_key = f'order:{order_id}'
        cached = redis_client.get(cache_key)
        
        if cached:
            return jsonify({
                'source': 'cache',
                'data': json.loads(cached)
            }), 200

        conn = get_db_connection()
        cur = conn.cursor()
        
        # Get order details
        cur.execute('''
            SELECT o.id, o.user_id, o.total_amount, o.status,
                   o.shipping_address, o.created_at, u.username, u.email
            FROM orders o
            JOIN users u ON o.user_id = u.id
            WHERE o.id = %s
        ''', (order_id,))
        
        order_row = cur.fetchone()
        if not order_row:
            return jsonify({'error': 'Order not found'}), 404
        
        # Get order items
        cur.execute('''
            SELECT oi.id, oi.product_id, oi.quantity, oi.price,
                   p.name, p.description
            FROM order_items oi
            JOIN products p ON oi.product_id = p.id
            WHERE oi.order_id = %s
        ''', (order_id,))
        
        items = []
        for item in cur.fetchall():
            items.append({
                'id': item[0],
                'product_id': item[1],
                'quantity': item[2],
                'price': float(item[3]),
                'product_name': item[4],
                'product_description': item[5]
            })
        
        order = {
            'id': order_row[0],
            'user_id': order_row[1],
            'total_amount': float(order_row[2]),
            'status': order_row[3],
            'shipping_address': order_row[4],
            'created_at': order_row[5].isoformat(),
            'username': order_row[6],
            'email': order_row[7],
            'items': items
        }
        
        cur.close()
        conn.close()
        
        redis_client.setex(cache_key, 300, json.dumps(order))
        
        return jsonify({
            'source': 'database',
            'data': order
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/orders', methods=['POST'])
def create_order():
    """Create new order"""
    try:
        data = request.json
        user_id = data.get('user_id')
        items = data.get('items', [])  # [{product_id, quantity}, ...]
        shipping_address = data.get('shipping_address')
        
        if not user_id or not items:
            return jsonify({'error': 'Missing required fields'}), 400
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Calculate total
        total_amount = 0
        for item in items:
            cur.execute('SELECT price FROM products WHERE id = %s', (item['product_id'],))
            price = cur.fetchone()[0]
            total_amount += float(price) * item['quantity']
        
        # Create order
        cur.execute('''
            INSERT INTO orders (user_id, total_amount, shipping_address)
            VALUES (%s, %s, %s)
            RETURNING id
        ''', (user_id, total_amount, shipping_address))
        
        order_id = cur.fetchone()[0]
        
        # Create order items
        for item in items:
            cur.execute('SELECT price FROM products WHERE id = %s', (item['product_id'],))
            price = cur.fetchone()[0]
            
            cur.execute('''
                INSERT INTO order_items (order_id, product_id, quantity, price)
                VALUES (%s, %s, %s, %s)
            ''', (order_id, item['product_id'], item['quantity'], price))
            
            # Update stock
            cur.execute('''
                UPDATE products 
                SET stock_quantity = stock_quantity - %s
                WHERE id = %s
            ''', (item['quantity'], item['product_id']))
        
        conn.commit()
        cur.close()
        conn.close()
        
        # Invalidate cache
        redis_client.delete('orders:all')
        
        return jsonify({
            'message': 'Order created successfully',
            'order_id': order_id,
            'total_amount': total_amount
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/orders/<int:order_id>/status', methods=['PUT'])
def update_order_status(order_id):
    """Update order status"""
    try:
        data = request.json
        new_status = data.get('status')
        
        if new_status not in ['pending', 'processing', 'shipped', 'delivered', 'cancelled']:
            return jsonify({'error': 'Invalid status'}), 400
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute('''
            UPDATE orders 
            SET status = %s, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
            RETURNING id
        ''', (new_status, order_id))
        
        if cur.rowcount == 0:
            return jsonify({'error': 'Order not found'}), 404
        
        conn.commit()
        cur.close()
        conn.close()
        
        # Invalidate cache
        redis_client.delete(f'order:{order_id}')
        redis_client.delete('orders:all')
        
        return jsonify({'message': 'Order status updated'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
