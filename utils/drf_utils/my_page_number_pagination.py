# -*- coding: utf-8 -*-
# @File    : my_page_number_pagination.py
# @Software: PyCharm
# @Description:
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class MyPageNumberPagination(PageNumberPagination):
    # 设置每页最大数据条目为50
    max_page_size = 50
    # 覆盖page_size字段为size
    page_size_query_param = 'page_size'
    # 配置page字段在接口文档中的描述信息
    page_query_description = '第几页'
    # 配置size字段在接口文档中的描述信息
    page_size_query_description = '每页几条'

    def get_paginated_response(self, data):
        """
        重写父类的get_paginated_response()方法
        在分页后的数据构成的响应体中添加total_pages(总共分了多少页)和page(当前所在第几页)字段
        @param data:
        @return:
        """
        # 调用父类中的get_paginated_response()方法获得dict类型返回值，再进行定制
        response = super().get_paginated_response(data)
        response.data['total_pages'] = self.page.paginator.num_pages
        response.data['page'] = self.page.number
        response.data['page_size'] = self.get_page_size(self.request)
        return Response(response.data)

    def get_paginated_response_schema(self, schema):
        """
        自定义接口文档中action=list的接口的schema
        """
        schema_data = super().get_paginated_response_schema(schema)
        schema_data['description'] = '数据'
        schema_data['properties']['total_pages'] = {'type': 'integer', 'description': '一共多少页', 'example': 5}
        schema_data['properties']['page'] = {'type': 'integer', 'description': '第几页', 'example': 1}
        schema_data['properties']['page_size'] = {'type': 'integer', 'description': '每页几条', 'example': 10}
        schema_data['properties']['count']['description'] = '一共多少条数据'
        return {
            'type': 'object',
            'properties': {
                'success': {
                    'type': 'boolean',
                    'description': '操作是否成功',
                    'example': True,
                },
                'message': {
                    'type': 'string',
                    'description': '业务提示消息',
                    'example': 'success',
                },
                'data': schema_data
            }
        }
