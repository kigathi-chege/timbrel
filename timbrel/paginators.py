from rest_framework.pagination import PageNumberPagination


class CommonPagination(PageNumberPagination):
    page_size_query_param = "page_size"
