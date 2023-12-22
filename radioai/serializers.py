from rest_framework import serializers
from .models import SchedulingTasks

class AudioConversionRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = SchedulingTasks
        fields = '__all__'
