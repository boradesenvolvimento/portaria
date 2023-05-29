from rest_framework import serializers

from .models import *

class OcorrenciaEntregaSerializer(serializers.ModelSerializer):
    class Meta:
        model = OcorrenciaEntrega
        fields = '__all__'
        

class JustificativaEntregaSerializer(serializers.ModelSerializer):
    ocorrencias = OcorrenciaEntregaSerializer(many=True, read_only=True)

    class Meta:
        model = JustificativaEntrega
        fields = (
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

        