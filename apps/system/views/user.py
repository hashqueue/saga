from drf_spectacular.utils import extend_schema
from rest_framework import status, serializers
from rest_framework.permissions import AllowAny
from rest_framework.decorators import action
from rest_framework.generics import CreateAPIView
from rest_framework.viewsets import ModelViewSet
from rest_framework_simplejwt.views import TokenObtainPairView
from django_filters import rest_framework as filters

from utils.drf_utils.custom_json_response import JsonResponse, unite_response_format_schema
from system.serializers.users import UserRegisterSerializer, MyTokenObtainPairSerializer, UserCreateUpdateSerializer, \
    UserRetrieveSerializer, UserListDestroySerializer, UserResetPasswordSerializer, UserThinRetrieveSerializer, \
    GetAllUserSerializer, UserUpdateProfileSerializer, UserStatisticsSerializer
from system.models import User


# Create your views here.
@extend_schema(tags=['用户登录'])
class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer
    permission_classes = [AllowAny]

    @extend_schema(
        responses={
            200: {
                "type": "object",
                "properties": {
                    "success": {"type": "boolean", 'description': '操作是否成功'},
                    "message": {"type": "string", 'description': '业务提示消息'},
                    "data": {"type": "object",
                             'description': '数据',
                             "properties": {
                                 "refresh": {"type": "string", 'description': 'refresh JWT token'},
                                 "access": {"type": "string", 'description': 'JWT token'},
                                 "user_id": {"type": "integer", 'description': '用户ID'}
                             }}
                },
                "example": {
                    "success": True,
                    "message": "登录成功",
                    "data": {
                        "refresh": "eyJ0xxx.eyJ0xxx.lw-sX",
                        "access": "eyJ0xxx.eyJ0.xxx.3bAec",
                        "user_id": 1
                    }
                },
            },
        },
    )
    def post(self, request, *args, **kwargs):
        """
        用户登录
        * `username`字段可填写用户的`username`或`email`, 只要校验成功就可以`登录成功`
        * 响应体中`access`就是JWT的`token`值, 用于访问其他接口时做用户认证使用
        """
        return super().post(request, *args, **kwargs)


@extend_schema(tags=['用户注册'])
class UserRegisterView(CreateAPIView):
    serializer_class = UserRegisterSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        """
        用户注册
        """
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return JsonResponse(data=serializer.data, msg='注册成功', success=True, status=status.HTTP_201_CREATED,
                                headers=headers)

    @extend_schema(responses=unite_response_format_schema('user-register', UserRegisterSerializer()))
    def post(self, request, *args, **kwargs):
        """
        用户注册
        * `所有字段`都是`必填项`
        """
        return super().post(request, *args, **kwargs)


class UserFilter(filters.FilterSet):
    username = filters.CharFilter(field_name='username', lookup_expr='icontains',
                                  label='用户名(模糊搜索且不区分大小写)')

    class Meta:
        model = User
        fields = ['username']


