from rest_framework import serializers

from transit_slip.models import Letter, TransitSlip

class LetterSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Letter
        fields = ['from_unit', 'to_unit', 'transit_slip',]

class LetterListingField(serializers.RelatedField):
    def to_representation(self, value):
        to_unit_code = value.to_unit.pk
        from_unit_code = value.from_unit.pk
        ltr_no = value.ltr_no
        return (f'{from_unit_code}__{to_unit_code}__{ltr_no}')

class TransitSlipSerializer(serializers.ModelSerializer):
    date = serializers.DateTimeField(format="%d/%m/%Y")
    dst = serializers.StringRelatedField()
    prepared_by = serializers.StringRelatedField()
    ltrs = LetterListingField(many=True, read_only=True)

    class Meta:
        model = TransitSlip
        fields = ['id', 'date', 'dst', 'prepared_by', 'ltrs']