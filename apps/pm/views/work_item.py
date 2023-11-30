from rest_framework import status
from rest_framework.viewsets import ModelViewSet
from drf_spectacular.utils import extend_schema
from django_filters import rest_framework as filters

from utils.drf_utils.custom_json_response import JsonResponse, unite_response_format_schema
from pm.serializers.work_items import WorkItemCreateUpdateSerializer, WorkItemRetrieveSerializer
from pm.models import WorkItem
from pm.tasks import make_changelog
from system.models import User
from system.tasks import send_email


class WorkItemFilter(filters.FilterSet):
    owner = filters.CharFilter(field_name='owner', lookup_expr='icontains', label='负责人(模糊搜索且不区分大小写)')
    name = filters.CharFilter(field_name='name', lookup_expr='icontains', label='工作项名称(模糊搜索且不区分大小写)')
    desc = filters.CharFilter(field_name='desc', lookup_expr='icontains', label='描述(模糊搜索且不区分大小写)')
    created_by = filters.CharFilter(field_name='created_by', lookup_expr='icontains',
                                    label='创建人(模糊搜索且不区分大小写)')
    sprint_id = filters.NumberFilter(field_name='sprint', label='所属迭代ID')

    class Meta:
        model = WorkItem
        fields = ['sprint_id', 'name', 'work_item_status', 'owner', 'work_item_type', 'priority', 'severity',
                  'bug_type', 'process_result', 'desc', 'created_by']


@extend_schema(tags=['工作项管理'])
class WorkItemViewSet(ModelViewSet):
    queryset = WorkItem.objects.all().order_by('-id')
    filterset_class = WorkItemFilter

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return WorkItemCreateUpdateSerializer
        elif self.action in ['retrieve', 'destroy', 'list']:
            return WorkItemRetrieveSerializer

    def perform_create(self, serializer):
        owner = User.objects.filter(username=serializer.validated_data.get('owner')).first()
        followers: list = serializer.validated_data.get('followers')
        if followers:
            followers_tmp = set(followers)
            followers_tmp.update([self.request.user, owner])
            serializer.save(created_by=self.request.user.username, updated_by=self.request.user.username,
                            followers=list(followers_tmp))
        else:
            serializer.save(created_by=self.request.user.username, updated_by=self.request.user.username,
                            followers=[self.request.user, owner])

    def perform_update(self, serializer):
        origin_work_item_obj = WorkItem.objects.get(id=self.kwargs.get('pk'))
        origin_data: dict = WorkItemCreateUpdateSerializer(instance=origin_work_item_obj).data
        # TODO: 这里只是给 更新WorkItem之前的followers发邮件提醒了，可能也需要给现在的followers也发邮件
        followers_email = [user.email for user in origin_work_item_obj.followers.all()]
        # 更新数据并入库
        owner = User.objects.filter(username=serializer.validated_data.get('owner')).first()
        current_followers: list = serializer.validated_data.get('followers')
        if current_followers:
            followers_tmp = set(current_followers)
            followers_tmp.update([self.request.user, owner])
            serializer.save(updated_by=self.request.user.username, followers=list(followers_tmp))
        else:
            serializer.save(updated_by=self.request.user.username, followers=[self.request.user, owner])
        # 生成变更记录并发送邮件
        # PS：celery的任务函数可以链式调用，当上一个任务函数执行成功后，再执行下一个任务函数，
        # 同时也会把上一个任务函数的返回值传给下一个任务函数，直到链式调用的所有任务函数执行完毕
        (make_changelog.s(origin_data, serializer.data, self.request.user.username,
                          followers_email) | send_email.s()).delay()

    @extend_schema(responses=unite_response_format_schema('create-work-item', WorkItemCreateUpdateSerializer()))
    def create(self, request, *args, **kwargs):
        """
        create work-item
        """
        res = super().create(request, *args, **kwargs)
        return JsonResponse(data=res.data, msg='success', success=True, status=status.HTTP_201_CREATED,
                            headers=res.headers)

    def list(self, request, *args, **kwargs):
        """
        select work-item list
        """
        res = super().list(request, *args, **kwargs)
        return JsonResponse(data=res.data, msg='success', success=True, status=status.HTTP_200_OK)

    @extend_schema(responses=unite_response_format_schema('select-work-item-detail', WorkItemRetrieveSerializer()))
    def retrieve(self, request, *args, **kwargs):
        """
        select work-item detail
        """
        res = super().retrieve(request, *args, **kwargs)
        return JsonResponse(data=res.data, msg='success', success=True, status=status.HTTP_200_OK)

    @extend_schema(
        responses=unite_response_format_schema('update-work-item-detail', WorkItemCreateUpdateSerializer()))
    def update(self, request, *args, **kwargs):
        """
        update work-item detail
        """
        res = super().update(request, *args, **kwargs)
        return JsonResponse(data=res.data, msg='success', success=True)

    @extend_schema(
        responses=unite_response_format_schema('partial-update-work-item-detail', WorkItemCreateUpdateSerializer()))
    def partial_update(self, request, *args, **kwargs):
        """
        partial update work-item detail
        """
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """
        delete work-item
        """
        return super().destroy(request, *args, **kwargs)
