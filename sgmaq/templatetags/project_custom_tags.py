from __future__ import unicode_literals
from django import template
import datetime


register = template.Library()

@register.simple_tag
def is_user_manager(user):
    return str(user)


@register.simple_tag
def current_time(format_string):
    return datetime.datetime.now().strftime(format_string)



@register.filter('has_group')
def has_group(user, group_name):
    """
    Verifica se este usuário pertence a un grupo
    """
    groups = user.groups.all().values_list('name', flat=True)
    return True if group_name in groups else False