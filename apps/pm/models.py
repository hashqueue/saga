from django.db import models
from utils.django_utils.base_model import BaseModel
from system.models import User


class Project(BaseModel):
    """
    项目
    """
    PROJECT_STATUS_CHOICES = [(1, '未开始'), (2, '进行中'), (3, '已完成')]
    name = models.CharField(max_length=128, verbose_name="项目名称", help_text='项目名称', db_index=True)
    members = models.ManyToManyField(User, blank=True, verbose_name="项目成员", help_text='项目成员')
    owner = models.CharField(max_length=150, verbose_name='负责人', help_text='负责人', db_index=True)
    project_status = models.PositiveSmallIntegerField(choices=PROJECT_STATUS_CHOICES, default=1,
                                                      verbose_name='项目状态', help_text='项目状态', db_index=True)

    class Meta:
        db_table = 'pm_project'
        verbose_name = '项目'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name


class Sprint(BaseModel):
    """
    迭代
    """
    SPRINT_STATUS_CHOICES = [(1, '未开始'), (2, '进行中'), (3, '已完成')]
    name = models.CharField(max_length=128, verbose_name="迭代名称", help_text='迭代名称', db_index=True)
    project = models.ForeignKey(Project, null=True, blank=True, on_delete=models.SET_NULL, verbose_name="所属项目",
                                help_text='所属项目')
    owner = models.CharField(max_length=150, verbose_name='负责人', help_text='负责人', db_index=True)
    started_at = models.DateTimeField(null=True, blank=True, verbose_name="开始时间", help_text='开始时间')
    finished_at = models.DateTimeField(null=True, blank=True, verbose_name="完成时间", help_text='完成时间')
    sprint_status = models.PositiveSmallIntegerField(choices=SPRINT_STATUS_CHOICES, default=1, verbose_name='迭代状态',
                                                     help_text='迭代状态', db_index=True)

    class Meta:
        db_table = 'pm_sprint'
        verbose_name = '迭代'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name


class WorkItem(BaseModel):
    """
    工作项
    """
    WORK_ITEM_TYPE_CHOICES = [(1, '需求'), (2, '任务'), (3, '缺陷')]
    BUG_TYPE_CHOICES = [
        (1, '功能问题'), (2, '性能问题'), (3, '接口问题'), (4, '安全问题'), (5, 'UI界面问题'), (6, '易用性问题'),
        (7, '兼容问题'), (8, '数据问题'), (9, '逻辑问题'), (10, '需求问题')
    ]
    PRIORITY_CHOICES = [(1, '最低'), (2, '较低'), (3, '普通'), (4, '较高'), (5, '最高')]
    PROCESS_RESULT_CHOICES = [
        (1, '不予处理'), (2, '延期处理'), (3, '外部原因'), (4, '需求变更'), (5, '转需求'), (6, '挂起'), (7, '设计如此'),
        (8, '重复缺陷'), (9, '无法重现')
    ]
    SEVERITY_CHOICES = [(1, '保留'), (2, '建议'), (3, '提示'), (4, '一般'), (5, '严重'), (6, '致命')]
    WORK_ITEM_STATUS_CHOICES = [
        (1, '未开始'), (2, '待处理'), (3, '重新打开'), (4, '进行中'), (5, '实现中'), (6, '已完成'), (7, '修复中'),
        (8, '已实现'), (9, '关闭'), (10, '已修复'), (11, '已验证'), (12, '已拒绝')
    ]
    name = models.CharField(max_length=128, verbose_name="工作项名称", help_text='工作项名称', db_index=True)
    owner = models.CharField(max_length=150, verbose_name='负责人', help_text='负责人', db_index=True)
    work_item_type = models.PositiveSmallIntegerField(choices=WORK_ITEM_TYPE_CHOICES, verbose_name='工作项类型',
                                                      help_text='工作项类型', db_index=True)
    priority = models.PositiveSmallIntegerField(choices=PRIORITY_CHOICES, verbose_name='优先级', help_text='优先级',
                                                db_index=True)
    sprint = models.ForeignKey(Sprint, null=True, blank=True, on_delete=models.SET_NULL, verbose_name="所属迭代",
                               help_text='所属迭代')
    work_item_status = models.PositiveSmallIntegerField(choices=WORK_ITEM_STATUS_CHOICES, default=1,
                                                        verbose_name='状态', help_text='状态', db_index=True)
    severity = models.PositiveSmallIntegerField(null=True, blank=True, choices=SEVERITY_CHOICES,
                                                verbose_name='缺陷严重程度', help_text='缺陷严重程度', db_index=True)
    bug_type = models.PositiveSmallIntegerField(choices=BUG_TYPE_CHOICES, null=True, blank=True,
                                                verbose_name='缺陷类型', help_text='缺陷类型', db_index=True)
    process_result = models.PositiveSmallIntegerField(choices=PROCESS_RESULT_CHOICES, null=True, blank=True,
                                                      verbose_name='缺陷处理结果', help_text='缺陷处理结果',
                                                      db_index=True)
    desc = models.TextField(blank=True, default='', verbose_name='描述', help_text='描述')
    deadline = models.DateTimeField(null=True, blank=True, verbose_name="截止日期", help_text='截止日期')
    followers = models.ManyToManyField(User, blank=True, verbose_name="关注人", help_text='关注人')
    parent = models.ForeignKey("self", null=True, blank=True, on_delete=models.SET_NULL, verbose_name="父工作项",
                               help_text='父工作项')

    class Meta:
        db_table = 'pm_work_item'
        verbose_name = '工作项'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name


def user_directory_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/user_upload_files/user_<username>/<filename>
    return f'user_upload_files/user_{instance.created_by}/{filename}'


class UserFile(BaseModel):
    """
    用户上传的静态文件
    """
    file = models.FileField(upload_to=user_directory_path, verbose_name='用户上传的静态文件',
                            help_text='用户上传的静态文件')
    work_item = models.ForeignKey(WorkItem, null=True, blank=True, on_delete=models.SET_NULL, verbose_name="所属工作项",
                                  help_text='所属工作项')

    class Meta:
        db_table = 'pm_file'
        verbose_name = '静态文件'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.file.name


class Comment(BaseModel):
    """
    用户评论
    """
    content = models.TextField(verbose_name='评论内容', help_text='评论内容')
    work_item = models.ForeignKey(WorkItem, null=True, blank=True, on_delete=models.SET_NULL, verbose_name="所属工作项",
                                  help_text='所属工作项')
    parent = models.ForeignKey("self", null=True, blank=True, on_delete=models.SET_NULL, verbose_name="父评论",
                               help_text='父评论')

    class Meta:
        db_table = 'pm_comment'
        verbose_name = '用户评论'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.content[:10]


class Changelog(BaseModel):
    """
    工作项变更记录
    """
    changelog = models.JSONField(verbose_name='变更记录内容', help_text='变更记录内容')
    work_item = models.ForeignKey(WorkItem, null=True, blank=True, on_delete=models.SET_NULL, verbose_name="所属工作项",
                                  help_text='所属工作项')

    class Meta:
        db_table = 'pm_changelog'
        verbose_name = '变更记录'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.id
