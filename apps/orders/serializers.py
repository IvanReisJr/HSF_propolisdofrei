from rest_framework import serializers
from .models import Order, OrderItem
from apps.products.serializers import ProductSerializer

class OrderItemSerializer(serializers.ModelSerializer):
    product_detail = ProductSerializer(source='product', read_only=True)

    class Meta:
        model = OrderItem
        fields = [
            'id', 'order', 'product', 'product_detail', 
            'quantity', 'unit_price', 'total_price', 'created_at'
        ]
        read_only_fields = ['total_price']

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    establishment_name = serializers.CharField(source='establishment.name', read_only=True)
    distributor_name = serializers.CharField(source='distributor.name', read_only=True)
    user_name = serializers.CharField(source='user.full_name', read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'establishment', 'establishment_name',
            'distributor', 'distributor_name', 'user', 'user_name',
            'status', 'total_amount', 'notes', 'items', 
            'created_at', 'updated_at'
        ]
        read_only_fields = ['total_amount']
