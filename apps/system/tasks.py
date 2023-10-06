import logging
from typing import List

from django.core.mail import send_mail
from django.conf import settings
from celery import Task as CTask, shared_task, current_task

logger = logging.getLogger(settings.TASK_LOGGER_NAME)


class SendEmailTask(CTask):

    def on_success(self, retval, task_id, args, kwargs):
        """
        任务成功时执行
        @param retval: 任务函数的返回值
        @param task_id: Celery生成的任务ID
        @param args: 传给任务函数的位置参数
        @param kwargs: 传给任务函数的关键字参数
        @return:
        """
        logger.info(f"发送邮件任务执行成功，函数返回值：{retval}")

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """
        任务失败时执行
        @param exc: 错误类型
        @param task_id: Celery生成的任务ID
        @param args: 传给任务函数的位置参数
        @param kwargs: 传给任务函数的关键字参数
        @param einfo: 错误详细信息
        @return:
        """
        logger.error(f"发送邮件任务执行失败：{exc}，异常信息如下：{einfo}")


@shared_task(base=SendEmailTask)
def send_email(subject: str, msg_type: str, message: str, recipient_list: List[str]):
    """
    发送邮件
    @param subject: 邮件主题
    @param msg_type: 邮件内容类型 text or html
    @param message: 邮件内容 文本或者html
    @param recipient_list: 收件人列表
    @return:
    """
    task_uuid = current_task.request.id
    logger.info(f"任务ID：{task_uuid}")
    logger.info("开始发送邮件...")
    logger.info(f"邮件内容：{message}")
    if msg_type == 'text':
        send_mail(subject, message, None, recipient_list)
    elif msg_type == 'html':
        send_mail(subject, '', None, recipient_list, html_message=message)
    else:
        logger.error(f"不支持该邮件内容类型：{msg_type}")
        return False
    logger.info("邮件发送成功")
    return True
