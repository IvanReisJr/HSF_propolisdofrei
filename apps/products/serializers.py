from rest_framework import serializers
from .models import Product, ProductStock
from apps.categories.serializers import CategorySerializer

class ProductStockSerializer(serializers.ModelSerializer):
    distributor_name = serializers.CharField(source='distributor.name', read_only=True)

    class Meta:
        model = ProductStock
        fields = ['id', 'distributor', 'distributor_name', 'current_stock', 'updated_at']

class ProductSerializer(serializers.ModelSerializer):
    category_detail = CategorySerializer(source='category', read_only=True)
    stocks = ProductStockSerializer(many=True, read_only=True)
    total_stock = serializers.IntegerField(source='get_total_stock', read_only=True)

    class Meta:
        model = Product
        fields = [
            'id', 'code', 'name', 'description', 'category', 'category_detail',
            'unit', 'cost_price', 'sale_price', 'min_stock', 'status',
            'total_stock', 'stocks', 'created_at', 'updated_at'
        ]
