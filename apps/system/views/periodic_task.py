from rest_framework import status
from rest_framework.viewsets import ModelViewSet
from drf_spectacular.utils import extend_schema
from django_celery_beat.models import PeriodicTask
from django_filters import rest_framework as filters

from system.serializers.periodic_tasks import PeriodicTaskCreateUpdateSerializer, PeriodicTaskRetrieveSerializer
from utils.drf_utils.custom_json_response import JsonResponse, unite_response_format_schema


class PeriodicTaskFilter(filters.FilterSet):
    name = filters.CharFilter(field_name='name', lookup_expr='exact', label='任务名称(不支持模糊搜索)')

    class Meta:
        model = PeriodicTask
        fields = ['name']


@extend_schema(tags=['定时任务管理'])
class PeriodicTaskViewSet(ModelViewSet):
    queryset = PeriodicTask.objects.all().order_by('-id')
    filterset_class = PeriodicTaskFilter

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return PeriodicTaskCreateUpdateSerializer
        elif self.action in ['retrieve', 'destroy', 'list']:
            return PeriodicTaskRetrieveSerializer

    @extend_schema(responses=unite_response_format_schema('create-periodic-task',
                                                          PeriodicTaskCreateUpdateSerializer()))
    def create(self, request, *args, **kwargs):
        """
        create periodic task
        """
        res = super().create(request, *args, **kwargs)
        return JsonResponse(data=res.data, msg='success', success=True, status=status.HTTP_201_CREATED,
                            headers=res.headers)

    def list(self, request, *args, **kwargs):
        """
        select periodic task list
        """
        res = super().list(request, *args, **kwargs)
        return JsonResponse(data=res.data, msg='success', success=True, status=status.HTTP_200_OK)

    @extend_schema(responses=unite_response_format_schema('select-periodic-task-detail',
                                                          PeriodicTaskRetrieveSerializer()))
    def retrieve(self, request, *args, **kwargs):
        """
        select periodic task detail
        """
        res = super().retrieve(request, *args, **kwargs)
        return JsonResponse(data=res.data, msg='success', success=True, status=status.HTTP_200_OK)

    @extend_schema(
        responses=unite_response_format_schema('update-periodic-task-detail',
                                               PeriodicTaskCreateUpdateSerializer()))
    def update(self, request, *args, **kwargs):
        """
        update periodic task detail
        """
        res = super().update(request, *args, **kwargs)
        return JsonResponse(data=res.data, msg='success', success=True)

    @extend_schema(
        responses=unite_response_format_schema('partial-update-periodic-task-detail',
                                               PeriodicTaskCreateUpdateSerializer()))
    def partial_update(self, request, *args, **kwargs):
        """
        partial update periodic task detail
        """
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """
        delete periodic task
        """
        return super().destroy(request, *args, **kwargs)