@extend_schema(tags=['用户管理'])
class UserViewSet(ModelViewSet):
    queryset = User.objects.all().order_by('-id')
    filterset_class = UserFilter

    def get_serializer_class(self):
        if self.action in ['update', 'partial_update', 'create']:
            return UserCreateUpdateSerializer
        elif self.action in ['list', 'destroy']:
            return UserListDestroySerializer
        elif self.action == 'retrieve':
            return UserRetrieveSerializer
        elif self.action == 'reset_password':
            return UserResetPasswordSerializer
        elif self.action == 'update_profile':
            return UserUpdateProfileSerializer

    @extend_schema(responses=unite_response_format_schema('create-user', UserCreateUpdateSerializer()))
    def create(self, request, *args, **kwargs):
        """
        create user
        """
        res = super().create(request, *args, **kwargs)
        return JsonResponse(data=res.data, msg='success', success=True, status=status.HTTP_201_CREATED,
                            headers=res.headers)

    def list(self, request, *args, **kwargs):
        """
        select user list
        """
        res = super().list(request, *args, **kwargs)
        return JsonResponse(data=res.data, msg='success', success=True, status=status.HTTP_200_OK)

    @extend_schema(responses=unite_response_format_schema('select-user-detail', UserRetrieveSerializer()))
    def retrieve(self, request, *args, **kwargs):
        """
        select user detail
        """
        res = super().retrieve(request, *args, **kwargs)
        return JsonResponse(data=res.data, msg='success', success=True, status=status.HTTP_200_OK)

    @extend_schema(
        responses=unite_response_format_schema('update-user-detail', UserCreateUpdateSerializer()))
    def update(self, request, *args, **kwargs):
        """
        update user detail
        """
        res = super().update(request, *args, **kwargs)
        return JsonResponse(data=res.data, msg='success', success=True)

    @extend_schema(
        responses=unite_response_format_schema('partial-update-user-detail',
                                               UserCreateUpdateSerializer()))
    def partial_update(self, request, *args, **kwargs):
        """
        partial update user detail
        """
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """
        delete user
        """
        return super().destroy(request, *args, **kwargs)

    @extend_schema(responses=unite_response_format_schema('reset-password', is_null_data=True))
    @action(methods=['post'], detail=False, url_path='reset-password')
    def reset_password(self, request, pk=None, version=None):
        """
        重置当前登陆用户的密码
        """
        serializer = UserResetPasswordSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            if self.request.user.check_password(serializer.validated_data.get('old_password')):
                self.request.user.set_password(serializer.validated_data.get('new_password'))
                self.request.user.save(update_fields=['password'])
                return JsonResponse(data=None, msg='success', success=True)
            raise serializers.ValidationError('旧密码验证失败')

    @extend_schema(responses=unite_response_format_schema('update-profile', UserUpdateProfileSerializer()))
    @action(methods=['PUT'], detail=False, url_path='update-profile')
    def update_profile(self, request, pk=None, version=None):
        """
        修改当前登录用户个人信息
        """
        instance = self.request.user
        serializer = UserUpdateProfileSerializer(instance=instance, data=request.data, context={'request': request})
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            if getattr(instance, '_prefetched_objects_cache', None):
                # If 'prefetch_related' has been applied to a queryset, we need to
                # forcibly invalidate the prefetch cache on the instance.
                instance._prefetched_objects_cache = {}
            return JsonResponse(data=serializer.data, msg='success', success=True)

    @extend_schema(responses=unite_response_format_schema('get-profile', UserRetrieveSerializer()))
    @action(methods=['get'], detail=False, url_path='profile')
    def get_profile(self, request, pk=None, version=None):
        """
        获取当前用户个人信息
        """
        serializer = UserRetrieveSerializer(instance=self.request.user, context={'request': request})
        return JsonResponse(data=serializer.data, msg='success', success=True)

    @extend_schema(responses=unite_response_format_schema('get-all-users', GetAllUserSerializer()))
    @action(methods=['get'], detail=False, url_path='all')
    def get_all_users(self, request, pk=None, version=None):
        """
        查询所有用户列表
        """
        queryset = User.objects.all().order_by('-id')
        serializer = UserThinRetrieveSerializer(queryset, many=True, context={'request': request})
        return JsonResponse(data={'results': serializer.data, 'count': len(serializer.data)}, msg='success',
                            success=True)

    @extend_schema(responses=unite_response_format_schema('get-user-statistics', UserStatisticsSerializer()))
    @action(methods=['get'], detail=False, url_path='statistics')
    def get_user_statistics(self, request, pk=None, version=None):
        """
        获取当前用户拥有的聚合数据信息
        """
        serializer = UserStatisticsSerializer(instance=self.request.user, context={'request': request})
        return JsonResponse(data=serializer.data, msg='success', success=True)
