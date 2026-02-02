from rest_framework import serializers
from .models import StockMovement
from apps.products.serializers import ProductSerializer

class StockMovementSerializer(serializers.ModelSerializer):
    product_detail = ProductSerializer(source='product', read_only=True)
    establishment_name = serializers.CharField(source='establishment.name', read_only=True)
    user_name = serializers.CharField(source='user.full_name', read_only=True)
    movement_type_display = serializers.CharField(source='get_movement_type_display', read_only=True)

    class Meta:
        model = StockMovement
        fields = [
            'id', 'establishment', 'establishment_name', 'product', 
            'product_detail', 'movement_type', 'movement_type_display',
            'quantity', 'previous_stock', 'new_stock', 'reason',
            'reference_id', 'reference_type', 'user', 'user_name', 
            'created_at'
        ]
