from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from drf_spectacular.types import OpenApiTypes
from django_celery_beat.models import IntervalSchedule, CrontabSchedule, PeriodicTask


class IntervalScheduleSerializer(serializers.ModelSerializer):

    class Meta:
        model = IntervalSchedule
        fields = '__all__'


class CrontabScheduleSerializer(serializers.ModelSerializer):

    class Meta:
        model = CrontabSchedule
        exclude = ('timezone',)


class PeriodicTaskCreateUpdateSerializer(serializers.ModelSerializer):
    schedule_type = serializers.ChoiceField(choices=((1, 'interval'), (2, 'crontab')), help_text='定时任务类型',
                                            write_only=True)
    interval = IntervalScheduleSerializer(required=False, allow_null=True)
    crontab = CrontabScheduleSerializer(required=False, allow_null=True)

    class Meta:
        model = PeriodicTask
        exclude = ('queue', 'exchange', 'routing_key', 'headers', 'expires', 'expire_seconds', 'solar', 'clocked')

    @staticmethod
    def check_schedule_type(validated_data):
        if validated_data.get('interval') and validated_data.get('crontab'):
            raise serializers.ValidationError('interval和crontab参数不能同时存在')
        schedule_type = validated_data.pop('schedule_type')
        if schedule_type == 1:
            if not validated_data.get('interval'):
                raise serializers.ValidationError('interval参数不能为空')
            interval = validated_data.pop('interval')
            interval_schedule, _ = IntervalSchedule.objects.get_or_create(**interval)
            validated_data['interval'] = interval_schedule
        else:
            if not validated_data.get('crontab'):
                raise serializers.ValidationError('crontab参数不能为空')
            crontab = validated_data.pop('crontab')
            crontab_schedule, _ = CrontabSchedule.objects.get_or_create(**crontab)
            validated_data['crontab'] = crontab_schedule

    def create(self, validated_data):
        self.check_schedule_type(validated_data)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        self.check_schedule_type(validated_data)
        return super().update(instance, validated_data)


class PeriodicTaskRetrieveSerializer(serializers.ModelSerializer):
    schedule_type = serializers.SerializerMethodField(help_text='定时任务类型(1, "interval"), (2, "crontab")',
                                                      read_only=True)
    interval = IntervalScheduleSerializer(required=False, allow_null=True)
    crontab = CrontabScheduleSerializer(required=False, allow_null=True)

    class Meta:
        model = PeriodicTask
        exclude = ('queue', 'exchange', 'routing_key', 'headers', 'expires', 'expire_seconds', 'solar', 'clocked')

    @extend_schema_field(OpenApiTypes.INT)
    def get_schedule_type(self, obj: PeriodicTask):
        return 1 if obj.interval else 2
