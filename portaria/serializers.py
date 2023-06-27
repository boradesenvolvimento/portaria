from rest_framework import serializers

from .models import *

class OcorrenciaEntregaSerializer(serializers.ModelSerializer):
    data_ocorrencia = serializers.DateField(format="%d-%m-%Y")
    
    class Meta:
        model = OcorrenciaEntrega
        fields = '__all__'
        

class JustificativaEntregaSerializer(serializers.ModelSerializer):
    ocorrencias = OcorrenciaEntregaSerializer(many=True, read_only=True)
    data_emissao = serializers.DateField(format="%d-%m-%Y")
    lead_time = serializers.DateField(format="%d-%m-%Y")

    class Meta:
        model = JustificativaEntrega
        fields = (
            "id",
            "conhecimento",
            "data_emissao",
            "destinatario",
            "remetente",
            "peso",
            "lead_time",
            "em_aberto",
            "local_entreg",
            "nota_fiscal",
            "ocorrencias"
        )
        depth = 1
        