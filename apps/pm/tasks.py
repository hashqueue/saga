from django.core.mail import send_mail
from celery import shared_task

from pm.models import WorkItem, Changelog, Project, Sprint
from system.models import User


def check_is_value_null(value):
    if value is None:
        return 'null'
    return value


@shared_task(ignore_result=True)
def make_changelog(origin_data: dict, current_data: dict, created_by: str, followers_email: list[str] = None):
    if followers_email:
        ignore_columns = ['id', 'created_at', 'updated_at', 'created_by', 'updated_by', 'sprint', 'parent',
                          'work_item_type', 'followers', 'desc']
        mapping_columns_data = {'priority': dict(WorkItem.PRIORITY_CHOICES),
                                'work_item_status': dict(WorkItem.WORK_ITEM_STATUS_CHOICES),
                                'severity': dict(WorkItem.SEVERITY_CHOICES),
                                'bug_type': dict(WorkItem.BUG_TYPE_CHOICES),
                                'process_result': dict(WorkItem.PROCESS_RESULT_CHOICES)}
        columns_desc = {'name': '标题', 'owner': '负责人', 'priority': '优先级', 'work_item_status': '状态',
                        'severity': '严重程度', 'bug_type': '缺陷类型', 'process_result': '处理结果', 'desc': '描述',
                        'deadline': '截止日期', 'followers': '关注者'}
        diff_results = []
        for key, value in current_data.items():
            if key not in ignore_columns:
                if value != origin_data.get(key):  # 当前值与历史值不同时
                    if key in mapping_columns_data.keys():
                        diff_results.append({'key': key, 'desc': columns_desc.get(key),
                                             'origin': check_is_value_null(
                                                 mapping_columns_data.get(key).get(origin_data.get(key))),
                                             'current': check_is_value_null(
                                                 mapping_columns_data.get(key).get(value))})
                    else:
                        diff_results.append({'key': key, 'desc': columns_desc.get(key),
                                             'origin': check_is_value_null(origin_data.get(key)),
                                             'current': check_is_value_null(value)})
        Changelog.objects.create(changelog=diff_results, work_item=WorkItem.objects.get(id=origin_data.get('id')),
                                 created_by=created_by)
        if diff_results:
            content = ''
            for item in diff_results:
                content += (f'<li>{item["desc"]}：<span style="color: red"><del>{item["origin"]}</del></span> -> '
                            f'<span style="color: green">{item["current"]}</span></li>\n')
            html_msg = f"""<!DOCTYPE html>
                    <html lang="zh">
                    <head>
                      <meta charset="UTF-8">
                      <title>WorkItem Update Notice</title>
                    </head>
                    <body>
                    <p>用户【{created_by}】更新了工作项【<span style="color: dodgerblue">
                    {origin_data.get('name')}</span>】，详情如下：</p>
                    <ul>
                    {content}
                    </ul>
                    </body>
                    </html>
                    """
            return {'subject': f"工作项[{origin_data.get('name')}]更新通知", 'msg_type': 'html', 'message': html_msg,
                    'recipient_list': followers_email}
        return {'subject': '', 'msg_type': 'html', 'message': '', 'recipient_list': []}
    return {'subject': '', 'msg_type': 'html', 'message': '', 'recipient_list': []}


@shared_task(ignore_result=True)
def send_work_items_notice(project_id: int):
    project = Project.objects.filter(id=project_id).first()
    if project:
        # 统计项目下的 所有迭代中的 所有未开始，待处理，重新打开，待处理，修复中状态的工作项和工作项的负责人及负责人的邮箱信息
        sprints = Sprint.objects.filter(project=project)
        work_items = WorkItem.objects.filter(sprint__in=sprints,
                                             work_item_status__in=[1, 2, 3, 7, 12]).values('name', 'owner')
        work_items_info = {}
        work_item_status_mapping = dict(WorkItem.WORK_ITEM_STATUS_CHOICES)
        for work_item in work_items:
            if work_item.get('owner') not in work_items_info.keys():
                work_items_info[work_item.get('owner')] = [{
                    'name': work_item.get('name'), 'status': work_item.get('work_item_status')
                }]
            else:
                work_items_info[work_item.get('owner')].append({
                    'name': work_item.get('name'), 'status': work_item.get('work_item_status')
                })
        for owner, work_items in work_items_info.items():
            owner_email = User.objects.get(username=owner).email
            # 生成邮件内容
            content = ''
            for item in work_items:
                content += (f'<li><span style="color: dodgerblue">{item["name"]}</span> -> '
                            f'<span style="color: orange">{work_item_status_mapping.get(item["status"])}</span></li>')
            html_msg = f"""<!DOCTYPE html>
                    <html lang="en">
                    <head>
                        <meta charset="UTF-8">
                        <title>WorkItem Status Notice</title>
                    </head>
                    <body>
                        <p>您有<span style="color: dodgerblue">工作项</span>待处理，详情如下：</p>
                        <ul>
                            {content}
                        </ul>
                    </body>
                    </html>
                    """
            send_mail('工作项状态提醒', '', None, [owner_email],
                      html_message=html_msg)
