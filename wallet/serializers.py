from rest_framework import serializers
from wallet.models import Currency


class CurrencySerializer(serializers.ModelSerializer):
    class Meta:
        model = Currency
        fields = ('id','abrev','name')

    '''id = serializers.IntegerField(read_only=True)
    abrev = serializers.CharField(required=True, allow_blank=True, max_length=3)
    name = serializers.CharField(required=True,max_length=20)

    def create(self, validated_data):
        return Currency.objects.create(**validated_data)

    def update(self, instance, validated_data):
        instance.abrev = validated_data.get('abrev', instance.abrev)
        instance.name = validated_data.get('name', instance.name)
        instance.save()
        return instance'''
